-- Length of stay and emergency share by condition.

WITH stays AS (
    SELECT
        condition,
        admission_type,
        julianday(discharge_date) - julianday(admit_date) AS los_days
    FROM admissions
)
SELECT
    condition,
    COUNT(*)                                             AS admissions,
    ROUND(AVG(los_days), 2)                              AS mean_los_days,
    ROUND(AVG(CASE WHEN admission_type = 'emergency' THEN 1.0 ELSE 0.0 END), 3)
                                                         AS emergency_share
FROM stays
GROUP BY condition
ORDER BY mean_los_days DESC;
