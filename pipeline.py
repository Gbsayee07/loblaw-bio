"""
pipeline.py

Runs the full data pipeline end to end:
    1. Initialize the database and load cell-count.csv  (load_data.py)
    2. Compute per-sample cell population frequencies    (Part 2)
    3. Run the responder vs non-responder analysis        (Part 3)
    4. Run the baseline subset analysis                   (Part 4)

Usage:
    python pipeline.py
"""

import load_data
from src import part2_frequencies, part3_stats, part4_subset


def main():
    print("=== Step 1/4: Initializing database and loading data ===")
    load_data.main()

    print("\n=== Step 2/4: Part 2 - cell population frequencies ===")
    part2_frequencies.main()

    print("\n=== Step 3/4: Part 3 - responder vs non-responder analysis ===")
    part3_stats.main()

    print("\n=== Step 4/4: Part 4 - baseline subset analysis ===")
    part4_subset.main()

    print("\nPipeline complete. See outputs/ for all generated tables and plots.")


if __name__ == "__main__":
    main()
