-- =========================================================================================
-- SaaS Subscription Analytics - 20+ Production-Grade PostgreSQL Business Queries
-- Author: Ravikant Yadav
-- Database Platform: PostgreSQL (v12+)
-- Description: This script contains 22 highly optimized, analytical SQL queries designed
--              to run directly on the PostgreSQL analytics schema. It tracks core metrics:
--              MRR, ARR, Net Revenue Retention (NRR), Cohort Retention, LTV:CAC, and Support SLA.
-- =========================================================================================

-- -----------------------------------------------------------------------------------------
-- QUERY 1: Executive KPI SaaS Scorecard
-- Purpose: Calculates fundamental SaaS KPIs: Total subscribers, active MRR, Annual
--          Recurring Revenue (ARR), ARPU (Average Revenue Per User), and churn counts.
-- -----------------------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT user_id) AS total_registered_subscribers,
    ROUND(SUM(CASE WHEN status = 'Active' THEN monthly_price ELSE 0 END)::NUMERIC, 2) AS active_mrr,
    ROUND((SUM(CASE WHEN status = 'Active' THEN monthly_price ELSE 0 END) * 12.0)::NUMERIC, 2) AS annual_recurring_revenue_arr,
    ROUND(AVG(CASE WHEN status = 'Active' THEN monthly_price END)::NUMERIC, 2) AS arpu,
    SUM(CASE WHEN status = 'Churned' THEN 1 ELSE 0 END) AS total_churned_subscribers
FROM analytics.subscriptions;


-- -----------------------------------------------------------------------------------------
-- QUERY 2: MoM MRR Growth & Recurring Revenue Expansion
-- Purpose: Track Month-over-Month (MoM) expansion of recurring revenues to evaluate growth.
-- -----------------------------------------------------------------------------------------
WITH monthly_mrr AS (
    SELECT
        DATE_TRUNC('month', payment_date::TIMESTAMP) AS record_month,
        SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END) AS net_monthly_mrr
    FROM analytics.payments
    GROUP BY DATE_TRUNC('month', payment_date::TIMESTAMP)
)
SELECT
    record_month,
    ROUND(net_monthly_mrr::NUMERIC, 2) AS net_monthly_mrr,
    ROUND((net_monthly_mrr - LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month))::NUMERIC, 2) AS mom_variance,
    ROUND(
        (((net_monthly_mrr - LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month)) /
         NULLIF(LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month), 0)) * 100)::NUMERIC,
        2
    ) AS mom_growth_percent
FROM monthly_mrr
ORDER BY record_month;


-- -----------------------------------------------------------------------------------------
-- QUERY 3: Annualized Subscriber Churn Rate (Logo Churn)
-- Purpose: Computes logo churn rate. Measures subscription accounts lost relative to
--          opening active accounts inside each month.
-- -----------------------------------------------------------------------------------------
WITH monthly_signups AS (
    SELECT
        DATE_TRUNC('month', start_date::TIMESTAMP) AS active_month,
        COUNT(subscription_id) AS new_signups
    FROM analytics.subscriptions
    GROUP BY DATE_TRUNC('month', start_date::TIMESTAMP)
),
monthly_churns AS (
    SELECT
        DATE_TRUNC('month', churn_date::TIMESTAMP) AS active_month,
        COUNT(subscription_id) AS churned_subscribers
    FROM analytics.churn_events
    GROUP BY DATE_TRUNC('month', churn_date::TIMESTAMP)
)
SELECT
    s.active_month,
    s.new_signups,
    COALESCE(c.churned_subscribers, 0) AS churned_subscribers,
    ROUND(
        (COALESCE(c.churned_subscribers, 0) * 100.0 / NULLIF(s.new_signups, 0))::NUMERIC,
        2
    ) AS monthly_logo_churn_rate_percent
FROM monthly_signups s
LEFT JOIN monthly_churns c ON s.active_month = c.active_month
ORDER BY s.active_month;


