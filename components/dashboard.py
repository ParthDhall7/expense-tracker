"""Dashboard page: metric cards, charts and recent transactions."""

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db

NAVY, GREEN, RED = "#1B2A49", "#2E9E6B", "#D64545"


def metric_card(label, value, color=NAVY):
    """Draw one white metric card (styled by the CSS in app.py)."""
    st.markdown(
        f'<div class="card"><div class="card-label">{label}</div>'
        f'<div class="card-value" style="color:{color}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def money(value):
    return f"₹{value:,.2f}"


def transactions_table(rows):
    """Show transactions as a tidy table (used by several pages)."""
    df = pd.DataFrame(rows, columns=["id", "date", "transaction_type", "category",
                                     "description", "amount"])
    df.columns = ["ID", "Date", "Type", "Category", "Description", "Amount"]
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f")})


def render():
    st.title("Dashboard")
    totals = db.get_totals()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Income", money(totals["income"]), GREEN)
    with c2:
        metric_card("Total Expenses", money(totals["expenses"]), RED)
    with c3:
        metric_card("Current Balance", money(totals["balance"]),
                    GREEN if totals["balance"] >= 0 else RED)
    with c4:
        metric_card("Transactions", str(totals["count"]))

    if totals["count"] == 0:
        st.info("No transactions yet. Use **Add Transaction** in the sidebar to get started.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Expenses by Category")
        by_cat = db.get_expenses_by_category()
        if by_cat:
            df = pd.DataFrame(by_cat, columns=["Category", "Amount"])
            fig = px.pie(df, names="Category", values="Amount", hole=0.4)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No expenses recorded yet.")

    with right:
        st.subheader("Monthly Income vs Expenses")
        monthly = pd.DataFrame(db.get_monthly_totals())
        long = monthly.melt(id_vars="month", value_vars=["income", "expenses"],
                            var_name="Type", value_name="Amount")
        long["Type"] = long["Type"].str.capitalize()
        fig = px.bar(long, x="month", y="Amount", color="Type", barmode="group",
                     color_discrete_map={"Income": GREEN, "Expenses": RED},
                     labels={"month": "Month"})
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Transactions")
    transactions_table(db.get_transactions(limit=10))
