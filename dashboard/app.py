"""
Interactive dashboard for Loblaw Bio's immune cell population analysis.

Run with:
    streamlit run dashboard/app.py
(or `make dashboard` from the repo root)
"""

import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection
from src.part2_frequencies import compute_frequencies
from src.part3_stats import POPULATIONS, get_filtered_frequencies, run_stats

st.set_page_config(page_title="Loblaw Bio | Immune Cell Analysis", layout="wide")


@st.cache_data
def load_data():
    conn = get_connection()
    try:
        freq = compute_frequencies(conn)
        meta = pd.read_sql_query(
            """
            SELECT s.sample_id AS sample, s.sample_type, s.time_from_treatment_start,
                   su.subject_id, su.project_id, su.condition, su.treatment,
                   su.response, su.sex, su.age
            FROM samples s
            JOIN subjects su ON s.subject_id = su.subject_id
            """,
            conn,
        )
    finally:
        conn.close()
    merged = freq.merge(meta, on="sample")
    return merged


data = load_data()

st.title("Loblaw Bio — Immune Cell Population Dashboard")
st.caption(
    "Explore relative frequencies of immune cell populations across samples, "
    "and compare miraclib responders vs non-responders in melanoma."
)

tab1, tab2, tab3 = st.tabs(
    ["Sample Overview", "Responder vs Non-Responder (Part 3)", "Baseline Subset (Part 4)"]
)

# ---------------------------------------------------------------------------
# Tab 1: Sample overview / explorer (Part 2)
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Cell population frequency per sample")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        conditions = st.multiselect(
            "Condition", sorted(data["condition"].unique()), default=None
        )
    with col2:
        treatments = st.multiselect(
            "Treatment", sorted(data["treatment"].unique()), default=None
        )
    with col3:
        sample_types = st.multiselect(
            "Sample type", sorted(data["sample_type"].unique()), default=None
        )
    with col4:
        sexes = st.multiselect("Sex", sorted(data["sex"].unique()), default=None)

    filtered = data.copy()
    if conditions:
        filtered = filtered[filtered["condition"].isin(conditions)]
    if treatments:
        filtered = filtered[filtered["treatment"].isin(treatments)]
    if sample_types:
        filtered = filtered[filtered["sample_type"].isin(sample_types)]
    if sexes:
        filtered = filtered[filtered["sex"].isin(sexes)]

    st.dataframe(
        filtered[
            [
                "sample",
                "subject_id",
                "project_id",
                "condition",
                "treatment",
                "response",
                "sex",
                "time_from_treatment_start",
                "population",
                "count",
                "total_count",
                "percentage",
            ]
        ].sort_values(["sample", "population"]),
        width="stretch",
        height=350,
    )

    st.markdown("**Average relative frequency (%) by population**")
    avg_by_pop = (
        filtered.groupby("population")["percentage"].mean().round(2).reset_index()
    )
    fig = px.bar(
        avg_by_pop, x="population", y="percentage", color="population",
        labels={"percentage": "Avg relative frequency (%)"},
    )
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Tab 2: Responder vs non-responder analysis (Part 3)
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Melanoma patients on miraclib (PBMC samples): responders vs non-responders")

    conn = get_connection()
    try:
        rvn = get_filtered_frequencies(conn)
    finally:
        conn.close()

    stats_df = run_stats(rvn)

    st.markdown("**Statistical comparison per population**")
    st.dataframe(stats_df, width="stretch")
    st.caption(
        "`mannwhitney_p` is the p-value from a Mann-Whitney U test (non-parametric). "
        "`welch_p` is the p-value from Welch's t-test (parametric, unequal variances). "
        "A population is flagged significant if either test gives p < 0.05."
    )

    significant = stats_df[stats_df["significant_p_lt_0.05"]]["population"].tolist()
    if significant:
        st.success(
            f"Significant difference (p < 0.05) found for: {', '.join(significant)}"
        )
    else:
        st.info("No population reached significance at p < 0.05.")

    pop_choice = st.selectbox("Population to visualize", POPULATIONS)
    sub = rvn[rvn["population"] == pop_choice]
    fig2 = px.box(
        sub,
        x="response",
        y="percentage",
        color="response",
        points="all",
        category_orders={"response": ["no", "yes"]},
        labels={"percentage": "Relative frequency (%)", "response": "Response"},
        title=f"{pop_choice}: relative frequency by response",
    )
    st.plotly_chart(fig2, width="stretch")

# ---------------------------------------------------------------------------
# Tab 3: Baseline subset explorer (Part 4)
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Baseline (day 0) melanoma, miraclib, PBMC samples")

    baseline = data[
        (data["condition"] == "melanoma")
        & (data["treatment"] == "miraclib")
        & (data["sample_type"] == "PBMC")
        & (data["time_from_treatment_start"] == 0)
    ]
    baseline_subjects = baseline.drop_duplicates("subject_id")

    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline samples", baseline["sample"].nunique())
    c2.metric("Subjects", baseline_subjects["subject_id"].nunique())
    c3.metric("Projects represented", baseline["project_id"].nunique())

    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown("**Samples per project**")
        st.dataframe(
            baseline.groupby("project_id")["sample"].nunique().rename("n_samples"),
            width="stretch",
        )
    with colB:
        st.markdown("**Responders vs non-responders (subjects)**")
        st.dataframe(
            baseline_subjects["response"].value_counts().rename("n_subjects"),
            width="stretch",
        )
    with colC:
        st.markdown("**Sex (subjects)**")
        st.dataframe(
            baseline_subjects["sex"].value_counts().rename("n_subjects"),
            width="stretch",
        )

    st.divider()
    st.markdown("**Ad-hoc explorer** — average absolute cell count for a custom slice")

    e1, e2, e3, e4, e5 = st.columns(5)
    with e1:
        e_condition = st.selectbox("Condition", sorted(data["condition"].unique()), key="e_cond")
    with e2:
        e_sex = st.selectbox("Sex", sorted(data["sex"].unique()), key="e_sex")
    with e3:
        e_response = st.selectbox("Response", ["yes", "no"], key="e_resp")
    with e4:
        e_time = st.selectbox("Time from treatment start", sorted(data["time_from_treatment_start"].unique()), key="e_time")
    with e5:
        e_population = st.selectbox("Population", POPULATIONS, key="e_pop")

    e_sub = data[
        (data["condition"] == e_condition)
        & (data["sex"] == e_sex)
        & (data["response"] == e_response)
        & (data["time_from_treatment_start"] == e_time)
        & (data["population"] == e_population)
    ]
    avg_count = e_sub["count"].mean()
    st.metric(
        f"Average {e_population} count "
        f"({e_condition}, {e_sex}, response={e_response}, t={e_time}, all sample/treatment types)",
        f"{avg_count:.2f}" if pd.notna(avg_count) else "N/A",
    )
    st.caption(f"Based on {len(e_sub)} sample(s).")