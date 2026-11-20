-- Beds occupied at the start of each week.
--
-- A recursive CTE builds one row per week from the first admission to the last
-- discharge. An admission occupies a bed on the week start if it has been
-- admitted on or before that day and not yet discharged.

WITH RECURSIVE bounds AS (
    SELECT
        DATE(MIN(admit_date))     AS first_day,
        DATE(MAX(discharge_date)) AS last_day
    FROM admissions
),
weeks(week_start, last_day) AS (
    SELECT first_day, last_day FROM bounds
    UNION ALL
    SELECT DATE(week_start, '+7 days'), last_day
    FROM weeks
    WHERE DATE(week_start, '+7 days') <= last_day
)
SELECT
    w.week_start,
    COUNT(a.admission_id) AS occupied_beds
FROM weeks w
LEFT JOIN admissions a
    ON a.admit_date <= w.week_start
   AND a.discharge_date > w.week_start
GROUP BY w.week_start
ORDER BY w.week_start;