-- -----------------------------------------------------------------------------------------
-- QUERY 4: Revenue Expansion & Upgrade vs. Downgrade Dynamics
-- Purpose: Isolates upgrade (expansion MRR) vs downgrade (contraction MRR) behaviors
--          to check if our upsell pipeline covers contract loss.
-- -----------------------------------------------------------------------------------------
WITH payment_transitions AS (
    SELECT
        subscription_id,
        DATE_TRUNC('month', payment_date::TIMESTAMP) AS payment_month,
        amount,
        LAG(amount, 1) OVER (PARTITION BY subscription_id ORDER BY payment_date) AS prev_amount
    FROM analytics.payments
    WHERE payment_status = 'Paid'
)
SELECT
    payment_month,
    ROUND(SUM(CASE WHEN amount > prev_amount THEN amount - prev_amount ELSE 0 END)::NUMERIC, 2) AS expansion_mrr,
    ROUND(SUM(CASE WHEN amount < prev_amount THEN prev_amount - amount ELSE 0 END)::NUMERIC, 2) AS contraction_mrr,
    ROUND(
        (SUM(CASE WHEN amount > prev_amount THEN amount - prev_amount ELSE 0 END) -
         SUM(CASE WHEN amount < prev_amount THEN prev_amount - amount ELSE 0 END))::NUMERIC,
        2
    ) AS net_expansion_mrr
FROM payment_transitions
WHERE prev_amount IS NOT NULL
GROUP BY payment_month
ORDER BY payment_month;


-- -----------------------------------------------------------------------------------------
-- QUERY 5: SaaS Customer Acquisition Cost (CAC) vs. Lifetime Value (LTV)
-- Purpose: Computes the premium SaaS LTV-to-CAC ratio by marketing channel.
--          LTV:CAC below 3.0 indicates unsustainable customer acquisition models.
-- -----------------------------------------------------------------------------------------
WITH channel_metrics AS (
    SELECT
        channel,
        SUM(spend) AS total_spend,
        SUM(trial_signups) AS total_trial_signups,
        SUM(paid_conversions) AS total_paid_conversions,
        ROUND((SUM(spend) / NULLIF(SUM(paid_conversions), 0))::NUMERIC, 2) AS calculated_cac
    FROM analytics.marketing_campaigns
    GROUP BY channel
),
user_ltv AS (
    SELECT
        u.acquisition_channel,
        ROUND(AVG(s.monthly_price)::NUMERIC, 2) AS avg_monthly_spend,
        ROUND(
            AVG(
                CASE
                    WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                    ELSE EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                END
            )::NUMERIC,
            1
        ) AS avg_tenure_months
    FROM analytics.users u
    JOIN analytics.subscriptions s ON u.user_id = s.user_id
    GROUP BY u.acquisition_channel
)
SELECT
    cm.channel AS acquisition_channel,
    cm.calculated_cac AS average_cac,
    ROUND((ul.avg_monthly_spend * ul.avg_tenure_months)::NUMERIC, 2) AS estimated_customer_ltv,
    ROUND(
        ((ul.avg_monthly_spend * ul.avg_tenure_months) / NULLIF(cm.calculated_cac, 0))::NUMERIC,
        2
    ) AS ltv_to_cac_ratio
FROM channel_metrics cm
JOIN user_ltv ul ON LOWER(cm.channel) = LOWER(ul.acquisition_channel)
ORDER BY ltv_to_cac_ratio DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 6: Customer Lifetime Value (LTV) Decile Distribution
-- Purpose: Separates SaaS subscriber base into spend deciles, checking if top VIP deciles
--          represent the vast majority of recurring revenue.
-- -----------------------------------------------------------------------------------------
WITH subscriber_spending AS (
    SELECT
        s.user_id,
        SUM(s.monthly_price *
            CASE
                WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                THEN CEIL(EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0)
                ELSE CEIL(EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0)
            END
        ) AS calculated_ltv,
        NTILE(10) OVER (
            ORDER BY SUM(s.monthly_price *
                CASE
                    WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                    THEN CEIL(EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0)
                    ELSE CEIL(EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0)
                END
            ) DESC
        ) AS spend_decile
    FROM analytics.subscriptions s
    GROUP BY s.user_id
)
SELECT
    spend_decile,
    COUNT(user_id) AS subscriber_count,
    ROUND(SUM(calculated_ltv)::NUMERIC, 2) AS decile_combined_revenue,
    ROUND(
        (SUM(calculated_ltv) * 100.0 / (SELECT SUM(calculated_ltv) FROM subscriber_spending))::NUMERIC,
        2
    ) AS revenue_contribution_percent,
    ROUND(AVG(calculated_ltv)::NUMERIC, 2) AS average_ltv_in_decile
