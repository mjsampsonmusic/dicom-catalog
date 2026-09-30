"""Walk a directory, read DICOM headers (no pixel data), and upsert the hierarchy."""
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pydicom
from pydicom.errors import InvalidDicomError


@dataclass
class IngestStats:
    files_seen: int = 0
    inserted: int = 0
    unchanged: int = 0
    conflicts: int = 0
    skipped: int = 0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _date(value) -> date | None:
    s = str(value or "")
    if len(s) != 8 or not s.isdigit():
        return None
    return date(int(s[:4]), int(s[4:6]), int(s[6:]))


def _int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _upsert_id(cur, sql: str, params: tuple) -> int:
    cur.execute(sql, params)
    return cur.fetchone()[0]


def ingest_directory(conn, source: Path, project_label: str) -> IngestStats:
    stats = IngestStats()
    with conn.cursor() as cur:
        project_id = _upsert_id(
            cur,
            "INSERT INTO project(label) VALUES (%s) "
            "ON CONFLICT (label) DO UPDATE SET label = EXCLUDED.label RETURNING id",
            (project_label,),
        )
        run_id = _upsert_id(
            cur,
            "INSERT INTO ingest_run(project_id, source_dir) VALUES (%s, %s) RETURNING id",
            (project_id, str(source)),
        )

        for path in sorted(p for p in Path(source).rglob("*") if p.is_file()):
            stats.files_seen += 1
            try:
                ds = pydicom.dcmread(path, stop_before_pixels=True)
                sop_uid = str(ds.SOPInstanceUID)
                study_uid = str(ds.StudyInstanceUID)
                series_uid = str(ds.SeriesInstanceUID)
            except (InvalidDicomError, AttributeError, OSError):
                stats.skipped += 1
                continue

            digest = _sha256(path)
            cur.execute("SELECT sha256 FROM instance WHERE sop_instance_uid = %s", (sop_uid,))
            existing = cur.fetchone()
            if existing:
                if existing[0] == digest:
                    stats.unchanged += 1
                else:
                    stats.conflicts += 1  # same UID, different bytes: flag, never overwrite
                continue

            birth = _date(ds.get("PatientBirthDate"))
            subject_id = _upsert_id(
                cur,
                "INSERT INTO subject(project_id, patient_id, sex, birth_year) VALUES (%s,%s,%s,%s) "
                "ON CONFLICT (project_id, patient_id) DO UPDATE SET sex = EXCLUDED.sex RETURNING id",
                (project_id, str(ds.get("PatientID", "UNKNOWN")), ds.get("PatientSex"),
                 birth.year if birth else None),
            )
            session_id = _upsert_id(
                cur,
                "INSERT INTO session(subject_id, study_instance_uid, study_date, accession_number, description) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (study_instance_uid) "
                "DO UPDATE SET study_date = EXCLUDED.study_date RETURNING id",
                (subject_id, study_uid, _date(ds.get("StudyDate")),
                 ds.get("AccessionNumber"), ds.get("StudyDescription")),
            )
            scan_id = _upsert_id(
                cur,
                "INSERT INTO scan(session_id, series_instance_uid, series_number, modality, description) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (series_instance_uid) "
                "DO UPDATE SET modality = EXCLUDED.modality RETURNING id",
                (session_id, series_uid, _int(ds.get("SeriesNumber")),
                 ds.get("Modality"), ds.get("SeriesDescription")),
            )
            cur.execute(
                "INSERT INTO instance(scan_id, sop_instance_uid, instance_number, file_path, sha256, size_bytes) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (scan_id, sop_uid, _int(ds.get("InstanceNumber")), str(path), digest, path.stat().st_size),
            )
            stats.inserted += 1

        cur.execute(
            "UPDATE ingest_run SET finished_at = now(), files_seen=%s, inserted=%s, unchanged=%s, "
            "conflicts=%s, skipped=%s WHERE id=%s",
            (stats.files_seen, stats.inserted, stats.unchanged, stats.conflicts, stats.skipped, run_id),
        )
    conn.commit()
    return stats
