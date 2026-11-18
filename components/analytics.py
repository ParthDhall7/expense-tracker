"""Financial Summary page: totals and breakdowns for a selected period."""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from components.dashboard import GREEN, RED, metric_card, money, style_fig


def render():
    st.title("Financial Summary")

    c1, c2, c3 = st.columns([1, 1, 1])
    use_dates = c1.checkbox("Limit to a period (otherwise all time)")
    start = c2.date_input("From", value=date.today().replace(day=1), disabled=not use_dates)
    end = c3.date_input("To", value=date.today(), disabled=not use_dates)
    start, end = (start, end) if use_dates else (None, None)

    try:
        totals = db.get_totals(start, end)
        by_cat = db.get_expenses_by_category(start, end)
        monthly = db.get_monthly_totals(start, end)
    except ValueError as e:
        st.error(str(e))
        return

    if totals["count"] == 0:
        st.info("No transactions in this period.")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Total Income", money(totals["income"]), GREEN, icon="↗", tint=GREEN)
    with m2:
        metric_card("Total Expenses", money(totals["expenses"]), RED, icon="↘", tint=RED)
    with m3:
        metric_card("Net Savings", money(totals["balance"]),
                    GREEN if totals["balance"] >= 0 else RED)
    with m4:
        if by_cat:
            metric_card("Highest Spending", f"{by_cat[0][0]} ({money(by_cat[0][1])})")
        else:
            metric_card("Highest Spending", "—")

    st.subheader("Monthly Expense Breakdown")
    df = pd.DataFrame(monthly)
    if (df["expenses"] > 0).any():
        fig = px.bar(df, x="month", y="expenses", labels={"month": "Month", "expenses": "Expenses"},
                     color_discrete_sequence=[RED])
        st.plotly_chart(style_fig(fig), use_container_width=True)
    table = df.rename(columns={"month": "Month", "income": "Income", "expenses": "Expenses"})
    table["Net"] = table["Income"] - table["Expenses"]
    st.dataframe(table, use_container_width=True, hide_index=True,
                 column_config={c: st.column_config.NumberColumn(format="₹%.2f")
                                for c in ["Income", "Expenses", "Net"]})