FROM subscriber_spending
GROUP BY spend_decile
ORDER BY spend_decile ASC;


-- -----------------------------------------------------------------------------------------
-- QUERY 7: Rolling Subscriber Cohort Monthly Retention Matrices
-- Purpose: Maps subscriber cohort lifetimes by signup month, showing when users churn.
-- -----------------------------------------------------------------------------------------
WITH cohort_acquisitions AS (
    SELECT
        user_id,
        DATE_TRUNC('month', signup_date::TIMESTAMP) AS cohort_month
    FROM analytics.users
),
payment_months AS (
    SELECT DISTINCT
        p.user_id,
        ca.cohort_month,
        DATE_TRUNC('month', p.payment_date::TIMESTAMP) AS active_month,
        -- Calculate months difference in PostgreSQL
        (EXTRACT(YEAR FROM age(DATE_TRUNC('month', p.payment_date::TIMESTAMP), ca.cohort_month)) * 12 +
         EXTRACT(MONTH FROM age(DATE_TRUNC('month', p.payment_date::TIMESTAMP), ca.cohort_month)))::INT AS month_index
    FROM analytics.payments p
    JOIN cohort_acquisitions ca ON p.user_id = ca.user_id
    WHERE p.payment_status = 'Paid'
)
SELECT
    cohort_month,
    month_index,
    COUNT(DISTINCT user_id) AS active_subscribers
FROM payment_months
WHERE month_index BETWEEN 0 AND 12
GROUP BY cohort_month, month_index
ORDER BY cohort_month, month_index;


-- -----------------------------------------------------------------------------------------
-- QUERY 8: SaaS Subscription Tier Metrics (Basic vs. Premium vs. Enterprise)
-- Purpose: Compares subscriber volumes, revenue distributions, and retention times
--          across plan tiers to drive premium upgrades.
-- -----------------------------------------------------------------------------------------
SELECT
    p.plan_name AS subscription_tier,
    COUNT(s.user_id) AS active_subscribers,
    ROUND(SUM(s.monthly_price)::NUMERIC, 2) AS tier_monthly_revenue,
    ROUND(AVG(s.monthly_price)::NUMERIC, 2) AS tier_arpu,
    ROUND(
        AVG(
            CASE
                WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                ELSE EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
            END
        )::NUMERIC,
        1
    ) AS average_tenure_months
FROM analytics.subscriptions s
JOIN analytics.plans p ON s.plan_id = p.plan_id
WHERE s.status = 'Active'
GROUP BY p.plan_name
ORDER BY tier_monthly_revenue DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 9: Severe Churn Warnings (Underutilized Active Subscriptions)
-- Purpose: Flags active accounts showing low feature events, placing them
--          at severe risk of cancelling in the next billing cycle.
-- -----------------------------------------------------------------------------------------
WITH last_product_activities AS (
    SELECT
        user_id,
        MAX(event_date::DATE) AS last_active_date,
        SUM(events) AS total_events_30_days
    FROM analytics.product_usage
    WHERE event_date::DATE >= '2025-12-01'::DATE
    GROUP BY user_id
)
SELECT
    s.user_id,
    p.plan_name AS subscription_tier,
    s.monthly_price AS account_monthly_cost,
    COALESCE(lpa.total_events_30_days, 0) AS total_events_last_30_days,
    ('2026-01-01'::DATE - COALESCE(lpa.last_active_date, s.start_date::DATE)) AS inactive_days,
    CASE
        WHEN ('2026-01-01'::DATE - COALESCE(lpa.last_active_date, s.start_date::DATE)) > 45 THEN 'Critical Risk (45+ Days Inactive)'
        WHEN ('2026-01-01'::DATE - COALESCE(lpa.last_active_date, s.start_date::DATE)) BETWEEN 30 AND 45 THEN 'High Risk (30-45 Days Inactive)'
        ELSE 'Healthy Activity'
    END AS retention_risk_level
