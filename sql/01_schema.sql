-- PostgreSQL schema for SaaS Subscription Analytics Dashboard
CREATE SCHEMA IF NOT EXISTS analytics;

-- Load CSVs into staging tables before applying typed production DDL.
-- The generated CSV files live in data/cleaned.
-- This schema is intentionally explicit enough for portfolio review and easy extension.
CREATE TABLE IF NOT EXISTS analytics.payments (
    record_id BIGSERIAL PRIMARY KEY,
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
