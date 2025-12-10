import streamlit as st
import pandas as pd
import json

from snowflake.snowpark.context import get_active_session

# -----------------------------------------------------------
# Snowflake session
# -----------------------------------------------------------
session = get_active_session()

st.set_page_config(page_title="EDW-2 Reasoning Assistant", layout="wide")
st.title("EDW-2 Reasoning Assistant (Snowflake Native)")

# -----------------------------------------------------------
# Helper: call Cortex COMPLETE safely
# -----------------------------------------------------------

def cortex_complete(prompt: str, model: str = "snowflake-arctic") -> str:
    """
    Call SNOWFLAKE.CORTEX.COMPLETE with the given prompt.

    We manually escape single quotes so the prompt is safe as a SQL literal.
    """
    # Escape single quotes for SQL: ' → ''
    safe_prompt = prompt.replace("'", "''")

    query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{safe_prompt}'
        )
    """

    return session.sql(query).collect()[0][0]

# -----------------------------------------------------------
# Helper: fetch analytics views
# -----------------------------------------------------------

def fetch_views():
    """
    Pull analytics from EDW_2_DB.REASONING.

    Assumes:
      - EDW_2_DB.REASONING.REVENUE_TABLE exists
      - V_REVENUE_BY_QUARTER / REGION / PRODUCT exist in that schema
    """
    rev = session.sql("""
        SELECT *
        FROM EDW_2_DB.REASONING.V_REVENUE_BY_QUARTER
        ORDER BY QUARTER
    """).to_pandas()

    reg = session.sql("""
        SELECT *
        FROM EDW_2_DB.REASONING.V_REVENUE_BY_REGION
        ORDER BY QUARTER, REGION
    """).to_pandas()

    prod = session.sql("""
        SELECT *
        FROM EDW_2_DB.REASONING.V_REVENUE_BY_PRODUCT
        ORDER BY QUARTER, PRODUCT
    """).to_pandas()

    return rev, reg, prod


# -----------------------------------------------------------
# Helper: route question → simple vs reasoning
# -----------------------------------------------------------

def classify_question(q: str) -> str:
    """
    Very simple heuristic router.

    - "reasoning"  => why / explanation / cause
    - "simple"     => everything else
    """
    lower = (q or "").lower()
    reasoning_keywords = ["why", "cause", "reason", "driver", "explain", "because"]

    if any(k in lower for k in reasoning_keywords):
        return "reasoning"

    # default: treat as a simple fact / metric question
    return "simple"


# -----------------------------------------------------------
# Planning: build a small multi-step plan for reasoning mode
# -----------------------------------------------------------

def plan_steps(question: str) -> dict:
    """
    Build a (deterministic) multi-step plan for reasoning questions.

    You can later swap this to a Cortex-generated JSON plan if you like.
    """
    steps = [
        {
            "id": "s1",
            "type": "quarter",
            "description": "Compare total revenue between the last two quarters."
        },
        {
            "id": "s2",
            "type": "region",
            "description": "Identify which region had the largest negative change in revenue."
        },
        {
            "id": "s3",
            "type": "product",
            "description": "Identify which product had the weakest performance in the last quarter."
        },
        {
            "id": "s4",
            "type": "synthesis",
            "description": "Combine quarter, region, and product insights to explain the revenue change."
        }
    ]

    return {
        "question": question,
        "steps": steps
    }


# -----------------------------------------------------------
# Evidence builder: summarize analytics into JSON
# -----------------------------------------------------------

def execute_plan(plan: dict, rev: pd.DataFrame, reg: pd.DataFrame, prod: pd.DataFrame) -> dict:
    """
    For now, just package the three analytics views into a JSON-friendly
    evidence structure. The plan is kept for context.
    """
    evidence = {
        "by_quarter": rev.to_dict(orient="records"),
        "by_region": reg.to_dict(orient="records"),
        "by_product": prod.to_dict(orient="records"),
    }
    return evidence


# -----------------------------------------------------------
# Simple path: no planning, just analytics + one Cortex call
# -----------------------------------------------------------

def simple_answer(question: str, rev: pd.DataFrame, reg: pd.DataFrame, prod: pd.DataFrame) -> str:
    """
    Simple path:

    - Use analytics views
    - Build an evidence blob
    - Ask Cortex for a short, direct answer
    """
    dummy_plan = {"steps": []}
    evidence = execute_plan(dummy_plan, rev, reg, prod)
    evidence_json = json.dumps(evidence, default=str)

    prompt = f"""
