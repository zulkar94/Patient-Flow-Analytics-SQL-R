-- Emergency admissions by age band, using age at the time of admission.

WITH admitted AS (
    SELECT
        a.admission_type,
        CAST((julianday(a.admit_date) - julianday(p.birth_date)) / 365.25 AS INTEGER) AS age
    FROM admissions a
    JOIN patients p ON p.patient_id = a.patient_id
),
banded AS (
    SELECT
        admission_type,
        CASE
            WHEN age < 40 THEN '0-39'
            WHEN age < 60 THEN '40-59'
            WHEN age < 75 THEN '60-74'
            ELSE '75+'
        END AS age_band
    FROM admitted
)
SELECT
    age_band,
    COUNT(*)                                                         AS admissions,
    SUM(CASE WHEN admission_type = 'emergency' THEN 1 ELSE 0 END)    AS emergency_admissions,
    ROUND(1.0 * SUM(CASE WHEN admission_type = 'emergency' THEN 1 ELSE 0 END) / COUNT(*), 3)
                                                                     AS emergency_share
FROM banded
GROUP BY age_band
ORDER BY age_band;
