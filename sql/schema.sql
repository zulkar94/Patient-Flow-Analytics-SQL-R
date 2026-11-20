-- Schema for the patient flow warehouse (SQLite dialect).
-- Dates are stored as ISO 8601 text (YYYY-MM-DD) and compared with julianday().

DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    patient_id  TEXT PRIMARY KEY,
    sex         TEXT NOT NULL CHECK (sex IN ('F', 'M')),
    birth_date  TEXT NOT NULL
);

CREATE TABLE admissions (
    admission_id    INTEGER PRIMARY KEY,
    patient_id      TEXT    NOT NULL REFERENCES patients (patient_id),
    admit_date      TEXT    NOT NULL,
    discharge_date  TEXT    NOT NULL,
    admission_type  TEXT    NOT NULL CHECK (admission_type IN ('emergency', 'elective')),
    condition       TEXT    NOT NULL,
    ward            TEXT    NOT NULL,
    CHECK (discharge_date >= admit_date)
);

CREATE INDEX idx_admissions_patient ON admissions (patient_id, admit_date);
CREATE INDEX idx_admissions_admit   ON admissions (admit_date);