You are a business data assistant answering straightforward questions.

User question:
{question}

You are given precomputed analytics as JSON:
{evidence_json}

Instructions:
- If the user asks for a specific value (e.g., revenue for a quarter or product),
  answer with that number and one short explanatory sentence.
- Do NOT describe your internal reasoning steps.
- Do NOT list a multi-step plan.
- Base your answer only on the data provided.
"""
    return cortex_complete(prompt)


# -----------------------------------------------------------
# Reasoning path: plan → execute → synthesize
# -----------------------------------------------------------

def synthesize_answer(question: str, plan: dict, evidence: dict) -> str:
    """
    Full reasoning path: include the plan and evidence in the prompt
    and ask Cortex for a multi-sentence explanation.
    """
    plan_json = json.dumps(plan, default=str)
    evidence_json = json.dumps(evidence, default=str)

    prompt = f"""
You are a senior business analyst.

User question:
{question}

Planned steps (JSON):
{plan_json}

Summarized evidence from analytics (JSON):
{evidence_json}

Write a professional, concise explanation that:
- Describes what happened (trends by quarter / region / product).
- Highlights the main drivers of the revenue change.
- Uses only the information in the evidence; do not hallucinate extra data.
- Avoids bullet points; answer in 1–3 paragraphs of plain text.
"""
    return cortex_complete(prompt)


# -----------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------

question = st.text_input("Ask a business question (e.g., 'Why was revenue down last quarter?')")
run = st.button("Run Analysis")

if run and question:
    # 1) Routing
    route = classify_question(question)
    st.subheader("Step 1 — Routing")
    st.markdown(f"**Route:** `{route}`")

    # ---------------------------------------
    # SIMPLE PATH: no planning
    # ---------------------------------------
    if route == "simple":
        st.markdown("_Simple question detected: skipping explicit planning and using direct analytics._")

        # 2) Analytics
        st.subheader("Step 2 — Snowflake Analytics")
        rev, reg, prod = fetch_views()
        st.success("Analytics successfully generated from Snowflake.")

        with st.expander("Preview: Revenue by Quarter"):
            st.dataframe(rev)
        with st.expander("Preview: Revenue by Region"):
            st.dataframe(reg)
        with st.expander("Preview: Revenue by Product"):
            st.dataframe(prod)

        # 3) Direct answer
        st.subheader("Step 3 — Direct AI Answer (no planning)")
        final_answer = simple_answer(question, rev, reg, prod)

        st.subheader("Final AI Explanation")
        st.markdown(
            f"""
<div style="background-color:#ecf7ee;padding:20px;border-radius:8px;font-size:16px;line-height:1.6;">
{final_answer}
</div>
""",
            unsafe_allow_html=True,
        )

    # ---------------------------------------
    # REASONING PATH: multi-step plan
    # ---------------------------------------
    else:
        st.markdown("_Reasoning question detected: using planning + multi-step reasoning._")

        # 2) Planning
        st.subheader("Step 2 — Planning")
        plan = plan_steps(question)
        steps = plan.get("steps", [])

        if steps:
            st.markdown("**Planned Steps:**")
            for s in steps:
                st.markdown(
                    f"- `{s.get('id', '')}` "
                    f"[{s.get('type', '')}] – {s.get('description', '')}"
                )
        else:
            st.markdown("_No steps returned; using default analytics plan._")

        # 3) Analytics
        st.subheader("Step 3 — Snowflake Analytics")
        rev, reg, prod = fetch_views()
        st.success("Analytics successfully generated from Snowflake.")

        with st.expander("Preview: Revenue by Quarter"):
            st.dataframe(rev)
        with st.expander("Preview: Revenue by Region"):
            st.dataframe(reg)
        with st.expander("Preview: Revenue by Product"):
            st.dataframe(prod)

        # Execute plan → build evidence
        evidence = execute_plan(plan, rev, reg, prod)

        # 4) Reasoning / synthesis
        st.subheader("Step 4 — AI Reasoning (Cortex)")
        final_answer = synthesize_answer(question, plan, evidence)

        st.subheader("Final AI Explanation")
        st.markdown(
            f"""
<div style="background-color:#ecf7ee;padding:20px;border-radius:8px;font-size:16px;line-height:1.6;">
{final_answer}
</div>
""",
            unsafe_allow_html=True,
        )

        # Optional debugging info
        with st.expander("Debug: Plan & Evidence JSON"):
            st.json({"plan": plan, "evidence": evidence})