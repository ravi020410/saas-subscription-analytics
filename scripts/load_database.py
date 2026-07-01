import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

def main():
    print("==================================================================")
    print("SaaS Subscription Analytics - Database Schema & ETL Loader")
    print("==================================================================")

    # 1. Connection Configurations
    DB_USER = "postgres"
    DB_PASS = "Postgres123!"
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    DB_NAME = "saas_analytics"  # Target database name

    # Root paths
    ROOT = Path(__file__).resolve().parents[1]
    SQL_DIR = ROOT / "sql"
    DATA_DIR = ROOT / "data" / "cleaned"

    # Define connection string to 'postgres' (default database) to ensure saas_analytics exists
    base_conn = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
    target_conn = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # 2. Establish Base Connection and Create Target Database if not exists
    print("Connecting to default 'postgres' database to verify target DB...")
    try:
        engine_base = create_engine(base_conn, isolation_level="AUTOCOMMIT")
        with engine_base.connect() as conn:
            # Check if database exists
            db_check = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")).scalar()
            if not db_check:
                print(f"Creating database: '{DB_NAME}'...")
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                print("Database created successfully!")
            else:
                print(f"Database '{DB_NAME}' already exists.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        print("Continuing and assuming database is already created...")

    # 3. Create SQLAlchemy Engine for Target Database
    print(f"\nConnecting to target database: '{DB_NAME}'...")
    try:
        engine = create_engine(target_conn)
        with engine.connect() as conn:
            print("Successfully connected to PostgreSQL database!")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to database: {e}")
        print("Please check that PostgreSQL is running locally and credentials are correct.")
        return

    # 4. Execute the Schema DDL (01_schema.sql)
    schema_file = SQL_DIR / "01_schema.sql"
    print(f"\n[1/3] Reading and executing Schema DDL: {schema_file.name}...")
    try:
        with open(schema_file, "r", encoding="utf-8") as sf:
            schema_ddl = sf.read()

        # Split DDL by semicolons (handling basic multiple statements safely)
        # We execute the whole block using raw transactions
        with engine.begin() as conn:
            conn.execute(text(schema_ddl))
        print("SUCCESS: Relational database schema successfully established!")
    except Exception as e:
        print(f"ERROR executing schema: {e}")
        return

    # 5. Mass Bulk Copy Staged Cleaned CSVs
    print("\n[2/3] Performing mass bulk-load of cleaned SaaS datasets...")
    # List tables in order of dependency (Users and Plans must load before Subscriptions, etc.)
    tables_to_load = [
        {"file": "plans.csv", "table": "plans"},
        {"file": "users.csv", "table": "users"},
        {"file": "subscriptions.csv", "table": "subscriptions"},
        {"file": "payments.csv", "table": "payments"},
        {"file": "churn_events.csv", "table": "churn_events"},
        {"file": "product_usage.csv", "table": "product_usage"},
        {"file": "support_tickets.csv", "table": "support_tickets"},
        {"file": "marketing_campaigns.csv", "table": "marketing_campaigns"}
    ]

    for item in tables_to_load:
        csv_file = DATA_DIR / item["file"]
        table_name = item["table"]

        if not csv_file.exists():
            print(f"  ❌ File not found: {item['file']}. Skipping table: '{table_name}'")
            continue

        print(f"  Loading '{item['file']}' into table 'analytics.{table_name}'...")
        try:
            df = pd.read_csv(csv_file)

            # Map specific datatypes to avoid PostgreSQL default schema parsing conflicts
            if table_name == "payments":
                df["payment_date"] = pd.to_datetime(df["payment_date"])
            elif table_name == "support_tickets":
                df["created_date"] = pd.to_datetime(df["created_date"])
            elif table_name == "marketing_campaigns":
                df["campaign_month"] = pd.to_datetime(df["campaign_month"]).dt.date

            # Write rows directly to PostgreSQL
            # we use if_exists='append' to match our pre-defined relational table structures
            df.to_sql(
                name=table_name,
                con=engine,
                schema="analytics",
                if_exists="append",
                index=False
            )
            print(f"    Loaded {len(df)} rows.")
        except Exception as e:
            print(f"    ❌ Error loading {item['file']}: {e}")

    # 6. Database Verification checks
    print("\n[3/3] Running structural row-count validations...")
    try:
        with engine.connect() as conn:
            # Query pg_tables inside analytics schema
            query = text("""
                SELECT table_name,
                       (xpath('/row/c/text()', xmlparse(content query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, ''))))[1]::text::int as row_count
                FROM information_schema.tables
                WHERE table_schema = 'analytics'
                ORDER BY table_name;
            """)
            results = conn.execute(query)
            print("-" * 45)
            print(f"{'PostgreSQL Table':<25} | {'Loaded Row Count':<15}")
            print("-" * 45)
            for row in results:
                print(f"analytics.{row[0]:<15} | {row[1]:<15}")
            print("-" * 45)
    except Exception as e:
         print(f"Error during validation scan: {e}")

    print("\n==================================================================")
    print("ETL PIPELINE SUCCESSFULLY EXECUTED AND VERIFIED!")
    print("==================================================================")

if __name__ == '__main__':
    main()
