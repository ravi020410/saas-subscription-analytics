import os
from pathlib import Path
import random
import csv
from datetime import datetime, timedelta

def main():
    print("==================================================================")
    print("SaaS Subscription Analytics - Autonomous Data Synthesis Engine")
    print("==================================================================")

    # 1. Define Paths
    ROOT = Path(__file__).resolve().parents[1]
    RAW_DIR = ROOT / "data" / "raw"
    CLEANED_DIR = ROOT / "data" / "cleaned"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Target raw directory: {RAW_DIR}")

    # Seed for deterministic yet realistic outputs
    random.seed(42)

    # 2. Generate Plans
    print("\n[1/8] Generating Plans Table (plans.csv)...")
    plans = [
        {"plan_id": 101, "plan_name": "Basic", "monthly_price": 15.00, "target_segment": "SMB", "max_seats": 5},
        {"plan_id": 102, "plan_name": "Professional", "monthly_price": 99.00, "target_segment": "Mid-Market", "max_seats": 25},
        {"plan_id": 103, "plan_name": "Enterprise", "monthly_price": 499.00, "target_segment": "Enterprise", "max_seats": 250}
    ]

    plans_file = RAW_DIR / "plans.csv"
    with open(plans_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["plan_id", "plan_name", "monthly_price", "target_segment", "max_seats"])
        writer.writeheader()
        writer.writerows(plans)

    # 3. Generate Users
    print("[2/8] Generating Users Table (users.csv)...")
    regions = ["North America", "Europe", "APAC", "LATAM"]
    channels = ["Organic Search", "Google Ads", "LinkedIn Ads", "Content Marketing", "Email Referral"]
    company_sizes = ["1-10", "11-50", "51-200", "201-500", "501+"]

    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 12, 31)
    total_days = (end_date - start_date).days

    users = []
    user_count = 1500  # Substantial enough for complex analysis

    for i in range(1, user_count + 1):
        user_id = 10000 + i
        # Linear distribution of signups over 4 years to simulate growth
        days_offset = int(random.triangular(0, total_days, total_days * 0.7))
        signup_datetime = start_date + timedelta(days=days_offset)
        signup_date_str = signup_datetime.strftime("%Y-%m-%d")

        region = random.choices(regions, weights=[0.45, 0.30, 0.15, 0.10])[0]
        channel = random.choices(channels, weights=[0.25, 0.30, 0.20, 0.15, 0.10])[0]
        company_size = random.choices(company_sizes, weights=[0.40, 0.30, 0.18, 0.08, 0.04])[0]

        users.append({
            "user_id": user_id,
            "region": region,
            "acquisition_channel": channel,
            "company_size": company_size,
            "signup_date": signup_date_str
        })

    users_file = RAW_DIR / "users.csv"
    with open(users_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "region", "acquisition_channel", "company_size", "signup_date"])
        writer.writeheader()
        writer.writerows(users)

    # 4. Generate Subscriptions
    print("[3/8] Generating Subscriptions Table (subscriptions.csv)...")
    subscriptions = []
    sub_counter = 50000

    # Track subscriptions for payments and usage logic
    active_subs = []
    all_subs = []

    for u in users:
        u_id = u["user_id"]
        u_signup = datetime.strptime(u["signup_date"], "%Y-%m-%d")
        c_size = u["company_size"]

        # Decide initial plan based on company size
        if c_size in ["501+", "201-500"]:
            initial_plan = random.choices([102, 103], weights=[0.20, 0.80])[0]
        elif c_size in ["51-200"]:
            initial_plan = random.choices([101, 102, 103], weights=[0.20, 0.70, 0.10])[0]
        else:
            initial_plan = random.choices([101, 102], weights=[0.85, 0.15])[0]

        sub_id = sub_counter + 1
        sub_counter += 1

        # Determine duration / status
        # Inject standard Month 3 churn spike (users canceling after onboarding fades)
        # Inject long lifespans for Enterprise tiers vs. high churn for Basic tiers
        rand_val = random.random()

        status = "Active"
        months_active = 1

        if initial_plan == 101:  # Basic
            if rand_val < 0.25:  # Churn in month 1-3
                months_active = random.choice([1, 2, 3])
                status = "Churned"
            elif rand_val < 0.55:  # Churn later
                months_active = random.randint(4, 18)
                status = "Churned"
            else:
                months_active = (datetime(2026, 1, 1) - u_signup).days // 30
                months_active = max(1, months_active)
        elif initial_plan == 102:  # Professional
            if rand_val < 0.12:  # Month 3 spike
                months_active = 3
                status = "Churned"
            elif rand_val < 0.35:
                months_active = random.randint(4, 24)
                status = "Churned"
            else:
                months_active = (datetime(2026, 1, 1) - u_signup).days // 30
                months_active = max(1, months_active)
        else:  # Enterprise
            if rand_val < 0.15:  # Enterprise is sticky
                months_active = random.randint(6, 24)
                status = "Churned"
            else:
                months_active = (datetime(2026, 1, 1) - u_signup).days // 30
                months_active = max(1, months_active)

        # Cap months active if they exceed the absolute current date boundary (Jan 1, 2026)
        max_possible_months = (datetime(2026, 1, 1) - u_signup).days // 30
        if status == "Churned" and months_active > max_possible_months:
            months_active = max_possible_months
        elif status == "Active":
            months_active = max_possible_months

        months_active = max(1, months_active)

        sub_start = u_signup
        sub_end = sub_start + timedelta(days=months_active * 30)

        sub_end_str = sub_end.strftime("%Y-%m-%d") if status == "Churned" else ""
        monthly_price_mapping = {101: 15.00, 102: 99.00, 103: 499.00}

        sub_record = {
            "subscription_id": sub_id,
            "user_id": u_id,
            "plan_id": initial_plan,
            "status": status,
            "start_date": sub_start.strftime("%Y-%m-%d"),
            "end_date": sub_end_str,
            "monthly_price": monthly_price_mapping[initial_plan],
            "mrr": monthly_price_mapping[initial_plan]  # Add mrr column to match notebook contract
        }

        subscriptions.append(sub_record)
        all_subs.append({
            "sub_id": sub_id,
            "user_id": u_id,
            "plan_id": initial_plan,
            "status": status,
            "start": sub_start,
            "end": sub_end,
            "months": months_active,
            "price": monthly_price_mapping[initial_plan]
        })

    sub_file = RAW_DIR / "subscriptions.csv"
    with open(sub_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subscription_id", "user_id", "plan_id", "status", "start_date", "end_date", "monthly_price", "mrr"])
        writer.writeheader()
        writer.writerows(subscriptions)

    # 5. Generate Payments
    print("[4/8] Generating Payments Table (payments.csv)...")
    payments = []
    payment_counter = 800000

    for s in all_subs:
        start_dt = s["start"]
        price = s["price"]

        for m in range(s["months"]):
            p_date = start_dt + timedelta(days=m * 30)
            p_id = payment_counter + 1
            payment_counter += 1

            # Simulate billing transaction errors (~1.5% transaction failures)
            # Active subscribers always resolve, but some show a failed decline transaction first
            if random.random() < 0.015:
                # Add failed record
                payments.append({
                    "payment_id": p_id,
                    "subscription_id": s["sub_id"],
                    "user_id": s["user_id"],
                    "plan_id": s["plan_id"],
                    "payment_date": p_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": price,
                    "payment_status": "Failed"
                })
                # Re-issue successful payment 1 day later
                p_id_retry = payment_counter + 1
                payment_counter += 1
                payments.append({
                    "payment_id": p_id_retry,
                    "subscription_id": s["sub_id"],
                    "user_id": s["user_id"],
                    "plan_id": s["plan_id"],
                    "payment_date": (p_date + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": price,
                    "payment_status": "Paid"
                })
            else:
                payments.append({
                    "payment_id": p_id,
                    "subscription_id": s["sub_id"],
                    "user_id": s["user_id"],
                    "plan_id": s["plan_id"],
                    "payment_date": p_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": price,
                    "payment_status": "Paid"
                })

    payments_file = RAW_DIR / "payments.csv"
    with open(payments_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["payment_id", "subscription_id", "user_id", "plan_id", "payment_date", "amount", "payment_status"])
        writer.writeheader()
        writer.writerows(payments)

    # 6. Generate Churn Events
    print("[5/8] Generating Churn Events Table (churn_events.csv)...")
    churn_events = []
    reasons = [
        "Price is too high / Budget cuts",
        "Switched to direct competitor",
        "Missing features or platform limitations",
        "Technical support backlog / unresolved SLA",
        "Underutilization / poor feature onboarding"
    ]

    for s in all_subs:
        if s["status"] == "Churned":
            # Select reason based on plan price and support bottlenecks
            if s["price"] == 499.00:  # Enterprise
                reason = random.choices(reasons, weights=[0.10, 0.35, 0.25, 0.20, 0.10])[0]
            elif s["price"] == 15.00:  # Basic
                reason = random.choices(reasons, weights=[0.40, 0.20, 0.10, 0.10, 0.20])[0]
            else:
                reason = random.choice(reasons)

            churn_events.append({
                "subscription_id": s["sub_id"],
                "user_id": s["user_id"],
                "churn_date": s["end"].strftime("%Y-%m-%d"),
                "churn_reason": reason,
                "mrr": s["price"]
            })

    churn_file = RAW_DIR / "churn_events.csv"
    with open(churn_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subscription_id", "user_id", "churn_date", "churn_reason", "mrr"])
        writer.writeheader()
        writer.writerows(churn_events)

    # 7. Generate Product Usage Logs
    print("[6/8] Generating Product Usage Table (product_usage.csv)...")
    product_usage = []
    features_pool = ["Dashboard", "CSV Export", "API Query", "Report Generation", "Settings Update", "Integration Sync"]

    for s in all_subs:
        # Loop through user history to generate activity records
        start_dt = s["start"]
        months = s["months"]
        u_id = s["user_id"]

        # Decide usage metrics based on plan tier and status
        # If user churned, usage decline precedes the churn date (critical analytical feature!)
        for m in range(months):
            m_start = start_dt + timedelta(days=m * 30)

            # Construct usage parameters
            if s["plan_id"] == 103:  # Enterprise
                base_minutes = 2000
                base_events = 1500
            elif s["plan_id"] == 102:  # Pro
                base_minutes = 600
                base_events = 450
            else:  # Basic
                base_minutes = 150
                base_events = 80

            # If they are in their final month before churning, drop usage by 70%
            if s["status"] == "Churned" and m == (months - 1):
                base_minutes = int(base_minutes * 0.25)
                base_events = int(base_events * 0.20)

            # Underutilized warning group: simulate some active users with absolute zero usage in 45 days
            is_underutilized_active = (s["status"] == "Active" and s["plan_id"] == 101 and random.random() < 0.10 and m >= (months - 2))

            if is_underutilized_active:
                base_minutes = 0
                base_events = 0

            # Generate 4 record logs per month (weekly telemetry aggregation)
            for w in range(4):
                log_date = m_start + timedelta(days=w * 7 + random.randint(0, 3))
                if log_date > datetime(2025, 12, 31):
                    continue

                weekly_minutes = int(random.normalvariate(base_minutes / 4.0, (base_minutes / 4.0) * 0.2)) if base_minutes > 0 else 0
                weekly_events = int(random.normalvariate(base_events / 4.0, (base_events / 4.0) * 0.2)) if base_events > 0 else 0

                weekly_minutes = max(0, weekly_minutes)
                weekly_events = max(0, weekly_events)

                feature_used = random.choice(features_pool) if weekly_events > 0 else "None"

                product_usage.append({
                    "user_id": u_id,
                    "event_date": log_date.strftime("%Y-%m-%d"),
                    "feature": feature_used,               # Add feature column matching notebook contract
                    "active_minutes": weekly_minutes,       # Rename minutes_active -> active_minutes
                    "events": weekly_events
                })

    usage_file = RAW_DIR / "product_usage.csv"
    with open(usage_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "event_date", "feature", "active_minutes", "events"])
        writer.writeheader()
        writer.writerows(product_usage)

    # 8. Generate Support Tickets (SLA Validation)
    print("[7/8] Generating Support Tickets Table (support_tickets.csv)...")
    support_tickets = []
    ticket_counter = 4000

    categories = ["Technical Issue", "Billing Query", "Feature Request", "Onboarding Help"]
    priorities = ["Low", "Medium", "High"]

    for s in all_subs:
        u_id = s["user_id"]
        start_dt = s["start"]
        months = s["months"]

        # High plan users and churning users submit more support tickets
        num_tickets = 0
        if s["status"] == "Churned":
            num_tickets = random.choices([0, 1, 2, 3], weights=[0.20, 0.40, 0.30, 0.10])[0]
        else:
            num_tickets = random.choices([0, 1, 2], weights=[0.70, 0.25, 0.05])[0]

        for t in range(num_tickets):
            t_id = ticket_counter + 1
            ticket_counter += 1

            # Select random date within subscription range
            t_offset = random.randint(1, max(30, months * 30 - 2))
            t_date = start_dt + timedelta(days=t_offset)
            if t_date > datetime(2025, 12, 31):
                continue

            priority = random.choices(priorities, weights=[0.60, 0.30, 0.10])[0]
            # Enterprise plans get prioritized ticket queues
            if s["plan_id"] == 103:
                priority = random.choices(["Medium", "High"], weights=[0.30, 0.70])[0]

            category = random.choices(categories, weights=[0.40, 0.30, 0.20, 0.10])[0]

            # SLAs: Response and Resolution Hours
            # Inject SLA failures: SMB low tickets take > 40 hours to resolve.
            # Enterprise high tickets take < 2 hours response, < 8 hours resolution.
            if priority == "High":
                first_resp = round(random.uniform(0.1, 1.5), 1)
                resol = round(random.uniform(1.0, 8.0), 1)
            elif priority == "Medium":
                first_resp = round(random.uniform(1.0, 4.0), 1)
                resol = round(random.uniform(8.0, 24.0), 1)
            else: # Low priority SLA Bottleneck
                first_resp = round(random.uniform(4.0, 12.0), 1)
                resol = round(random.uniform(12.0, 48.0), 1) # Violates standard 24h SLA

            support_tickets.append({
                "ticket_id": t_id,
                "user_id": u_id,
                "created_date": t_date.strftime("%Y-%m-%d %H:%M:%S"),
                "category": category,
                "priority": priority,
                "first_response_hours": first_resp,
                "resolution_hours": resol
            })

    tickets_file = RAW_DIR / "support_tickets.csv"
    with open(tickets_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket_id", "user_id", "created_date", "category", "priority", "first_response_hours", "resolution_hours"])
        writer.writeheader()
        writer.writerows(support_tickets)

    # 9. Generate Marketing Spend Table
    print("[8/8] Generating Marketing Campaign Metrics (marketing_campaigns.csv)...")
    marketing_campaigns = []

    # 4 channels across 4 years (monthly tracking)
    m_channels = ["Organic Search", "Google Ads", "LinkedIn Ads", "Content Marketing", "Email Referral"]
    monthly_spends = {
        "Organic Search": 1200.00,      # SEO writers, tool cost
        "Google Ads": 15000.00,         # Heavy PPC spend
        "LinkedIn Ads": 18000.00,       # Elite B2B targeting, high CAC
        "Content Marketing": 4500.00,   # Dynamic value blogging
        "Email Referral": 800.00
    }

    cur_m = datetime(2022, 1, 1)
    camp_id = 1

    while cur_m <= datetime(2025, 12, 1):
        m_str = cur_m.strftime("%Y-%m-%d")

        for mc in m_channels:
            spend = monthly_spends[mc]
            # Vary spend slightly month-over-month
            spend_var = spend * random.uniform(0.9, 1.1)

            # Map trial signups and conversion to paid logic
            if mc == "LinkedIn Ads":
                conversions = int(spend_var / 350.0) # High CAC
                trials = int(conversions * 4.5)
            elif mc == "Google Ads":
                conversions = int(spend_var / 220.0)
                trials = int(conversions * 6.0)
            elif mc == "Content Marketing":
                conversions = int(spend_var / 120.0) # Organic, low CAC, highly sticky
                trials = int(conversions * 5.0)
            else: # Referral / Organic
                conversions = int(spend_var / 40.0)
                trials = int(conversions * 8.0)

            marketing_campaigns.append({
                "campaign_id": camp_id,
                "campaign_month": m_str,
                "channel": mc,
                "spend": round(spend_var, 2),
                "trial_signups": trials,
                "paid_conversions": conversions
            })
            camp_id += 1

        # Increment month
        cur_m = (cur_m + timedelta(days=32)).replace(day=1)

    m_file = RAW_DIR / "marketing_campaigns.csv"
    with open(m_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["campaign_id", "campaign_month", "channel", "spend", "trial_signups", "paid_conversions"])
        writer.writeheader()
        writer.writerows(marketing_campaigns)

    # 10. Pre-computed Monthly KPIs (Ensuring standard baseline runs smoothly)
    print("\nPre-computing Monthly Baseline Aggregations (monthly_kpis.csv)...")
    monthly_kpis = []

    cur_m = datetime(2022, 1, 1)
    while cur_m <= datetime(2025, 12, 1):
        m_str = cur_m.strftime("%Y-%m-%d")

        # Calculate users active during this month
        active_logos = 0
        total_mrr = 0.0

        for s in all_subs:
            sub_start = s["start"]
            sub_end = s["end"]

            # User is active this month if their signup was before or in this month,
            # and they either haven't churned or churned after this month.
            is_active_this_month = (sub_start.year < cur_m.year or (sub_start.year == cur_m.year and sub_start.month <= cur_m.month))
            if s["status"] == "Churned":
                is_active_this_month = is_active_this_month and (sub_end.year > cur_m.year or (sub_end.year == cur_m.year and sub_end.month >= cur_m.month))

            if is_active_this_month:
                active_logos += 1
                total_mrr += s["price"]

        # Simulate slight metrics noise
        monthly_kpis.append({
            "month": m_str,
            "active_logos": active_logos,
            "mrr": round(total_mrr, 2),
            "arr": round(total_mrr * 12.0, 2),
            "nrr": round(random.uniform(1.02, 1.15), 2),
            "churn_rate": round(random.uniform(2.1, 4.5), 2)
        })

        cur_m = (cur_m + timedelta(days=32)).replace(day=1)

    kpi_file = RAW_DIR / "monthly_kpis.csv"
    with open(kpi_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "active_logos", "mrr", "arr", "nrr", "churn_rate"])
        writer.writeheader()
        writer.writerows(monthly_kpis)

    print("\n==================================================================")
    print("SUCCESS: Relational SaaS datasets successfully synthesized!")
    print(f"Generated raw data stored in: {RAW_DIR}")
    print("==================================================================")

if __name__ == '__main__':
    main()
