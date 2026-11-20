"""Check each analysis query against a hand-built fixture with known answers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from patient_flow.run_queries import ANALYSIS_DIR, run_query

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")

# Fixture chosen so every expected value can be worked out by hand.
#   P1 born 1950-01-01: pneumonia (emergency) 2024-01-01 to 2024-01-11,
#                       pneumonia (emergency) 2024-01-20 to 2024-01-25 (readmitted 9 days later),
#                       hip replacement (elective) 2024-06-01 to 2024-06-05.
#   P2 born 1990-01-01: appendicitis (emergency) 2024-03-01 to 2024-03-03.
#   Last discharge is 2024-06-05, so the readmission cutoff is 2024-05-06.
#   The hip replacement discharge falls after the cutoff and is excluded.


@pytest.fixture
def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO patients VALUES (?, ?, ?)",
        [("P1", "M", "1950-01-01"), ("P2", "F", "1990-01-01")],
    )
    conn.executemany(
        "INSERT INTO admissions VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "P1", "2024-01-01", "2024-01-11", "emergency", "pneumonia", "Ward A"),
            (2, "P1", "2024-01-20", "2024-01-25", "emergency", "pneumonia", "Ward A"),
            (3, "P1", "2024-06-01", "2024-06-05", "elective", "hip_replacement", "Ward B"),
            (4, "P2", "2024-03-01", "2024-03-03", "emergency", "appendicitis", "Ward C"),
        ],
    )
    yield conn
    conn.close()


def as_dict(columns: list[str], rows: list[tuple], key: str) -> dict:
    index = columns.index(key)
    return {row[index]: dict(zip(columns, row)) for row in rows}


def test_length_of_stay_by_condition(connection):
    columns, rows = run_query(connection, ANALYSIS_DIR / "01_length_of_stay_by_condition.sql")
    result = as_dict(columns, rows, "condition")
    assert result["pneumonia"]["admissions"] == 2
    assert result["pneumonia"]["mean_los_days"] == 7.5
    assert result["pneumonia"]["emergency_share"] == 1.0
    assert result["hip_replacement"]["mean_los_days"] == 4.0
    assert result["hip_replacement"]["emergency_share"] == 0.0


def test_readmission_rate_respects_cutoff(connection):
    columns, rows = run_query(connection, ANALYSIS_DIR / "02_readmissions_30_day.sql")
    result = as_dict(columns, rows, "condition")
    # Pneumonia: discharge 1 is readmitted within 30 days, discharge 2 is not.
    assert result["pneumonia"]["discharges"] == 2
    assert result["pneumonia"]["readmissions_30d"] == 1
    assert result["pneumonia"]["readmission_rate"] == 0.5
    # The hip replacement discharge is after the cutoff, so it is not counted.
    assert "hip_replacement" not in result
    assert result["appendicitis"]["readmission_rate"] == 0.0


def test_weekly_occupancy_counts_beds_on_week_start(connection):
    columns, rows = run_query(connection, ANALYSIS_DIR / "03_weekly_bed_occupancy.sql")
    occupancy = {row[0]: row[1] for row in rows}
    assert occupancy["2024-01-01"] == 1  # admission 1 started that day
    assert occupancy["2024-01-08"] == 1  # still in bed on 8 January
    assert occupancy["2024-01-15"] == 0  # discharged on 11 January, readmitted on 20 January
    assert occupancy["2024-01-22"] == 1  # admission 2 in progress


def test_emergency_share_by_age_band(connection):
    columns, rows = run_query(
        connection, ANALYSIS_DIR / "04_emergency_admissions_by_age_band.sql"
    )
    result = as_dict(columns, rows, "age_band")
    # P1 is 73 to 74 years old at admission, so the 60-74 band holds three admissions.
    assert result["60-74"]["admissions"] == 3
    assert result["60-74"]["emergency_admissions"] == 2
    assert result["0-39"]["emergency_share"] == 1.0


def test_survival_input_is_censored_at_thirty_days(connection):
    columns, rows = run_query(connection, ANALYSIS_DIR / "05_readmission_survival_input.sql")
    frame = [dict(zip(columns, row)) for row in rows]
    assert {row["admission_id"] for row in frame} == {1, 2, 4}
    readmitted = next(row for row in frame if row["admission_id"] == 1)
    assert readmitted["event"] == 1
    assert readmitted["time_days"] == 9
    for row in frame:
        assert 0 < row["time_days"] <= 30
