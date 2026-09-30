# dicom-catalog

Catalogs DICOM imaging data into PostgreSQL using the same hierarchy XNAT uses:
**project > subject > session (DICOM study) > scan (DICOM series) > instance**.

- Reads headers only (`stop_before_pixels`), so large archives catalog fast
- Idempotent: re-running an ingest inserts nothing new; each run is logged in `ingest_run`
- Integrity: every file is SHA-256 hashed; a file whose bytes change under an existing SOPInstanceUID is flagged as a conflict and never overwritten
- Data-quality report: counts by modality, series with gaps in InstanceNumber (partial transfers), duplicate files, sessions missing a study date
- Ships with a synthetic DICOM generator, so no real patient data ever touches the repo

## Quick start

```bash
docker compose up -d                 # PostgreSQL 16
pip install -e ".[dev]"
dicom-catalog synth ./demo_data      # synthetic MR, CT, PT series
dicom-catalog ingest ./demo_data --project DEMO
dicom-catalog report
pytest -q
```

Set `DATABASE_URL` to point at another database.

## Schema

| Table | Key | Maps to |
|---|---|---|
| project | label | XNAT project |
| subject | (project, PatientID) | XNAT subject |
| session | StudyInstanceUID | XNAT imaging session |
| scan | SeriesInstanceUID | XNAT scan |
| instance | SOPInstanceUID | DICOM file |

## Releases

Versioned with SemVer; see `CHANGELOG.md`. CI runs the test suite against a live PostgreSQL service on every push.
