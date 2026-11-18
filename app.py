"""Expense Tracker - entry point. Run with:  streamlit run app.py"""

import streamlit as st

import database as db
from components import analytics, dashboard, transactions

st.set_page_config(page_title="Expense Tracker", layout="wide")

db.init_db()

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; max-width: 1400px; }
    h1 { font-weight: 700; letter-spacing: -0.5px; }

    /* Metric cards */
    .card { background: #0F1420; border: 1px solid #1F2937; border-radius: 18px;
            padding: 22px 24px; margin-bottom: 16px; }
    .card-top { display: flex; justify-content: space-between; align-items: center; }
    .card-label { color: #D1D5DB; font-size: 0.95rem; }
    .badge { width: 34px; height: 34px; border-radius: 10px; display: flex;
             align-items: center; justify-content: center; font-weight: 700; }
    .card-value { font-size: 1.9rem; font-weight: 700; margin-top: 22px; }
    .card-sub { color: #9CA3AF; font-size: 0.8rem; margin-top: 2px; }
    .empty { text-align: center; color: #9CA3AF; padding: 36px 0 12px 0; }

    /* Chart / table containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #0F1420; border: 1px solid #1F2937 !important;
        border-radius: 18px; padding: 8px 10px; }

    /* Slim sidebar */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 240px; max-width: 240px; width: 240px;
        background: #0B0F19; border-right: 1px solid #1F2937; }
    .brand { display: flex; align-items: center; gap: 10px; padding-bottom: 14px;
             border-bottom: 1px solid #1F2937; margin-bottom: 14px; }
    .brand-icon { background: #4F7CFF; border-radius: 10px; width: 38px; height: 38px;
                  display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
    .brand-title { font-weight: 700; line-height: 1.1; }
    .brand-sub { color: #9CA3AF; font-size: 0.75rem; }
    .nav-label { color: #9CA3AF; font-size: 0.75rem; margin-bottom: 4px; }
    /* Hide the radio circles so the options look like menu items */
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 9px 12px; border-radius: 10px; width: 100%; cursor: pointer; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #111827; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #1A2234; }
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

st.sidebar.markdown(
    '<div class="brand"><div class="brand-icon">💰</div><div>'
    '<div class="brand-title">Expense Tracker</div>'
    '<div class="brand-sub">Finance Dashboard</div></div></div>'
    '<div class="nav-label">Navigation</div>',
    unsafe_allow_html=True,
)
page = st.sidebar.radio("Navigate", list(PAGES), key="nav", label_visibility="collapsed")

# Show any message left by the previous action (add / edit / delete).
if "flash" in st.session_state:
    kind, message = st.session_state.pop("flash")
    (st.success if kind == "success" else st.error)(message)

PAGES[page]()
