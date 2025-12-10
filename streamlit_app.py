import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

session = get_active_session()

st.set_page_config(page_title="EDW-2 Reasoning Assistant", layout="wide")
st.title("EDW-2 Reasoning Assistant (Snowflake Native)")

# -----------------------------
# USER INPUT
# -----------------------------
question = st.text_input("Ask a business reasoning question:")
run = st.button("Run Analysis")

# -----------------------------
# STEP 1: DYNAMIC SUB-QUESTIONS
# -----------------------------
def generate_subquestions(question):
    return [
        "How did total revenue change across the last two quarters?",
        "Which region experienced the largest revenue change?",
        "Which product category contributed most to the change?"
    ]

# -----------------------------
# STEP 2: ANALYTICS FROM VIEWS
# -----------------------------
def run_analytics():
    rev = session.sql("SELECT * FROM V_REVENUE_BY_QUARTER").to_pandas()
    reg = session.sql("SELECT * FROM V_REVENUE_BY_REGION").to_pandas()
    prod = session.sql("SELECT * FROM V_REVENUE_BY_PRODUCT").to_pandas()
    return rev, reg, prod

# -----------------------------
# STEP 3: CORTEX REASONING
# -----------------------------
def cortex_reasoning(rev, reg, prod, question):

    last_two = rev.tail(2)
    delta = last_two.iloc[1]["TOTAL_REVENUE"] - last_two.iloc[0]["TOTAL_REVENUE"]

    worst_region = (
        reg.groupby("REGION")["TOTAL_REVENUE"].sum()
        .sort_values()
        .idxmin()
    )

    worst_product = (
        prod.groupby("PRODUCT")["TOTAL_REVENUE"].sum()
        .sort_values()
        .idxmin()
    )

    prompt = f"""
User Question:
{question}

Key Findings:
Revenue change between last two quarters: {delta}
Region with weakest performance: {worst_region}
Product with weakest performance: {worst_product}

Write a professional, concise business explanation.
No bullet points.
No recommendations.
Only explain what happened and why.
"""

    cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-8b-instant',
            '{prompt}'
        );
    """

    return session.sql(cortex_sql).collect()[0][0]

# -----------------------------
# MAIN EXECUTION
# -----------------------------
if run and question:

    st.subheader("Step 1 — Generated Sub-Questions")
    for q in generate_subquestions(question):
        st.markdown(f"- {q}")

    st.subheader("Step 2 — Snowflake Analytics")
    rev, reg, prod = run_analytics()
    st.success("Analytics successfully generated from Snowflake.")

    st.subheader("Step 3 — AI Reasoning (Cortex)")

    final_answer = cortex_reasoning(rev, reg, prod, question)

    st.subheader("Final AI Explanation")

    st.markdown(
        f"""
<div style="background-color:#ecf7ee;padding:20px;border-radius:8px;font-size:16px;line-height:1.6;">
{final_answer}
</div>
""",
        unsafe_allow_html=True
    )
