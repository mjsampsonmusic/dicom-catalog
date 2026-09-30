-- XNAT-style hierarchy: project > subject > session (DICOM study) > scan (DICOM series) > instance
CREATE TABLE IF NOT EXISTS project (
    id          SERIAL PRIMARY KEY,
    label       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subject (
    id          SERIAL PRIMARY KEY,
    project_id  INT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    patient_id  TEXT NOT NULL,
    sex         TEXT,
    birth_year  INT,
    UNIQUE (project_id, patient_id)
);

CREATE TABLE IF NOT EXISTS session (
    id                  SERIAL PRIMARY KEY,
    subject_id          INT NOT NULL REFERENCES subject(id) ON DELETE CASCADE,
    study_instance_uid  TEXT NOT NULL UNIQUE,
    study_date          DATE,
    accession_number    TEXT,
    description         TEXT
);

CREATE TABLE IF NOT EXISTS scan (
    id                   SERIAL PRIMARY KEY,
    session_id           INT NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    series_instance_uid  TEXT NOT NULL UNIQUE,
    series_number        INT,
    modality             TEXT,
    description          TEXT
);

CREATE TABLE IF NOT EXISTS instance (
    id                SERIAL PRIMARY KEY,
    scan_id           INT NOT NULL REFERENCES scan(id) ON DELETE CASCADE,
    sop_instance_uid  TEXT NOT NULL UNIQUE,
    instance_number   INT,
    file_path         TEXT NOT NULL,
    sha256            CHAR(64) NOT NULL,
    size_bytes        BIGINT NOT NULL,
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingest_run (
    id           SERIAL PRIMARY KEY,
    project_id   INT NOT NULL REFERENCES project(id),
    source_dir   TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    files_seen   INT NOT NULL DEFAULT 0,
    inserted     INT NOT NULL DEFAULT 0,
    unchanged    INT NOT NULL DEFAULT 0,
    conflicts    INT NOT NULL DEFAULT 0,
    skipped      INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_subject_project ON subject(project_id);
CREATE INDEX IF NOT EXISTS idx_session_subject ON session(subject_id);
CREATE INDEX IF NOT EXISTS idx_scan_session ON scan(session_id);
CREATE INDEX IF NOT EXISTS idx_instance_scan ON instance(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_modality ON scan(modality);
