"""Run every analysis query in sql/analysis and write each result to CSV."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parents[2] / "sql" / "analysis"


def run_query(connection: sqlite3.Connection, sql_path: Path) -> tuple[list[str], list[tuple]]:
    cursor = connection.execute(sql_path.read_text(encoding="utf-8"))
    columns = [column[0] for column in cursor.description]
    return columns, cursor.fetchall()


def run_all(db_path: Path, out_dir: Path, analysis_dir: Path = ANALYSIS_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    connection = sqlite3.connect(db_path)
    try:
        for sql_path in sorted(analysis_dir.glob("*.sql")):
            columns, rows = run_query(connection, sql_path)
            target = out_dir / f"{sql_path.stem}.csv"
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows(rows)
            written.append(target)
    finally:
        connection.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/patient_flow.db"))
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    for path in run_all(args.db, args.out):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
