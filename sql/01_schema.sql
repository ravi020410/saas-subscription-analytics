-- =========================================================================================
-- SaaS Subscription Analytics - Production-Ready Relational Schema (PostgreSQL)
-- Database Platform: PostgreSQL (v12+)
-- Description: This script defines the core analytical schema ('analytics') and creates
--              8 fully typed relational tables with constraints, default values, and
--              high-performance index structures.
-- =========================================================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- -----------------------------------------------------------------------------------------
-- TABLE 1: PLANS (Pricing Tiers)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.plans (
    plan_id INT PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL UNIQUE,
    monthly_price NUMERIC(10, 2) NOT NULL CHECK (monthly_price >= 0),
    target_segment VARCHAR(50) NOT NULL,
    max_seats INT NOT NULL CHECK (max_seats > 0)
);

-- -----------------------------------------------------------------------------------------
-- TABLE 2: USERS (Registered Customer Accounts)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.users (
    user_id INT PRIMARY KEY,
    region VARCHAR(50) NOT NULL CHECK (region IN ('North America', 'Europe', 'APAC', 'LATAM')),
    acquisition_channel VARCHAR(50) NOT NULL,
    company_size VARCHAR(20) NOT NULL,
    signup_date DATE NOT NULL CHECK (signup_date >= '2020-01-01')
);

-- -----------------------------------------------------------------------------------------
-- TABLE 3: SUBSCRIPTIONS (Customer Subscription States)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.subscriptions (
    subscription_id INT PRIMARY KEY,
    user_id INT NOT NULL REFERENCES analytics.users(user_id) ON DELETE CASCADE,
    plan_id INT NOT NULL REFERENCES analytics.plans(plan_id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active', 'Paused', 'Churned')),
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_price NUMERIC(10, 2) NOT NULL CHECK (monthly_price >= 0),
    mrr NUMERIC(10, 2) NOT NULL CHECK (mrr >= 0), -- Added mrr column to match notebook contract
    CONSTRAINT chk_end_date CHECK (end_date IS NULL OR end_date >= start_date)
);

-- -----------------------------------------------------------------------------------------
-- TABLE 4: PAYMENTS (Transaction Billing Logs)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.payments (
    payment_id INT PRIMARY KEY,
    subscription_id INT NOT NULL REFERENCES analytics.subscriptions(subscription_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES analytics.users(user_id) ON DELETE CASCADE,
    plan_id INT NOT NULL REFERENCES analytics.plans(plan_id) ON DELETE RESTRICT,
    payment_date TIMESTAMP NOT NULL,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('Paid', 'Failed'))
);

-- -----------------------------------------------------------------------------------------
-- TABLE 5: CHURN EVENTS (Exit Surveys & Lost Revenue)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.churn_events (
    subscription_id INT PRIMARY KEY REFERENCES analytics.subscriptions(subscription_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES analytics.users(user_id) ON DELETE CASCADE,
    churn_date DATE NOT NULL,
    churn_reason VARCHAR(255) NOT NULL,
    mrr NUMERIC(10, 2) NOT NULL CHECK (mrr >= 0)
);

-- -----------------------------------------------------------------------------------------
-- TABLE 6: PRODUCT USAGE (Weekly Telemetry Logs)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.product_usage (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES analytics.users(user_id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    feature VARCHAR(50) NOT NULL DEFAULT 'Dashboard', -- Added feature column
    active_minutes INT NOT NULL DEFAULT 0 CHECK (active_minutes >= 0), -- Renamed minutes_active -> active_minutes
    events INT NOT NULL DEFAULT 0 CHECK (events >= 0)
);

-- -----------------------------------------------------------------------------------------
-- TABLE 7: SUPPORT TICKETS (Service Level Agreements - SLAs)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.support_tickets (
    ticket_id INT PRIMARY KEY,
    user_id INT NOT NULL REFERENCES analytics.users(user_id) ON DELETE CASCADE,
    created_date TIMESTAMP NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
    first_response_hours NUMERIC(5, 2) CHECK (first_response_hours >= 0),
    resolution_hours NUMERIC(5, 2) CHECK (resolution_hours >= 0)
);

-- -----------------------------------------------------------------------------------------
-- TABLE 8: MARKETING CAMPAIGNS (CAC & Cohort Spend Economics)
-- -----------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.marketing_campaigns (
    campaign_id INT PRIMARY KEY,
    campaign_month DATE NOT NULL,
    channel VARCHAR(50) NOT NULL,
    spend NUMERIC(10, 2) NOT NULL CHECK (spend >= 0),
    trial_signups INT NOT NULL CHECK (trial_signups >= 0),
    paid_conversions INT NOT NULL CHECK (paid_conversions >= 0)
);

-- =========================================================================================
-- HIGH-PERFORMANCE B-TREE INDEXES
-- Purpose: Optimizes query execution speeds, fast relational joins, and chronological scans.
-- =========================================================================================

-- Relational Join Indexes (Foreign Keys)
CREATE INDEX IF NOT EXISTS idx_subs_user_id ON analytics.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_plan_id ON analytics.subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_payments_sub_id ON analytics.payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON analytics.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_plan_id ON analytics.payments(plan_id);
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON analytics.support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON analytics.product_usage(user_id);

-- Chronological Filter Indexes
CREATE INDEX IF NOT EXISTS idx_payments_date ON analytics.payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_users_signup_date ON analytics.users(signup_date);
CREATE INDEX IF NOT EXISTS idx_usage_event_date ON analytics.product_usage(event_date);
CREATE INDEX IF NOT EXISTS idx_tickets_created_date ON analytics.support_tickets(created_date);
CREATE INDEX IF NOT EXISTS idx_campaigns_month ON analytics.marketing_campaigns(campaign_month);
