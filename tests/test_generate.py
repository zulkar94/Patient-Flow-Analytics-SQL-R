"""Tests for the synthetic data generator and warehouse loader."""

from __future__ import annotations

import sqlite3
from datetime import date

from patient_flow.generate import CONDITIONS, generate
from patient_flow.load import build_database


def test_generation_is_reproducible():
    first = generate(200, date(2023, 1, 1), date(2025, 12, 31), seed=7)
    second = generate(200, date(2023, 1, 1), date(2025, 12, 31), seed=7)
    assert first == second


def test_admissions_are_valid():
    _, admissions = generate(500, date(2023, 1, 1), date(2025, 12, 31), seed=1)
    assert admissions, "generator should produce admissions"
    for _admission_id, _, admit, discharge, kind, condition, _ in admissions:
        assert discharge >= admit
        assert kind in {"emergency", "elective"}
        assert condition in CONDITIONS


def test_admissions_do_not_overlap_per_patient():
    _, admissions = generate(500, date(2023, 1, 1), date(2025, 12, 31), seed=3)
    by_patient: dict[str, list[tuple[str, str]]] = {}
    for _, patient, admit, discharge, *_ in admissions:
        by_patient.setdefault(patient, []).append((admit, discharge))
    for stays in by_patient.values():
        stays.sort()
        for (_, previous_discharge), (next_admit, _) in zip(stays, stays[1:], strict=False):
            assert next_admit > previous_discharge


def test_build_database_loads_every_row(tmp_path):
    patients, admissions = generate(50, date(2023, 1, 1), date(2025, 12, 31), seed=5)
    raw = tmp_path / "raw"
    raw.mkdir()
    from patient_flow.generate import write_csv

    write_csv(raw / "patients.csv", ["patient_id", "sex", "birth_date"], patients)
    write_csv(
        raw / "admissions.csv",
        [
            "admission_id",
            "patient_id",
            "admit_date",
            "discharge_date",
            "admission_type",
            "condition",
            "ward",
        ],
        admissions,
    )
    db = tmp_path / "test.db"
    build_database(db, raw)
    connection = sqlite3.connect(db)
    try:
        assert connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == len(patients)
        assert connection.execute("SELECT COUNT(*) FROM admissions").fetchone()[0] == len(
            admissions
        )
    finally:
        connection.close()
