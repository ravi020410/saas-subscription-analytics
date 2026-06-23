# SaaS Subscription Analytics & Churn Diagnosis Dashboard

[![SQL](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Postgres-blue?logo=postgresql&logoColor=white)](https://github.com/ravi020410/saas-subscription-analytics/tree/main/sql)
[![Python](https://img.shields.io/badge/Language-Python%203.11-darkgreen?logo=python&logoColor=white)](https://github.com/ravi020410/saas-subscription-analytics/tree/main/notebooks)
[![Power BI](https://img.shields.io/badge/BI-Power%20BI%20%7C%20DAX-yellow?logo=powerbi&logoColor=white)](https://github.com/ravi020410/saas-subscription-analytics/tree/main/dashboards/powerbi)

An end-to-end data analytics project diagnosing subscriber retention, MRR growth, and platform activity drivers for a B2B SaaS platform. This project implements a fully normalized analytical PostgreSQL database, granular Python exploratory analysis (EDA), cohort retention modeling, and Power BI DAX metrics to bridge raw transactional records into high-impact executive strategies.

---

## 📂 Project Architecture & Repository Structure

The data flow starts from messy, raw transactional CSV logs, runs through Python quality validation, aggregates user activity and support records in a PostgreSQL data warehouse, and concludes with dynamic visualization in Power BI and Jupyter Notebooks.

```text
├── data/
│   ├── raw/             # Messiah, uncleaned transactional source-like CSV files
│   └── cleaned/         # Cleaned, structured, and validated CSV files
├── sql/
│   ├── 01_schema.sql                      # DDL defining analytics schema
│   ├── 02_load_csv.sql                    # CSV bulk copy stubs
│   ├── 03_kpi_queries.sql                 # Baseline checks
│   ├── 04_quality_checks.sql              # Duplicate and integrity auditing
│   ├── 05_analysis_queries.sql            # Simple MoM trend queries
│   └── 20_business_analysis_queries.sql   # 22 Advanced PostgreSQL Business Queries (MRR, Cohorts, NRR)
├── notebooks/
│   ├── 01_eda.ipynb                       # Dataset loading & initial statistical profiling
│   ├── 02_data_cleaning.ipynb             # Null imputation, logic checks, deduplication
│   ├── 03_feature_engineering.ipynb      # Usage intensity, tenure, and ticket aggregations
│   ├── 04_visualization.ipynb             # Seaborn & Matplotlib custom analytical plots
│   └── 05_business_insights.ipynb         # Cohort heatmaps & Random Forest Churn Importances
├── dashboards/
│   └── powerbi/
│       ├── dashboard_spec.md              # UX design & visualization requirements
│       ├── theme.json                     # Color theme and grid alignment specs
│       └── measures.dax                   # Production-ready custom DAX calculations
├── visuals/             # Exported PNGs, cohort heatmaps, and trend charts
└── scripts/             # Automated Python execution scripts for cleaning and loading
```

---

## 📈 Executive KPI Dashboard (Calculated Baseline)

These high-level metrics are computed from the historical payment, subscription, and user database, ensuring an auditable and mathematically consistent baseline:

| SaaS Metric | Calculated Value | Business Significance |
|:---|---:|:---|
| **Monthly Recurring Revenue (MRR)** | **$861.1K** | Baseline monthly predictable contract value. |
| **Annual Recurring Revenue (ARR)** | **$10.3M** | Projected annual run-rate of current active contracts. |
| **Average Revenue Per User (ARPU)** | **$302.00** | Mean monthly subscription price across active logos. |
| **Net Revenue Retention (NRR)** | **1.1x** | Healthy expansion (110%) — upgrades cover contraction. |
| **Gross Revenue Retention (GRR)** | **88.2%** | Standard retention rate excluding upgrade expansion. |
| **Customer Logo Churn Rate** | **23.1%** | Total customers canceling within the period (Needs improvement). |
| **Customer Lifetime Value (LTV)** | **$4,884.90**| Estimated total revenue contribution before churn. |
| **Trial Conversion Rate** | **17.8%** | Success percentage of marketing trial signups. |

---

## 🛠️ Tech Stack & Key Libraries
- **Database:** PostgreSQL (v12+) — custom schema design, indexes, multi-stage CTEs, window functions.
- **Languages:** Python (v3.11), T-SQL/PostgreSQL, Power BI DAX.
- **Python Ecosystem:**
  - `pandas` & `numpy` — high-performance data wrangling, cohort indexing, feature matrices.
  - `matplotlib` & `seaborn` — publication-quality custom static plots and heatmaps.
  - `scikit-learn` — Random Forest Classifier used to isolate feature importances driving churn.
  - `plotly` — interactive exploratory timelines.
- **BI Platform:** Power BI Desktop — Star schema modeling, time-intelligence DAX measures.

---

## 📊 Core Analytical Highlights & Visuals

### 1. Advanced Cohort Retention (from [05_business_insights.ipynb](notebooks/05_business_insights.ipynb))
By tracking users from their initial signup month through their subsequent 12 months of active payments, we constructed a **Cohort Retention Heatmap**. The analysis reveals:
- A critical **8% to 12% subscriber drop-off at Month 3** across all cohorts.
- Higher initial retention in the Q1-2023 cohorts, indicating product onboarding effectiveness variation.

### 2. Random Forest Churn Drivers (from [05_business_insights.ipynb](notebooks/05_business_insights.ipynb))
Using engineered variables (including usage events, active platform minutes, support ticket count, and monthly spend), we trained a classification tree to mathematically rank why customers cancel:
1. **Active Platform Minutes:** Low activity is the single highest predictor of subscription cancellation.
2. **Support Ticket Count:** High support ticket resolution backlog indicates customer friction.
3. **Monthly Price:** Higher price points show moderate sensitivity, especially in SMBs.

### 3. PostgreSQL Business Engine (from [20_business_analysis_queries.sql](sql/20_business_analysis_queries.sql))
Contains **22 advanced PostgreSQL scripts** that answer critical business questions, such as:
- **Query 5 (LTV-to-CAC Ratio):** Joins marketing spend datasets with subscriber tenures. Identifies channels with positive unit economics (Content, Organic) vs. unprofitable acquisition funnels.
- **Query 7 (Monthly Cohorts):** Custom PostgreSQL date-truncation script calculating rolling monthly retention without pre-built cohort libraries.
- **Query 9 (Critical Retention Warnings):** Combines subscription data with product usage logs to isolate "Underutilized Active Accounts" showing zero activity in the last 30 days.

---

## 🎯 Strategic Business Recommendations

Based on the quantitative findings from our SQL and Python pipelines, we propose three tactical focus areas to accelerate growth:

1. **Proactive Customer Support Outreach:** Implement an automated alert trigger if an Enterprise account's support ticket goes unresolved for over 12 hours, directly addressing the support friction identified as a top churn driver.
2. **Engagement Retention Campaigns:** Target underutilized active users (as surfaced in `QUERY 9`) with personalized in-app guides and feature walk-throughs to increase platform active minutes.
3. **Optimize the First 60 Days Onboarding:** Address the critical Month 3 retention drop highlighted by the Cohort Matrix by overhauling the user onboarding flow, encouraging quicker activation of core features.

---

## 🚀 How to Run the Analysis

### 1. Prerequisites
Ensure you have Python 3.11 installed locally, along with a PostgreSQL server instance.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Schema Setup
1. Create a database called `saas_analytics`.
2. Execute the DDL script in your database shell or query tool:
   ```bash
   psql -U postgres -d saas_analytics -f sql/01_schema.sql
   ```
3. Load the cleaned CSV tables located under `data/cleaned/` into your corresponding schema tables.

### 4. Run Notebooks
Open VS Code or Jupyter and step through the files in `notebooks/` chronologically from `01_eda.ipynb` to `05_business_insights.ipynb` to see the full data-cleaning, engineering, and predictive modeling pipeline.

---

## 👤 Author
**Ravikant Yadav**  
*Data Analyst & Business Intelligence Specialist*  
- **Email:** [yadavravikant597@gmail.com](mailto:yadavravikant597@gmail.com)  
- **LinkedIn:** [Ravikant Yadav](https://www.linkedin.com/in/ravikant-yadav)  
- **GitHub:** [ravi020410](https://github.com/ravi020410)
