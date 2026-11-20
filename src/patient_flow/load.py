"""Build the SQLite warehouse from the raw CSV files."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


def read_rows(path: Path) -> list[tuple]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)  # skip header
        return [tuple(row) for row in reader]


def build_database(db_path: Path, raw_dir: Path, schema_path: Path = SCHEMA_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        patients = read_rows(raw_dir / "patients.csv")
        admissions = [
            (int(a), p, admit, discharge, kind, condition, ward)
            for a, p, admit, discharge, kind, condition, ward in read_rows(
                raw_dir / "admissions.csv"
            )
        ]
        connection.executemany("INSERT INTO patients VALUES (?, ?, ?)", patients)
        connection.executemany("INSERT INTO admissions VALUES (?, ?, ?, ?, ?, ?, ?)", admissions)
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--db", type=Path, default=Path("data/patient_flow.db"))
    args = parser.parse_args()
    build_database(args.db, args.raw)
    print(f"Loaded warehouse at {args.db}")


if __name__ == "__main__":
    main()
