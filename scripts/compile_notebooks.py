import os
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def main():
    print("==================================================================")
    print("SaaS Subscription Analytics - Programmatic Notebook Compiler")
    print("==================================================================")

    # 1. Define Paths
    ROOT = Path(__file__).resolve().parents[1]
    NOTEBOOKS_DIR = ROOT / "notebooks"
    VISUALS_DIR = ROOT / "visuals"

    VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # Ordered list of notebooks to execute chronologically
    notebooks = [
        "01_eda.ipynb",
        "02_data_cleaning.ipynb",
        "03_feature_engineering.ipynb",
        "04_visualization.ipynb",
        "05_business_insights.ipynb"
    ]

    # Initialize Execution Preprocessor
    # timeout=600 gives plenty of time for ML fitting and file writing
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

    print(f"Reading notebooks from: {NOTEBOOKS_DIR}")
    print(f"Target visuals directory: {VISUALS_DIR}\n")

    for nb_name in notebooks:
        nb_path = NOTEBOOKS_DIR / nb_name
        if not nb_path.exists():
            print(f"❌ Notebook not found: {nb_name}. Skipping.")
            continue

        print(f"Compiling and executing: {nb_name}...")
        try:
            # Load notebook JSON structure
            with open(nb_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)

            # Change working directory of the execution to notebooks directory
            # so relative paths (like Path("..")) resolve correctly
            ep.preprocess(nb, {"metadata": {"path": str(NOTEBOOKS_DIR)}})

            # Save the fully-executed notebook back to disk
            with open(nb_path, "w", encoding="utf-8") as f:
                nbformat.write(nb, f)

            print(f"  [SUCCESS] Executed and saved outputs for {nb_name}")

        except Exception as e:
            print(f"  [ERROR] Failed to compile {nb_name}: {e}")

    print("\n==================================================================")
    print("ALL NOTEBOOKS EXECUTED AND EMBEDDED OUTPUTS PERSISTED!")
    print("==================================================================")

if __name__ == '__main__':
    main()
