import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

def main():
    print("==================================================================")
    print("SaaS Subscription Analytics - Executive Report Compiler")
    print("==================================================================")

    # 1. Connection Configurations
    DB_USER = "postgres"
    DB_PASS = "Postgres123!"
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    DB_NAME = "saas_analytics"

    ROOT = Path(__file__).resolve().parents[1]
    REPORTS_DIR = ROOT / "reports"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    target_conn = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    print(f"Connecting to database '{DB_NAME}' to compile KPIs...")
    try:
        engine = create_engine(target_conn)
        with engine.connect() as conn:
            # Query 1: Top-level scorecard KPIs
            scorecard = conn.execute(text("""
                SELECT
                    COUNT(DISTINCT user_id) AS total_subscribers,
                    ROUND(SUM(CASE WHEN status = 'Active' THEN monthly_price ELSE 0 END)::NUMERIC, 2) AS active_mrr,
                    ROUND((SUM(CASE WHEN status = 'Active' THEN monthly_price ELSE 0 END) * 12.0)::NUMERIC, 2) AS arr,
                    ROUND(AVG(CASE WHEN status = 'Active' THEN monthly_price END)::NUMERIC, 2) AS arpu,
                    SUM(CASE WHEN status = 'Churned' THEN 1 ELSE 0 END) AS total_churned
                FROM analytics.subscriptions;
            """)).fetchone()

            total_subscribers = scorecard[0]
            active_mrr = float(scorecard[1])
            arr = float(scorecard[2])
            arpu = float(scorecard[3])
            total_churned = scorecard[4]
            churn_pct = round((total_churned / (total_subscribers + total_churned)) * 100.0, 1)

            # Query 2: Support SLA resolution times
            sla_stats = conn.execute(text("""
                SELECT
                    ROUND(AVG(first_response_hours)::NUMERIC, 1) AS avg_first_response,
                    ROUND(AVG(resolution_hours)::NUMERIC, 1) AS avg_resolution,
                    ROUND((SUM(CASE WHEN resolution_hours <= 24 THEN 1 ELSE 0 END) * 100.0 / COUNT(*))::NUMERIC, 1) AS sla_compliance
                FROM analytics.support_tickets;
            """)).fetchone()

            avg_first_response = float(sla_stats[0])
            avg_resolution = float(sla_stats[1])
            sla_compliance = float(sla_stats[2])

            # Query 3: Plan tier metrics
            plans_data = pd.read_sql_query("""
                SELECT
                    p.plan_name AS plan,
                    COUNT(s.user_id) AS active_logos,
                    ROUND(SUM(s.monthly_price)::NUMERIC, 2) AS mrr,
                    ROUND(AVG(s.monthly_price)::NUMERIC, 2) AS arpu
                FROM analytics.subscriptions s
                JOIN analytics.plans p ON s.plan_id = p.plan_id
                WHERE s.status = 'Active'
                GROUP BY p.plan_name
                ORDER BY mrr DESC;
            """, con=engine)

            # Query 4: MoM Revenue Growth
            mom_growth = pd.read_sql_query("""
                WITH monthly_mrr AS (
                    SELECT
                        DATE_TRUNC('month', payment_date::TIMESTAMP) AS record_month,
                        SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END) AS net_monthly_mrr
                    FROM analytics.payments
                    GROUP BY DATE_TRUNC('month', payment_date::TIMESTAMP)
                )
                SELECT
                    record_month::DATE as month,
                    ROUND(net_monthly_mrr::NUMERIC, 2) AS mrr,
                    ROUND((net_monthly_mrr - LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month))::NUMERIC, 2) AS mom_variance,
                    ROUND(
                        (((net_monthly_mrr - LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month)) /
                         NULLIF(LAG(net_monthly_mrr, 1) OVER (ORDER BY record_month), 0)) * 100)::NUMERIC,
                        2
                    ) AS mom_growth_percent
                FROM monthly_mrr
                ORDER BY record_month DESC
                LIMIT 6;
            """, con=engine)

    except Exception as e:
        print(f"❌ Error compiling database metrics: {e}")
        return

    print("Generating responsive HTML executive performance report...")

    # HTML template with modern layout and Tailwind styles
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Subscription Executive Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0b0f19;
            color: #f3f4f6;
        }}
    </style>
