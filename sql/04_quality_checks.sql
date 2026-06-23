-- Duplicate check
SELECT record_id, COUNT(*)
FROM analytics.payments
GROUP BY 1
HAVING COUNT(*) > 1;

-- Date completeness check
SELECT COUNT(*) AS missing_dates
FROM analytics.payments
WHERE payment_date IS NULL;
