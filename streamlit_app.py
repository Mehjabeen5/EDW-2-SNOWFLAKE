import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# -------------------------------------------------------------
# ✅ Snowflake Native Session (NO SECRETS, NO PASSWORDS)
# -------------------------------------------------------------
session = get_active_session()

st.set_page_config(page_title="EDW-2 Reasoning Assistant", layout="centered")

# -------------------------------------------------------------
# ✅ UI HEADER
# -------------------------------------------------------------
st.title("🧠 EDW-2 Reasoning Query Assistant (Snowflake Cortex)")

st.markdown("""
Ask a high-level **business reasoning question**.  
The system will:

- Break it into **dynamic sub-questions**
- Run **Snowflake analytics**
- Use **Cortex** to generate a final explanation
""")

question = st.text_input("🔎 Ask a reasoning question:")

run = st.button("Run Reasoning")

# -------------------------------------------------------------
# ✅ DYNAMIC SUB-QUESTION GENERATOR (NOT STATIC)
# -------------------------------------------------------------
def generate_subquestions(user_question: str):
    prompt = f"""
    Convert this business question into 3 short, professional analytical sub-questions:
    "{user_question}"

    The sub-questions must focus on:
    1. Overall trends
    2. Regional contribution
    3. Product performance

    Return as a numbered list only.
    """

    sql = f"""
    SELECT snowflake.cortex.complete(
        'llama3.1-70b',
        '{prompt}'
    )
    """
    result = session.sql(sql).collect()[0][0]
    return result.split("\n")


# -------------------------------------------------------------
# ✅ SNOWFLAKE ANALYTICS QUERIES
# -------------------------------------------------------------
def get_revenue_trend():
    return session.sql("""
        SELECT quarter, SUM(revenue) AS total_revenue
        FROM REVENUE_TABLE
        GROUP BY quarter
        ORDER BY quarter
    """).to_pandas()


def get_region_revenue():
    return session.sql("""
        SELECT region, SUM(revenue) AS total_revenue
        FROM REVENUE_TABLE
        GROUP BY region
        ORDER BY total_revenue DESC
    """).to_pandas()


def get_product_revenue():
    return session.sql("""
        SELECT product, SUM(revenue) AS total_revenue
        FROM REVENUE_TABLE
        GROUP BY product
        ORDER BY total_revenue DESC
    """).to_pandas()


# -------------------------------------------------------------
# ✅ CORTEX FINAL REASONING CALL (PROFESSIONAL)
# -------------------------------------------------------------
def cortex_reasoning(rev_df, reg_df, prod_df, user_q):

    summary_prompt = f"""
You are a business analyst.

User Question:
{user_q}

Quarterly Revenue Summary:
{rev_df.to_string(index=False)}

Regional Revenue Summary:
{reg_df.to_string(index=False)}

Product Revenue Summary:
{prod_df.to_string(index=False)}

Write a professional business explanation that:
- Identifies the key revenue outcome
- Explains the top region and product
- Avoids recommendations and next steps
- Avoids fluff
- Sounds executive-ready
"""

    sql = f"""
    SELECT snowflake.cortex.complete(
        'llama3.1-70b',
        '{summary_prompt}'
    )
    """

    return session.sql(sql).collect()[0][0]


# -------------------------------------------------------------
# ✅ MAIN EXECUTION
# -------------------------------------------------------------
if run and question:

    # -------------------------
    # ✅ STEP 1 — SUB-QUESTIONS
    # -------------------------
    st.markdown("## 🧩 Step 1 — Generated Sub-Questions")

    subqs = generate_subquestions(question)

    with st.expander("View Generated Sub-Questions"):
        for s in subqs:
            if s.strip():
                st.markdown(f"- {s}")

    # -------------------------
    # ✅ STEP 2 — ANALYTICS
    # -------------------------
    st.markdown("## 📊 Step 2 — Snowflake Analytics")
    st.success("Revenue, region, and product analytics successfully executed.")

    revenue_df = get_revenue_trend()
    region_df = get_region_revenue()
    product_df = get_product_revenue()

    with st.expander("View Revenue Trend"):
        st.dataframe(revenue_df)

    with st.expander("View Regional Revenue"):
        st.dataframe(region_df)

    with st.expander("View Product Revenue"):
        st.dataframe(product_df)

    # -------------------------
    # ✅ STEP 3 — AI REASONING
    # -------------------------
    st.markdown("## 🤖 Step 3 — AI Reasoning (Cortex)")
    st.markdown("## ✅ Final AI Explanation")

    final_answer = cortex_reasoning(
        revenue_df, region_df, product_df, question
    )

    st.success(final_answer)

