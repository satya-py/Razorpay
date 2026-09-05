"""
AutoCart — Agentic Checkout & Payment Recovery Assistant
Razorpay AI Builder Internship 2026 — Track 1: AI Growth & Agentic Commerce

Run locally with:
    streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

from modules.intent_parser import parse_intent
from modules.decision_engine import evaluate
from modules.razorpay_client import get_client, create_payment_link

load_dotenv()

st.set_page_config(page_title="AutoCart", page_icon="🛒", layout="centered")

# ---------- Session state ----------
if "recent_transactions" not in st.session_state:
    st.session_state.recent_transactions = []
if "pending_task" not in st.session_state:
    st.session_state.pending_task = None
if "decision" not in st.session_state:
    st.session_state.decision = None

# ---------- Sidebar: settings ----------
st.sidebar.header("⚙️ Settings")

openai_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", "")
)
razorpay_key_id = st.sidebar.text_input(
    "Razorpay Test Key ID", value=os.getenv("RAZORPAY_KEY_ID", "")
)
razorpay_key_secret = st.sidebar.text_input(
    "Razorpay Test Key Secret", type="password", value=os.getenv("RAZORPAY_KEY_SECRET", "")
)
budget_limit = st.sidebar.number_input(
    "Budget limit per transaction (₹)", min_value=100, value=2000, step=100
)
customer_name = st.sidebar.text_input("Customer name (for payment link)", value="Test User")
customer_email = st.sidebar.text_input("Customer email (for payment link)", value="test@example.com")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Keys are only used in this session and never stored. "
    "Get Razorpay test keys from Dashboard → Settings → API Keys."
)

# ---------- Main UI ----------
st.title("🛒 AutoCart")
st.caption("An agentic checkout assistant — Razorpay AI Builder Internship 2026")

st.markdown(
    "Describe what you want done in plain English, e.g. "
    "*\"reorder my office supplies under 2000 rupees\"* or "
    "*\"renew my design tool subscription\"*."
)

user_input = st.text_input("What would you like AutoCart to do?", key="user_input")

col1, col2 = st.columns([1, 1])
run_clicked = col1.button("🧠 Process Request", use_container_width=True)
reset_clicked = col2.button("🔄 Reset", use_container_width=True)

if reset_clicked:
    st.session_state.pending_task = None
    st.session_state.decision = None
    st.rerun()

# ---------- Step 1 + 2: Parse intent, run decision engine ----------
if run_clicked:
    if not user_input.strip():
        st.warning("Please describe what you'd like AutoCart to do.")
    elif not openai_key:
        st.error("OpenAI API key is required for intent parsing. Add it in the sidebar.")
    else:
        with st.spinner("Parsing your request..."):
            try:
                task = parse_intent(user_input, openai_key)
            except Exception as e:
                st.error(f"Intent parsing failed: {e}")
                task = None

        if task:
            decision = evaluate(task, budget_limit, st.session_state.recent_transactions)
            st.session_state.pending_task = task
            st.session_state.decision = decision

# ---------- Step 3: Show reasoning trail + approval gate ----------
if st.session_state.decision:
    decision = st.session_state.decision
    task = st.session_state.pending_task

    st.subheader("🧩 Structured Task")
    st.json(task)

    st.subheader("📋 Agent Reasoning Trail")
    for line in decision["reasoning"]:
        st.write(line)

    if decision["approved_by_rules"]:
        st.success("Decision engine approved this transaction. Awaiting your final approval.")

        if st.button("✅ Approve & Pay via Razorpay", type="primary"):
            if not razorpay_key_id or not razorpay_key_secret:
                st.error("Razorpay test Key ID and Secret are required. Add them in the sidebar.")
            else:
                with st.spinner("Creating Razorpay payment link..."):
                    try:
                        client = get_client(razorpay_key_id, razorpay_key_secret)
                        link = create_payment_link(client, task, customer_name, customer_email)

                        st.session_state.recent_transactions.append({
                            "item": task.get("item", "unknown"),
                            "amount": task.get("max_amount", 0),
                            "timestamp": link.get("created_at"),
                        })

                        st.success("Payment link created successfully ✅")
                        st.markdown(f"**Pay here:** {link['short_url']}")
                        st.json(link)

                        st.session_state.pending_task = None
                        st.session_state.decision = None
                    except Exception as e:
                        st.error(f"Razorpay error: {e}")
    else:
        st.error("Decision engine blocked this transaction. See reasoning above.")

# ---------- Dashboard: transaction history ----------
st.markdown("---")
st.subheader("📊 Transaction History (this session)")
if st.session_state.recent_transactions:
    st.table(st.session_state.recent_transactions)
else:
    st.caption("No transactions yet.")