FROM analytics.subscriptions s
JOIN analytics.plans p ON s.plan_id = p.plan_id
LEFT JOIN last_product_activities lpa ON s.user_id = lpa.user_id
WHERE s.status = 'Active'
ORDER BY inactive_days DESC, total_events_last_30_days ASC
LIMIT 100;


-- -----------------------------------------------------------------------------------------
-- QUERY 10: MoM Net Revenue Retention (NRR) & Churned Revenue Mechanics
-- Purpose: Calculates monthly NRR, checking if expansions and renewals cover
--          losses from churned contracts.
-- -----------------------------------------------------------------------------------------
WITH monthly_sub_revenue AS (
    SELECT
        DATE_TRUNC('month', payment_date::TIMESTAMP) AS payment_month,
        subscription_id,
        SUM(amount) AS total_paid
    FROM analytics.payments
    WHERE payment_status = 'Paid'
    GROUP BY 1, 2
),
revenue_movements AS (
    SELECT
        curr.payment_month,
        curr.subscription_id,
        curr.total_paid AS current_mrr,
        COALESCE(prev.total_paid, 0) AS previous_mrr
    FROM monthly_sub_revenue curr
    LEFT JOIN monthly_sub_revenue prev
        ON curr.subscription_id = prev.subscription_id
        AND curr.payment_month = prev.payment_month + INTERVAL '1 month'
)
SELECT
    payment_month,
    ROUND(SUM(previous_mrr)::NUMERIC, 2) AS starting_mrr,
    ROUND(SUM(current_mrr)::NUMERIC, 2) AS ending_mrr,
    ROUND(
        (SUM(current_mrr) * 100.0 / NULLIF(SUM(previous_mrr), 0))::NUMERIC,
        2
    ) AS net_revenue_retention_percent
FROM revenue_movements
GROUP BY payment_month
ORDER BY payment_month;


