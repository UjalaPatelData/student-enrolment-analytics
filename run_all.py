"""Runs the full pipeline: generate data -> clean -> load to SQLite -> analyze."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import analyze, clean_data, generate_data  # noqa: E402

if __name__ == "__main__":
    print("== 1. Generating synthetic applications ==");  generate_data.main()
    print("\n== 2. Data quality and cleaning ==");        clean_data.main()
    print("\n== 3. SQL analysis and charts ==");            analyze.main()