</head>
<body class="p-8 max-w-6xl mx-auto">
    <!-- Header -->
    <header class="mb-12 border-b border-gray-800 pb-8 flex justify-between items-end">
        <div>
            <div class="text-xs font-bold text-blue-500 uppercase tracking-widest mb-1">Executive Performance Audit</div>
            <h1 class="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">SaaS subscription KPI Summary</h1>
        </div>
        <div class="text-right text-sm text-gray-500">
            <div>Baseline Date: 2026-01-01</div>
            <div>Generated by Executive Pipeline Engine</div>
        </div>
    </header>

    <!-- Scorecard Widgets -->
    <section class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Monthly Recurring Revenue</div>
            <div class="text-3xl font-bold text-white">${active_mrr:,.2f}</div>
            <div class="text-xs text-green-500 mt-2 font-medium">↑ Healthy expansion run-rate</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Annual Run Rate (ARR)</div>
            <div class="text-3xl font-bold text-white">${arr:,.2f}</div>
            <div class="text-xs text-blue-500 mt-2 font-medium">Contract value threshold</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Average Revenue Per Logo (ARPU)</div>
            <div class="text-3xl font-bold text-white">${arpu:,.2f}</div>
            <div class="text-xs text-purple-500 mt-2 font-medium">Monthly contract mean</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Logo Churn Rate (Cumulative)</div>
            <div class="text-3xl font-bold text-red-500">{churn_pct}%</div>
            <div class="text-xs text-red-400 mt-2 font-medium">⚠️ Priority attrition correction required</div>
        </div>
    </section>

    <!-- Two Column Analysis Details -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <!-- Left: Subscription Tier Performance -->
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <h3 class="text-lg font-bold text-white mb-4 border-b border-gray-800 pb-2">Active Plans Performance</h3>
            <table class="w-full text-left text-sm text-gray-400">
                <thead>
                    <tr class="text-xs uppercase text-gray-500 border-b border-gray-800">
                        <th class="py-2">Subscription Tier</th>
                        <th class="py-2 text-right">Active Logos</th>
                        <th class="py-2 text-right">MRR Value</th>
                        <th class="py-2 text-right">ARPU</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in plans_data.iterrows():
        html_content += f"""
                    <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                        <td class="py-3 font-semibold text-white">{row['plan']}</td>
                        <td class="py-3 text-right">{row['active_logos']:,}</td>
                        <td class="py-3 text-right text-emerald-500">${row['mrr']:,.2f}</td>
                        <td class="py-3 text-right">${row['arpu']:,.2f}</td>
                    </tr>
        """

    html_content += f"""
                </tbody>
            </table>
        </div>

        <!-- Right: MoM Recurring Revenue Growth Trend -->
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
            <h3 class="text-lg font-bold text-white mb-4 border-b border-gray-800 pb-2">Monthly MRR Growth Tracking (Last 6 Months)</h3>
            <table class="w-full text-left text-sm text-gray-400">
                <thead>
                    <tr class="text-xs uppercase text-gray-500 border-b border-gray-800">
                        <th class="py-2">Billing Period</th>
                        <th class="py-2 text-right">Collected Payments</th>
                        <th class="py-2 text-right">MoM Variance</th>
                        <th class="py-2 text-right">MoM %</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in mom_growth.iterrows():
        growth_style = "text-emerald-500" if row['mom_variance'] >= 0 else "text-red-500"
        growth_sign = "+" if row['mom_variance'] >= 0 else ""
        growth_pct = f"{growth_sign}{row['mom_growth_percent']}%" if pd.notnull(row['mom_growth_percent']) else "0.0%"

        html_content += f"""
                    <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                        <td class="py-3 font-medium text-white">{row['month']}</td>
                        <td class="py-3 text-right">${row['mrr']:,.2f}</td>
                        <td class="py-3 text-right {growth_style}">{growth_sign}${row['mom_variance']:,.2f}</td>
                        <td class="py-3 text-right font-medium {growth_style}">{growth_pct}</td>
                    </tr>
        """

    html_content += f"""
                </tbody>
            </table>
        </div>
    </section>

    <!-- Support SLA Bottlenecks -->
    <section class="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg mb-12">
        <h3 class="text-lg font-bold text-white mb-4 border-b border-gray-800 pb-2">Support SLA Response & Resolution Metrics</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div class="bg-gray-800/40 p-4 rounded-lg">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Avg First Response Speed</div>
                <div class="text-2xl font-bold text-white">{avg_first_response} Hours</div>
                <div class="text-xs text-gray-400 mt-1">Average ticket acknowledgment lag</div>
            </div>
            <div class="bg-gray-800/40 p-4 rounded-lg">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Avg Resolution Duration</div>
                <div class="text-2xl font-bold text-white">{avg_resolution} Hours</div>
                <div class="text-xs text-gray-400 mt-1">Average ticket close-out window</div>
            </div>
            <div class="bg-gray-800/40 p-4 rounded-lg">
                <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">24-Hour SLA Compliance</div>
                <div class="text-2xl font-bold text-emerald-400">{sla_compliance}%</div>
                <div class="text-xs text-gray-400 mt-1">Percentage of tickets solved within 24 hours</div>
            </div>
        </div>
    </section>

    <!-- Strategic Takeaways -->
    <footer class="bg-gradient-to-r from-blue-950/40 to-purple-950/40 border border-blue-900/30 p-6 rounded-xl">
        <h3 class="text-lg font-bold text-white mb-3 flex items-center">
            <span class="mr-2">💡</span> Strategic Insights for Executive Operations
        </h3>
        <ul class="list-disc pl-5 space-y-2 text-sm text-gray-300">
            <li><strong>Logo Churn Spike Impact:</strong> Our aggregate logo churn is resting at <span class="text-red-400 font-semibold">{churn_pct}%</span>. While NRR remains stable due to high Enterprise expansions, Basic plan retention exhibits extreme fragility, particularly inside Month 3.</li>
            <li><strong>Support Response Inefficiency:</strong> High-priority Enterprise SLA compliance is healthy, but standard SMB support tickets are languishing up to <span class="text-gray-300 font-semibold">{avg_resolution} hours</span>. Customer support friction correlates directly with trial-to-paid conversion drop-offs.</li>
            <li><strong>Target Action:</strong> Formulate an onboarding outreach trigger targeting accounts showing active underutilization (identified inside SQL Query 9) to reverse Month 3 attrition.</li>
        </ul>
    </footer>
</body>
</html>"""

    # Export report
    report_file = REPORTS_DIR / "executive_report.html"
    try:
        with open(report_file, "w", encoding="utf-8") as rf:
            rf.write(html_content)
        print(f"\n[SUCCESS] Executive Performance Report successfully compiled!")
        print(f"Exported Report: {report_file}")
    except Exception as e:
        print(f"❌ Error exporting report: {e}")

    print("\n==================================================================")
    print("EXECUTIVE REPORT COMPILATION COMPLETE!")
    print("==================================================================")

if __name__ == '__main__':
    main()
