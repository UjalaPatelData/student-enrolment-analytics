-- SQLite schema for the student enrolment analysis

CREATE TABLE programs (
    program_code          TEXT PRIMARY KEY,
    program_name          TEXT NOT NULL,
    faculty               TEXT NOT NULL,
    tuition_domestic      REAL NOT NULL CHECK (tuition_domestic > 0),
    tuition_international REAL NOT NULL CHECK (tuition_international > 0)
);

CREATE TABLE terms (
    term       TEXT PRIMARY KEY,
    intake     TEXT NOT NULL CHECK (intake IN ('Fall', 'Winter')),
    start_date TEXT NOT NULL
);

CREATE TABLE applications (
    application_id     TEXT PRIMARY KEY,
    term               TEXT NOT NULL REFERENCES terms(term),
    applied_date       TEXT NOT NULL,
    program_code       TEXT NOT NULL REFERENCES programs(program_code),
    student_type       TEXT NOT NULL CHECK (student_type IN ('Domestic', 'International')),
    age_group          TEXT NOT NULL,
    channel            TEXT NOT NULL,
    offered            INTEGER NOT NULL CHECK (offered IN (0, 1)),
    accepted           INTEGER NOT NULL CHECK (accepted IN (0, 1)),
    enrolled           INTEGER NOT NULL CHECK (enrolled IN (0, 1)),
    first_term_gpa     REAL CHECK (first_term_gpa BETWEEN 0 AND 4),
    retained_next_term INTEGER CHECK (retained_next_term IN (0, 1)),
    CHECK (enrolled <= accepted AND accepted <= offered)
);

CREATE INDEX idx_app_term    ON applications(term);
CREATE INDEX idx_app_program ON applications(program_code);
CREATE INDEX idx_app_type    ON applications(student_type);
