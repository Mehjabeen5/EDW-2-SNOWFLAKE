import streamlit as st
import snowflake.connector
import pandas as pd
import openai
import re

# ---------------------------
# CONFIG
# ---------------------------

SNOWFLAKE_CONFIG = {
    "account": "rla87684",
    "user": "MSHAIK05",
    "password": "YOUR_SNOWFLAKE_PASSWORD",
    "warehouse": "COMPUTE_WH",
    "database": "EDW_2_DB",
    "schema": "PUBLIC",
    "role": "ACCOUNTADMIN"
}

openai.api_key = "YOUR_OPENAI_KEY"   # later you can swap for Cortex

# ---------------------------
# DATABASE CONNECTION
# ---------------------------

def get_snowflake_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

# ---------------------------
# QUERY FUNCTIONS
# ---------------------------

def get_profit_trend():
    conn = get_snowflake_connection()
    df = pd.read_sql("SELECT * FROM PROFIT_TREND ORDER BY QUARTER;", conn)
    conn.close()
    return df

def get_region_trend():
    conn = get_snowflake_connection()
    df = pd.read_sql("""
        SELECT REGION, SUM(REVENUE) AS TOTAL_REVENUE 
        FROM REVENUE_DATA 
        GROUP BY REGION;
    """, conn)
    conn.close()
    return df

def get_product_trend():
    conn = get_snowflake_connection()
    df = pd.read_sql("""
        SELECT PRODUCT, SUM(REVENUE) AS TOTAL_REVENUE 
        FROM REVENUE_DATA 
        GROUP BY PRODUCT;
    """, conn)
    conn.close()
    return df

# ---------------------------
# REASONING DETECTOR
# ---------------------------

def is_reasoning_question(question):
    keywords = ["why", "reason", "cause", "drop", "decline", "low"]
    return any(word in question.lower() for word in keywords)

# ---------------------------
# SUB-QUESTION GENERATOR
# ---------------------------

def generate_sub_questions(question):
    return [
        "Analyze profit trend by quarter",
        "Analyze revenue by region",
        "Analyze revenue by product"
    ]

# ---------------------------
# LLM SUMMARIZER (OpenAI now → Cortex later)
# ---------------------------

def summarize_results(question, profit_df, region_df, product_df):

    prompt = f"""
User Question: {question}

Profit Trend:
{profit_df.to_string(index=False)}

Region Trend:
{region_df.to_string(index=False)}

Product Trend:
{product_df.to_string(index=False)}

Generate a business explanation in simple language.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response["choices"][0]["message"]["content"]

# ---------------------------
# STREAMLIT UI
# ---------------------------

st.set_page_config(page_title="EDW-2 Reasoning Assistant", layout="wide")

st.title("📊 EDW-2 Reasoning Analytics Assistant")

question = st.text_input("Ask a business question:")

if st.button("Analyze"):

    if not question:
        st.warning("Please enter a question.")
    
    elif is_reasoning_question(question):

        st.subheader("🧠 Reasoning Mode Detected")

        sub_questions = generate_sub_questions(question)

        st.write("Generated Sub-Questions:")
        for q in sub_questions:
            st.markdown(f"- {q}")

        profit_df = get_profit_trend()
        region_df = get_region_trend()
        product_df = get_product_trend()

        st.subheader("📈 Profit Trend")
        st.dataframe(profit_df)

        st.subheader("🌍 Revenue by Region")
        st.dataframe(region_df)

        st.subheader("📦 Revenue by Product")
        st.dataframe(product_df)

        st.subheader("📝 AI Explanation")
        final_answer = summarize_results(question, profit_df, region_df, product_df)
        st.success(final_answer)

    else:
        st.subheader("📄 Simple Data Query Mode")
        st.info("Non-reasoning SQL queries will be handled here later.")
