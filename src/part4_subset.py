"""
Part 4: Data Subset Analysis

1. Identify all melanoma PBMC samples at baseline (time_from_treatment_start = 0)
   from subjects treated with miraclib.
2. Among these samples, report:
   a. How many samples came from each project
   b. How many (distinct) subjects were responders vs non-responders
   c. How many (distinct) subjects were male vs female

Writes:
    outputs/part4_baseline_subset.csv          (the raw subset of samples)
    outputs/part4_samples_per_project.csv
    outputs/part4_responders_by_sex.csv        (kept for reference/debugging)
    outputs/part4_response_counts.csv
    outputs/part4_sex_counts.csv
"""

import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, OUTPUTS_DIR

BASELINE_QUERY = """
SELECT
    s.sample_id,
    s.subject_id,
    su.project_id,
    su.condition,
    su.treatment,
    su.response,
    su.sex,
    su.age,
    s.sample_type,
    s.time_from_treatment_start
FROM samples s
JOIN subjects su ON s.subject_id = su.subject_id
WHERE su.condition = 'melanoma'
  AND su.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
"""


def main():
    conn = get_connection()
    try:
        subset = pd.read_sql_query(BASELINE_QUERY, conn)
    finally:
        conn.close()

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    subset.to_csv(os.path.join(OUTPUTS_DIR, "part4_baseline_subset.csv"), index=False)

    # a) samples per project
    samples_per_project = (
        subset.groupby("project_id")["sample_id"].count()
        .rename("n_samples")
        .reset_index()
        .sort_values("project_id")
    )
    samples_per_project.to_csv(
        os.path.join(OUTPUTS_DIR, "part4_samples_per_project.csv"), index=False
    )

    # b) responders / non-responders (by distinct subject, since response is a
    #    subject-level attribute and each subject contributes one baseline sample here)
    subjects = subset.drop_duplicates("subject_id")
    response_counts = (
        subjects["response"].value_counts(dropna=False)
        .rename_axis("response")
        .reset_index(name="n_subjects")
    )
    response_counts.to_csv(
        os.path.join(OUTPUTS_DIR, "part4_response_counts.csv"), index=False
    )

    # c) male / female
    sex_counts = (
        subjects["sex"].value_counts()
        .rename_axis("sex")
        .reset_index(name="n_subjects")
    )
    sex_counts.to_csv(os.path.join(OUTPUTS_DIR, "part4_sex_counts.csv"), index=False)

    print(f"Baseline melanoma/miraclib/PBMC samples: {len(subset)}")
    print("\nSamples per project:")
    print(samples_per_project.to_string(index=False))
    print("\nResponders vs non-responders (by subject):")
    print(response_counts.to_string(index=False))
    print("\nMale vs female (by subject):")
    print(sex_counts.to_string(index=False))


if __name__ == "__main__":
    main()
