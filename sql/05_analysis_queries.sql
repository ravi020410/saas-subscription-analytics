-- Portfolio-ready analytical query examples for SaaS Analytics
-- Add table-specific joins after loading the dimension tables.
WITH monthly AS (
    SELECT DATE_TRUNC('month', payment_date) AS month, SUM(amount) AS value
    FROM analytics.payments
    GROUP BY 1
)
SELECT
    month,
    value,
    value - LAG(value) OVER (ORDER BY month) AS absolute_change,
    value / NULLIF(LAG(value) OVER (ORDER BY month), 0) - 1 AS growth_rate
FROM monthly
ORDER BY month;
