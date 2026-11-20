-- One row per eligible discharge, shaped for survival analysis in R.
--
-- time_days: days until readmission, or days of follow-up if not readmitted,
--            capped at 30 days.
-- event:     1 if readmitted within 30 days, 0 if censored.

WITH ordered AS (
    SELECT
        a.admission_id,
        a.patient_id,
        a.condition,
        a.admission_type,
        a.admit_date,
        a.discharge_date,
        p.sex,
        CAST((julianday(a.admit_date) - julianday(p.birth_date)) / 365.25 AS INTEGER) AS age,
        LEAD(a.admit_date) OVER (
            PARTITION BY a.patient_id
            ORDER BY a.admit_date
        ) AS next_admit_date
    FROM admissions a
    JOIN patients p ON p.patient_id = a.patient_id
),
cutoff AS (
    SELECT DATE(MAX(discharge_date), '-30 days') AS last_eligible_discharge
    FROM admissions
),
eligible AS (
    SELECT o.*,
           julianday(o.next_admit_date) - julianday(o.discharge_date) AS gap_days,
           julianday(c.last_eligible_discharge) - julianday(o.discharge_date) AS followup_days
    FROM ordered o
    CROSS JOIN cutoff c
    WHERE o.discharge_date <= c.last_eligible_discharge
)
SELECT
    admission_id,
    condition,
    admission_type,
    sex,
    CASE
        WHEN age < 40 THEN '0-39'
        WHEN age < 60 THEN '40-59'
        WHEN age < 75 THEN '60-74'
        ELSE '75+'
    END AS age_band,
    julianday(discharge_date) - julianday(admit_date) AS los_days,
    CASE
        WHEN next_admit_date IS NOT NULL AND gap_days BETWEEN 0 AND 30 THEN gap_days
        ELSE MIN(30, followup_days)
    END AS time_days,
    CASE
        WHEN next_admit_date IS NOT NULL AND gap_days BETWEEN 0 AND 30 THEN 1
        ELSE 0
    END AS event
FROM eligible
ORDER BY admission_id;
