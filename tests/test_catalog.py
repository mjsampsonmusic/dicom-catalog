import pytest
from pydicom.uid import generate_uid

from dicom_catalog.db import connect, init_schema
from dicom_catalog.ingest import ingest_directory
from dicom_catalog.report import run_report
from dicom_catalog.synth import write_series


@pytest.fixture
def conn():
    c = connect()
    with c.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS ingest_run, instance, scan, session, subject, project CASCADE")
    c.commit()
    init_schema(c)
    yield c
    c.close()


def test_ingest_builds_hierarchy(conn, tmp_path):
    study = generate_uid()
    write_series(tmp_path, "SUBJ001", study, "MR", 1, 5)
    write_series(tmp_path, "SUBJ001", study, "MR", 2, 3)
    stats = ingest_directory(conn, tmp_path, "DEMO")
    assert stats.inserted == 8 and stats.skipped == 0
    with conn.cursor() as cur:
        cur.execute("SELECT (SELECT count(*) FROM subject), (SELECT count(*) FROM session),"
                    " (SELECT count(*) FROM scan), (SELECT count(*) FROM instance)")
        assert cur.fetchone() == (1, 1, 2, 8)


def test_reingest_is_idempotent(conn, tmp_path):
    write_series(tmp_path, "SUBJ001", generate_uid(), "CT", 1, 4)
    ingest_directory(conn, tmp_path, "DEMO")
    stats = ingest_directory(conn, tmp_path, "DEMO")
    assert (stats.inserted, stats.unchanged) == (0, 4)


def test_changed_bytes_flagged_not_overwritten(conn, tmp_path):
    write_series(tmp_path, "SUBJ001", generate_uid(), "CT", 1, 2)
    ingest_directory(conn, tmp_path, "DEMO")
    f = next(tmp_path.rglob("0001.dcm"))
    f.write_bytes(f.read_bytes() + b"\0\0")
    stats = ingest_directory(conn, tmp_path, "DEMO")
    assert stats.conflicts == 1


def test_non_dicom_skipped(conn, tmp_path):
    (tmp_path / "notes.txt").write_text("not an image")
    stats = ingest_directory(conn, tmp_path, "DEMO")
    assert stats.skipped == 1 and stats.inserted == 0


def test_report_finds_incomplete_scan(conn, tmp_path):
    write_series(tmp_path, "SUBJ001", generate_uid(), "PT", 1, 6, skip={3})
    ingest_directory(conn, tmp_path, "DEMO")
    report = run_report(conn)
    assert len(report["incomplete_scans"]) == 1
    assert report["counts_by_modality"][0][0] == "PT"
