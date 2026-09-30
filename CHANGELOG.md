# Changelog

Follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-09-30
### Added
- PostgreSQL schema modeled on the XNAT hierarchy (project, subject, session, scan, instance) plus an ingest_run audit table
- Header-only DICOM ingest with idempotent upserts and SHA-256 checksums; changed files are flagged, never overwritten
- Data-quality report: counts by modality, incomplete series, duplicate files, missing study dates
- Synthetic DICOM generator for demos and tests (no real patient data)
- pytest suite and GitHub Actions CI against a live PostgreSQL service
