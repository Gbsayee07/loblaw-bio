"""
Part 2: Data Overview

For each sample, computes the total cell count (sum across all five
populations) and the relative frequency (%) of each population.

Output columns: sample, total_count, population, count, percentage
Writes: outputs/cell_frequencies.csv
"""

import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, OUTPUTS_DIR


def compute_frequencies(conn):
    counts = pd.read_sql_query(
        "SELECT sample_id AS sample, population, count FROM cell_counts", conn
    )

    totals = counts.groupby("sample")["count"].sum().rename("total_count")
    counts = counts.merge(totals, on="sample")
    counts["percentage"] = (counts["count"] / counts["total_count"] * 100).round(2)

    result = counts[["sample", "total_count", "population", "count", "percentage"]]
    result = result.sort_values(["sample", "population"]).reset_index(drop=True)
    return result


def main():
    conn = get_connection()
    try:
        result = compute_frequencies(conn)
    finally:
        conn.close()

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUTS_DIR, "cell_frequencies.csv")
    result.to_csv(out_path, index=False)

    print(f"Wrote {len(result)} rows to {out_path}")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
