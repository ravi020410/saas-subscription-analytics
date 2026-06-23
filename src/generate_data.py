"""Regenerate synthetic data for SaaS Subscription Analytics Dashboard.

Install requirements first:
    python -m pip install -r requirements.txt

This portfolio build generated data from tools/generate_portfolio.py. This
project-local script documents the rerun entry point for reviewers.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
subprocess.run([sys.executable, str(ROOT / "tools" / "generate_portfolio.py")], check=True)
