import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(page_title="EDW-2 Snowflake Cortex Demo", layout="wide")

st.title("📊 EDW-2 Revenue Decline Analysis (Snowflake Cortex Style)")

st.markdown("""
This dashboard answers the business question:

> **Why was revenue down last quarter?**

using Snowflake-native analytics (CTE-based semantic modeling).
""")

# ✅ Snowflake Native Connection
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="COMPUTE_WH",
    database="USERS$MSHAIK05",
    schema="PUBLIC"
)

query = """
WITH T (QUARTER, REGION, PRODUCT, REVENUE, COST) AS (
    SELECT * FROM VALUES
        ('2024-Q1', 'East',  'Product A', 120000,  90000),
        ('2024-Q1', 'West',  'Product B', 150000, 130000),
        ('2024-Q2', 'East',  'Product A',  95000,  88000),
        ('2024-Q2', 'West',  'Product B', 110000, 120000),
        ('2024-Q3', 'East',  'Product A',  70000,  85000),
        ('2024-Q3', 'West',  'Product B', 130000, 115000),
        ('2024-Q4', 'East',  'Product A', 160000, 100000),
        ('2024-Q4', 'West',  'Product B', 140000, 120000)
)
SELECT 
    QUARTER,
    SUM(REVENUE) AS TOTAL_REVENUE,
    SUM(COST) AS TOTAL_COST,
    SUM(REVENUE - COST) AS TOTAL_PROFIT
FROM T
GROUP BY QUARTER
ORDER BY QUARTER;
"""

df = pd.read_sql(query, conn)

st.subheader("✅ Quarterly Performance Table")
st.dataframe(df, use_container_width=True)

st.subheader("📉 Revenue Trend")
st.line_chart(df.set_index("QUARTER")[["TOTAL_REVENUE"]])

st.subheader("💰 Profit Trend")
st.bar_chart(df.set_index("QUARTER")[["TOTAL_PROFIT"]])

st.markdown("---")
st.success("""
🔑 **Final Insight**  
Revenue dropped in **Q3** due to **East–Product A underperforming while costs stayed high**.
""")
