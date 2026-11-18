"""Expense Tracker - entry point. Run with:  streamlit run app.py"""

import streamlit as st

import database as db
from components import analytics, dashboard, transactions

st.set_page_config(page_title="Expense Tracker", layout="wide")

# Create the database and table on first run (safe to call every time).
db.init_db()

# Simple styling: neutral background, white cards, navy headings.
st.markdown(
    """
    <style>
    .stApp { background-color: #F4F6FA; color: #1B2A49; }
    h1, h2, h3, label, p { color: #1B2A49; }
    /* Slimmer, cleaner sidebar */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 220px; max-width: 220px; width: 220px;
        background-color: #FFFFFF; border-right: 1px solid #E3E7EF;
    }
    [data-testid="stSidebar"] h1 { font-size: 1.3rem; }
    [data-testid="stSidebar"] label p { font-size: 0.95rem; }
    .card { background: #FFFFFF; border-radius: 10px; padding: 18px 20px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 12px; }
    .card-label { color: #6B7280; font-size: 0.85rem; }
    .card-value { font-size: 1.5rem; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "Dashboard": dashboard.render,
    "Add Transaction": transactions.render_add,
    "View Transactions": transactions.render_view,
    "Edit / Delete": transactions.render_manage,
    "Financial Summary": analytics.render,
}

st.sidebar.title("Expense Tracker")
page = st.sidebar.radio("Navigate", list(PAGES), label_visibility="collapsed")

# Show any message left by the previous action (add / edit / delete).
if "flash" in st.session_state:
    kind, message = st.session_state.pop("flash")
    (st.success if kind == "success" else st.error)(message)

PAGES[page]()
