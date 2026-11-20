"""Generate synthetic patient and admission records.

No real patient data is used or required. Every value is drawn from a seeded
random generator, so the same seed always produces the same files.
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# condition: (mean length of stay in days, probability the admission is an emergency)
CONDITIONS: dict[str, tuple[float, float]] = {
    "pneumonia": (6.0, 0.80),
    "heart_failure": (7.5, 0.70),
    "copd_exacerbation": (5.5, 0.75),
    "diabetes_complication": (4.5, 0.60),
    "hip_replacement": (4.0, 0.10),
    "appendicitis": (3.0, 0.90),
}
WARDS = ["Ward A", "Ward B", "Ward C", "Ward D"]
ADMISSION_COUNT_WEIGHTS = {0: 0.55, 1: 0.25, 2: 0.12, 3: 0.06, 4: 0.02}


def draw_length_of_stay(rng: random.Random, mean_days: float, age: int) -> int:
    """Length of stay in whole days. Older patients stay slightly longer."""
    age_factor = 1 + 0.01 * max(0, age - 60)
    raw = rng.expovariate(1 / (mean_days * age_factor))
    return max(1, round(raw))


def generate(
    n_patients: int,
    start: date,
    end: date,
    seed: int = 42,
) -> tuple[list[tuple], list[tuple]]:
    """Return (patients, admissions) as lists of tuples ready for CSV output."""
    rng = random.Random(seed)
    patients: list[tuple] = []
    admissions: list[tuple] = []
    counts, weights = zip(*ADMISSION_COUNT_WEIGHTS.items())
    next_admission_id = 1

    for i in range(1, n_patients + 1):
        patient_id = f"P{i:05d}"
        birth = date(1930, 1, 1) + timedelta(days=rng.randint(0, 365 * 90))
        sex = rng.choice(["F", "M"])
        patients.append((patient_id, sex, birth.isoformat()))

        cursor = start + timedelta(days=rng.randint(0, 180))
        for _ in range(rng.choices(counts, weights)[0]):
            if cursor >= end:
                break
            age = (cursor - birth).days // 365
            condition = rng.choice(list(CONDITIONS))
            mean_los, p_emergency = CONDITIONS[condition]
            los = draw_length_of_stay(rng, mean_los, age)
            discharge = cursor + timedelta(days=los)
            if discharge > end:
                break
            admission_type = "emergency" if rng.random() < p_emergency else "elective"
            admissions.append(
                (
                    next_admission_id,
                    patient_id,
                    cursor.isoformat(),
                    discharge.isoformat(),
                    admission_type,
                    condition,
                    rng.choice(WARDS),
                )
            )
            next_admission_id += 1
            cursor = discharge + timedelta(days=rng.randint(5, 250))

    return patients, admissions


def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    patients, admissions = generate(
        args.patients, date(2023, 1, 1), date(2025, 12, 31), args.seed
    )
    write_csv(args.out / "patients.csv", ["patient_id", "sex", "birth_date"], patients)
    write_csv(
        args.out / "admissions.csv",
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
    print(f"Wrote {len(patients)} patients and {len(admissions)} admissions to {args.out}")


if __name__ == "__main__":
    main()
