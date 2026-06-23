from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for csv_path in (ROOT / "data" / "raw").glob("*.csv"):
    df = pd.read_csv(csv_path)
    if "quality_issue" in df.columns:
        id_candidates = [c for c in df.columns if c.endswith("_id")]
        if id_candidates:
            df = df.drop_duplicates(subset=id_candidates[:1])
        df = df[df["quality_issue"].fillna("").str.contains("missing", case=False) == False]
    df.to_csv(ROOT / "data" / "cleaned" / csv_path.name, index=False)
print("Cleaned raw CSVs into data/cleaned.")