-- -----------------------------------------------------------------------------------------
-- QUERY 11: Daily MRR Revenue Moving Averages
-- Purpose: Smooths out daily transaction spikes through rolling 7-day averages.
-- -----------------------------------------------------------------------------------------
WITH daily_sales AS (
    SELECT
        DATE_TRUNC('day', payment_date::TIMESTAMP) AS sale_day,
        SUM(amount) AS daily_inflow
    FROM analytics.payments
    WHERE payment_status = 'Paid'
    GROUP BY 1
)
SELECT
    sale_day,
    ROUND(daily_inflow::NUMERIC, 2) AS daily_inflow,
    ROUND(
        AVG(daily_inflow) OVER (
            ORDER BY sale_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::NUMERIC,
        2
    ) AS rolling_7day_average_inflow
FROM daily_sales
ORDER BY sale_day;


-- -----------------------------------------------------------------------------------------
-- QUERY 12: High-Value SaaS Outliers (Statistical Z-Score Filter)
-- Purpose: Identifies unusual high-paying subscribers (e.g. customized Enterprise deals)
--          exceeding 2 standard deviations from average MRR prices.
-- -----------------------------------------------------------------------------------------
WITH price_metrics AS (
    SELECT
        AVG(monthly_price) AS average_monthly_price,
        STDDEV(monthly_price) AS standard_deviation_price
    FROM analytics.subscriptions
    WHERE status = 'Active'
)
SELECT
    s.subscription_id,
    s.user_id,
    p.plan_name AS subscription_tier,
    ROUND(s.monthly_price::NUMERIC, 2) AS monthly_price,
    ROUND(pm.average_monthly_price::NUMERIC, 2) AS average_price_benchmark,
    ROUND(
        ((s.monthly_price - pm.average_monthly_price) / NULLIF(pm.standard_deviation_price, 0))::NUMERIC,
        2
    ) AS price_z_score
FROM analytics.subscriptions s
JOIN analytics.plans p ON s.plan_id = p.plan_id
CROSS JOIN price_metrics pm
WHERE s.status = 'Active'
  AND (s.monthly_price - pm.average_monthly_price) / NULLIF(pm.standard_deviation_price, 0) > 2.0
ORDER BY monthly_price DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 13: Subscriber Data Integrity Audits (Null Fields)
-- Purpose: System health check. Ensures all records map valid subscriber fields.
-- -----------------------------------------------------------------------------------------
SELECT
    COUNT(*) AS total_logged_subscriptions,
    SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user_ids,
    SUM(CASE WHEN plan_id IS NULL THEN 1 ELSE 0 END) AS null_plan_ids,
    SUM(CASE WHEN status = 'Churned' AND end_date IS NULL THEN 1 ELSE 0 END) AS anomalous_churn_dates
FROM analytics.subscriptions;


-- -----------------------------------------------------------------------------------------
-- QUERY 14: Transaction Duplication Audit in Billing Engine
-- Purpose: Financial audit. Flags potential identical duplicate payment entries processed
--          for the same subscription within the same minute.
-- -----------------------------------------------------------------------------------------
SELECT
    subscription_id,
    payment_date,
    amount,
    COUNT(*) AS duplicate_occurrences
FROM analytics.payments
GROUP BY subscription_id, payment_date, amount
HAVING COUNT(*) > 1;


-- -----------------------------------------------------------------------------------------
-- QUERY 15: Average Customer Lifetime Value (LTV) by Target Segment
-- Purpose: Evaluates LTV metrics by plan target segments to optimize sales campaigns.
-- -----------------------------------------------------------------------------------------
SELECT
    p.target_segment,
    COUNT(s.subscription_id) AS subscription_sample,
    ROUND(AVG(s.monthly_price)::NUMERIC, 2) AS average_monthly_spend,
    ROUND(
        AVG(
            CASE
                WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                ELSE EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
            END
        )::NUMERIC,
        1
    ) AS average_lifespan_months,
    ROUND(
        (AVG(s.monthly_price) *
         AVG(
             CASE
                 WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                 THEN EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                 ELSE EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
             END
         ))::NUMERIC,
        2
    ) AS calculated_ltv
FROM analytics.subscriptions s
JOIN analytics.plans p ON s.plan_id = p.plan_id
GROUP BY p.target_segment
ORDER BY calculated_ltv DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 16: Core Churn Reason Analysis
-- Purpose: Tracks the key drivers behind subscriber churn from exit surveys.
-- -----------------------------------------------------------------------------------------
SELECT
    churn_reason,
    COUNT(*) AS churn_occurrences,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.churn_events))::NUMERIC, 2) AS churn_percentage,
    ROUND(AVG(mrr)::NUMERIC, 2) AS average_lost_mrr
FROM analytics.churn_events
GROUP BY churn_reason
ORDER BY churn_occurrences DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 17: Support SLA Completion Rates
-- Purpose: Tracks resolution times and customer support performance metrics.
--          Highlights potential operational bottlenecks leading to churn.
-- -----------------------------------------------------------------------------------------
SELECT
    priority,
    category,
    COUNT(*) AS total_tickets,
    ROUND(AVG(first_response_hours)::NUMERIC, 2) AS avg_first_response_hours,
    ROUND(AVG(resolution_hours)::NUMERIC, 2) AS avg_resolution_hours,
    SUM(CASE WHEN resolution_hours <= 24 THEN 1 ELSE 0 END) AS resolved_within_24h,
    ROUND(
        (SUM(CASE WHEN resolution_hours <= 24 THEN 1 ELSE 0 END) * 100.0 / COUNT(*))::NUMERIC,
        2
    ) AS sla_resolution_rate_percent
