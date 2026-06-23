-- Monthly KPI trend
SELECT
    DATE_TRUNC('month', payment_date) AS month,
    COUNT(*) AS records,
    SUM(amount) AS total_value
FROM analytics.payments
GROUP BY 1
ORDER BY 1;

-- Quality profile
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT record_id) AS distinct_records
FROM analytics.payments;
