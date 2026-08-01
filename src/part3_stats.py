"""
Part 3: Statistical Analysis

Compares relative frequencies of each immune cell population between
responders and non-responders, restricted to:
    - condition = melanoma
    - treatment = miraclib
    - sample_type = PBMC

Produces:
    outputs/responder_vs_nonresponder_stats.csv   (Mann-Whitney U + Welch's t-test per population)
    outputs/boxplots/<population>.png              (one boxplot per population)
    outputs/boxplots/all_populations.png            (combined figure)
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, OUTPUTS_DIR
from src.part2_frequencies import compute_frequencies

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def get_filtered_frequencies(conn):
    """Relative frequencies for melanoma / miraclib / PBMC samples, with response label."""
    freq = compute_frequencies(conn)

    meta = pd.read_sql_query(
        """
        SELECT s.sample_id AS sample, s.sample_type, su.condition, su.treatment, su.response
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
        """,
        conn,
    )

    merged = freq.merge(meta, on="sample")
    filtered = merged[
        (merged["condition"] == "melanoma")
        & (merged["treatment"] == "miraclib")
        & (merged["sample_type"] == "PBMC")
        & (merged["response"].isin(["yes", "no"]))
    ].copy()

    return filtered


def run_stats(filtered):
    rows = []
    for pop in POPULATIONS:
        sub = filtered[filtered["population"] == pop]
        responders = sub[sub["response"] == "yes"]["percentage"]
        non_responders = sub[sub["response"] == "no"]["percentage"]

        u_stat, u_p = stats.mannwhitneyu(
            responders, non_responders, alternative="two-sided"
        )
        t_stat, t_p = stats.ttest_ind(responders, non_responders, equal_var=False)

        rows.append(
            {
                "population": pop,
                "n_responders": len(responders),
                "n_non_responders": len(non_responders),
                "responder_mean_pct": round(responders.mean(), 2),
                "non_responder_mean_pct": round(non_responders.mean(), 2),
                "mannwhitney_u": round(u_stat, 3),
                "mannwhitney_p": round(u_p, 5),
                "welch_t": round(t_stat, 3),
                "welch_p": round(t_p, 5),
                "significant_p_lt_0.05": (u_p < 0.05) or (t_p < 0.05),
            }
        )

    return pd.DataFrame(rows).sort_values("mannwhitney_p").reset_index(drop=True)


def make_boxplots(filtered, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sns.set_style("whitegrid")

    # Combined figure, one subplot per population
    fig, axes = plt.subplots(1, len(POPULATIONS), figsize=(4 * len(POPULATIONS), 5))
    for ax, pop in zip(axes, POPULATIONS):
        sub = filtered[filtered["population"] == pop]
        sns.boxplot(
            data=sub,
            x="response",
            y="percentage",
            order=["no", "yes"],
            ax=ax,
            hue="response",
            palette={"no": "#e07a5f", "yes": "#3d5a80"},
            legend=False,
        )
        sns.stripplot(
            data=sub,
            x="response",
            y="percentage",
            order=["no", "yes"],
            ax=ax,
            color="black",
            alpha=0.4,
            size=3,
        )
        ax.set_title(pop)
        ax.set_xlabel("Response")
        ax.set_ylabel("Relative frequency (%)")

    fig.suptitle(
        "Cell population frequency: responders vs non-responders\n"
        "(melanoma, miraclib, PBMC)"
    )
    fig.tight_layout()
    combined_path = os.path.join(out_dir, "all_populations.png")
    fig.savefig(combined_path, dpi=150)
    plt.close(fig)

    # Individual per-population plots
    for pop in POPULATIONS:
        sub = filtered[filtered["population"] == pop]
        fig, ax = plt.subplots(figsize=(5, 5))
        sns.boxplot(
            data=sub,
            x="response",
            y="percentage",
            order=["no", "yes"],
            ax=ax,
            hue="response",
            palette={"no": "#e07a5f", "yes": "#3d5a80"},
            legend=False,
        )
        sns.stripplot(
            data=sub,
            x="response",
            y="percentage",
            order=["no", "yes"],
            ax=ax,
            color="black",
            alpha=0.4,
            size=4,
        )
        ax.set_title(f"{pop}: responders vs non-responders")
        ax.set_xlabel("Response")
        ax.set_ylabel("Relative frequency (%)")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"{pop}.png"), dpi=150)
        plt.close(fig)

    return combined_path


def main():
    conn = get_connection()
    try:
        filtered = get_filtered_frequencies(conn)
    finally:
        conn.close()

    stats_df = run_stats(filtered)

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    stats_path = os.path.join(OUTPUTS_DIR, "responder_vs_nonresponder_stats.csv")
    stats_df.to_csv(stats_path, index=False)

    boxplot_dir = os.path.join(OUTPUTS_DIR, "boxplots")
    make_boxplots(filtered, boxplot_dir)

    print(f"Wrote stats to {stats_path}")
    print(stats_df.to_string(index=False))
    print(f"Wrote boxplots to {boxplot_dir}")


if __name__ == "__main__":
    main()
