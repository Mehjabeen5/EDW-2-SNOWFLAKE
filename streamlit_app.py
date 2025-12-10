import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

# ✅ Use active Snowflake session (App-native)
session = get_active_session()

# -----------------------------
# PAGE HEADER
# -----------------------------
st.set_page_config(page_title="EDW-2 Reasoning Assistant", layout="wide")

st.title("🧠 EDW-2 Reasoning Assistant")

st.info("""
**Reasoning Agent Activated**
""")

# -----------------------------
# USER INPUT
# -----------------------------
question = st.text_input("🔎 Ask a reasoning question:")
run = st.button("Run Reasoning")

# -----------------------------
# STEP 1: SUB-QUESTIONS
# -----------------------------
def generate_subquestions(question):

    q = question.lower()

    if "why" in q and "revenue" in q:
        return [
            "How did total revenue change compared to the previous quarter?",
            "Which region saw the largest revenue drop?",
            "Which product contributed most to the decline?"
        ]

    elif "highest" in q or "top" in q:
        return [
            "Which quarter recorded the highest total revenue?",
            "Which region contributed most in that quarter?",
            "Which product contributed most in that quarter?"
        ]

    else:
        return [
            "How did total revenue change recently?",
            "Which region performed best?",
            "Which product performed best?"
        ]
# -----------------------------
# ✅ STEP 2: SNOWFLAKE ANALYTICS (FIXED: QUARTER-AWARE)
# -----------------------------
def run_snowflake_analytics():

    revenue_sql = """
        SELECT QUARTER,
               SUM(REVENUE) AS TOTAL_REVENUE
        FROM EDW_2_DB.REASONING.REVENUE_TABLE
        GROUP BY QUARTER
        ORDER BY QUARTER;
    """

    revenue_df = session.sql(revenue_sql).to_pandas()

    # ✅ Dynamically detect LAST and PREVIOUS quarters
    last_q = revenue_df.iloc[-1]["QUARTER"]
    prev_q = revenue_df.iloc[-2]["QUARTER"]

    # ✅ Region for LAST quarter only
    region_sql = f"""
        SELECT REGION,
               SUM(REVENUE) AS TOTAL_REVENUE
        FROM EDW_2_DB.REASONING.REVENUE_TABLE
        WHERE QUARTER = '{last_q}'
        GROUP BY REGION
        ORDER BY TOTAL_REVENUE DESC;
    """

    # ✅ Product for LAST quarter only
    product_sql = f"""
        SELECT PRODUCT,
               SUM(REVENUE) AS TOTAL_REVENUE
        FROM EDW_2_DB.REASONING.REVENUE_TABLE
        WHERE QUARTER = '{last_q}'
        GROUP BY PRODUCT
        ORDER BY TOTAL_REVENUE DESC;
    """

    region_df = session.sql(region_sql).to_pandas()
    product_df = session.sql(product_sql).to_pandas()

    return revenue_df, region_df, product_df, last_q, prev_q

# -----------------------------
# ✅ STEP 3: CORTEX REASONING (FIXED: QUESTION-AWARE)
# -----------------------------
def cortex_reasoning(revenue_df, region_df, product_df, last_q, prev_q, question):

    last_rev = revenue_df.iloc[-1]["TOTAL_REVENUE"]
    prev_rev = revenue_df.iloc[-2]["TOTAL_REVENUE"]

    revenue_change = last_rev - prev_rev

    top_region = region_df.iloc[0]["REGION"]
    top_region_value = region_df.iloc[0]["TOTAL_REVENUE"]

    top_product = product_df.iloc[0]["PRODUCT"]
    top_product_value = product_df.iloc[0]["TOTAL_REVENUE"]

    cortex_prompt = f"""
User Question:
{question}

Business Evidence:
- Revenue in {prev_q}: {prev_rev}
- Revenue in {last_q}: {last_rev}
- Revenue Change: {revenue_change}
- Top Region in {last_q}: {top_region} ({top_region_value})
- Top Product in {last_q}: {top_product} ({top_product_value})

Instructions:
Write a clean, concise executive explanation.
Use short professional paragraphs.
No bullet points.
No section titles.
No recommendations.
Explain only what happened and why.
"""

    cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-70b',
            '{cortex_prompt}'
        );
    """

    result = session.sql(cortex_sql).collect()[0][0]
    return result

# -----------------------------
# ✅ MAIN EXECUTION
# -----------------------------
if run and question:

    # STEP 1
    st.subheader("🧩 Step 1 — Generated Sub-Questions")

    sub_qs = generate_subquestions(question)

    with st.expander("Click to view generated sub-questions"):
        for q in sub_qs:
            st.markdown(f"- {q}")

    # STEP 2
    st.subheader("📊 Step 2 — Snowflake Analytics")

    revenue_df, region_df, product_df, last_q, prev_q = run_snowflake_analytics()

    st.success("Revenue data successfully analyzed.")

    # STEP 3
    st.subheader("🤖 Step 3 — AI Reasoning (Cortex)")

    final_answer = cortex_reasoning(
        revenue_df, region_df, product_df, last_q, prev_q, question
    )

    st.subheader("✅ Final AI Explanation")

    # ✅ CLEAN PROFESSIONAL DISPLAY
    st.markdown(
        f"""
<div style="background-color:#eaf6ea;padding:20px;border-radius:8px;font-size:16px;line-height:1.6;">
{final_answer}
</div>
""",
        unsafe_allow_html=True
    )

    st.markdown("---")
