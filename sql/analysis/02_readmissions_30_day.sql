-- 30-day readmission rate by condition.
--
-- A discharge counts as readmitted when the same patient's next admission starts
-- 0 to 30 days after discharge. LEAD() finds that next admission per patient.
-- Only discharges on or before (last discharge - 30 days) are counted, so every
-- counted discharge has a full 30-day follow-up window in the data.

WITH ordered AS (
    SELECT
        admission_id,
        patient_id,
        condition,
        discharge_date,
        LEAD(admit_date) OVER (
            PARTITION BY patient_id
            ORDER BY admit_date
        ) AS next_admit_date
    FROM admissions
),
cutoff AS (
    SELECT DATE(MAX(discharge_date), '-30 days') AS last_eligible_discharge
    FROM admissions
),
flagged AS (
    SELECT
        o.condition,
        CASE
            WHEN o.next_admit_date IS NOT NULL
             AND julianday(o.next_admit_date) - julianday(o.discharge_date) BETWEEN 0 AND 30
            THEN 1 ELSE 0
        END AS readmitted_30d
    FROM ordered o
    CROSS JOIN cutoff c
    WHERE o.discharge_date <= c.last_eligible_discharge
)
SELECT
    condition,
    COUNT(*)                                       AS discharges,
    SUM(readmitted_30d)                            AS readmissions_30d,
    ROUND(1.0 * SUM(readmitted_30d) / COUNT(*), 3) AS readmission_rate
FROM flagged
GROUP BY condition
ORDER BY readmission_rate DESC;