FROM analytics.support_tickets
GROUP BY priority, category
ORDER BY priority DESC, avg_resolution_hours DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 18: SLA Success Rate Trend (MoM)
-- Purpose: Tracks whether the customer support team's SLA performance is improving.
-- -----------------------------------------------------------------------------------------
SELECT
    DATE_TRUNC('month', created_date::TIMESTAMP) AS ticket_month,
    COUNT(*) AS total_tickets,
    ROUND(AVG(resolution_hours)::NUMERIC, 2) AS avg_resolution_hours,
    ROUND(
        (SUM(CASE WHEN resolution_hours <= 24 THEN 1 ELSE 0 END) * 100.0 / COUNT(*))::NUMERIC,
        2
    ) AS sla_resolution_rate_percent
FROM analytics.support_tickets
GROUP BY 1
ORDER BY 1;


-- -----------------------------------------------------------------------------------------
-- QUERY 19: Annualized ARR Run Rate Forecasting by Region
-- Purpose: Projects forward recurring revenue expectations by company geographic region.
-- -----------------------------------------------------------------------------------------
SELECT
    u.region,
    COUNT(s.subscription_id) AS active_subscriptions,
    ROUND(SUM(s.monthly_price)::NUMERIC, 2) AS current_mrr,
    ROUND((SUM(s.monthly_price) * 12.0)::NUMERIC, 2) AS current_arr,
    ROUND((SUM(s.monthly_price) * 12.0 * 1.15)::NUMERIC, 2) AS projected_1year_arr_with_15percent_growth
FROM analytics.subscriptions s
JOIN analytics.users u ON s.user_id = u.user_id
WHERE s.status = 'Active'
GROUP BY u.region
ORDER BY current_arr DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 20: Average Subscriber Lifespan by Company Size
-- Purpose: Identifies whether enterprise or SMB customers are more sticky over time.
-- -----------------------------------------------------------------------------------------
SELECT
    u.company_size,
    COUNT(s.subscription_id) AS subscription_sample,
    ROUND(
        AVG(
            CASE
                WHEN s.status = 'Churned' AND s.end_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (s.end_date::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
                ELSE EXTRACT(EPOCH FROM ('2026-01-01'::TIMESTAMP - s.start_date::TIMESTAMP)) / 2592000.0
            END
        )::NUMERIC,
        1
    ) AS average_tenure_months,
    ROUND(AVG(s.monthly_price)::NUMERIC, 2) AS average_monthly_price
FROM analytics.subscriptions s
JOIN analytics.users u ON s.user_id = u.user_id
GROUP BY u.company_size
ORDER BY average_tenure_months DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 21: Billing Engine Decline Rate Analysis (Transaction Level)
-- Purpose: Highlights financial declines across payment processors to optimize automated
--          payment retry workflows.
-- -----------------------------------------------------------------------------------------
SELECT
    plan_id,
    COUNT(*) AS payment_attempts,
    SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) AS failed_payments,
    ROUND(
        (SUM(CASE WHEN payment_status = 'Failed' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*))::NUMERIC,
        2
    ) AS payment_decline_rate_percent
FROM analytics.payments
GROUP BY plan_id
ORDER BY payment_decline_rate_percent DESC;


-- -----------------------------------------------------------------------------------------
-- QUERY 22: Consolidated SaaS Executive Scorecard Matrix
-- Purpose: Generates a complete cross-tabulation of active subscriber count, MRR values,
--          and total payments by geographic region.
-- -----------------------------------------------------------------------------------------
SELECT
    u.region,
    COUNT(CASE WHEN s.status = 'Active' THEN 1 END) AS active_subscribers,
    ROUND(SUM(CASE WHEN s.status = 'Active' THEN s.monthly_price ELSE 0 END)::NUMERIC, 2) AS total_active_mrr,
    ROUND(AVG(CASE WHEN s.status = 'Active' THEN s.monthly_price END)::NUMERIC, 2) AS arpu,
    COUNT(CASE WHEN s.status = 'Churned' THEN 1 END) AS cumulative_churn_loss
FROM analytics.subscriptions s
JOIN analytics.users u ON s.user_id = u.user_id
GROUP BY u.region
ORDER BY total_active_mrr DESC;
