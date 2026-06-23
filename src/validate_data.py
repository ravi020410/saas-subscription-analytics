from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
failures = []
for csv_path in sorted((ROOT / "data" / "cleaned").glob("*.csv")):
    df = pd.read_csv(csv_path)
    if df.empty:
        failures.append(f"{csv_path.name}: empty")
    duplicate_count = df.duplicated().sum()
    if duplicate_count:
        failures.append(f"{csv_path.name}: {duplicate_count} duplicate full rows")
print("\n".join(failures) if failures else "All cleaned CSV checks passed.")
raise SystemExit(1 if failures else 0)
