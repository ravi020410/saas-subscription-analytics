from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
print(f"Reports are generated in {ROOT / 'reports'} by tools/generate_portfolio.py.")
