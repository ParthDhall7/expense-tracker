"""Dashboard page: metric cards, charts and recent transactions."""

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db

GREEN, RED, BLUE = "#22C55E", "#F43F5E", "#4F7CFF"
TEXT, MUTED = "#F3F4F6", "#9CA3AF"


def money(value):
    return f"₹{value:,.2f}"


def metric_card(label, value, color=TEXT, subtitle="", icon="", tint=BLUE):
    """Draw one rounded metric card with a small coloured icon badge (CSS lives in app.py)."""
    st.markdown(
        f'<div class="card">'
        f'<div class="card-top"><span class="card-label">{label}</span>'
        f'<span class="badge" style="background:{tint}26;color:{tint}">{icon}</span></div>'
        f'<div class="card-value" style="color:{color}">{value}</div>'
        f'<div class="card-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def go_to(page):
    """Button callback: switch the sidebar to another page."""
    st.session_state["nav"] = page


def empty_state(message):
    """Centered 'nothing here yet' message with a button that opens Add Transaction."""
    st.markdown(f'<div class="empty">{message}</div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    # mid.button("Add Transaction", key=f"empty_{abs(hash(message))}_{id(message)}",
    #            on_click=go_to, args=("Add Transaction",), type="primary",
    #            use_container_width=True)


def style_fig(fig, height=320):
    """Make Plotly charts blend into the dark cards."""
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=height,
                      margin=dict(t=10, b=10, l=10, r=10),
                      legend=dict(orientation="h", y=-0.15))
    return fig


def transactions_table(rows):
    """Show transactions as a tidy table (used by several pages)."""
    df = pd.DataFrame(rows, columns=["id", "date", "transaction_type", "category",
                                     "description", "amount"])
    df.columns = ["ID", "Date", "Type", "Category", "Description", "Amount"]
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f")})


def render():
    st.title("Expense Tracker Dashboard")
    st.caption("Track your personal finances with live insights")
    totals = db.get_totals()

    savings_rate = (totals["balance"] / totals["income"] * 100) if totals["income"] > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Income", money(totals["income"]), subtitle="All time earnings",
                    icon="↗", tint=GREEN)
    with c2:
        metric_card("Total Expenses", money(totals["expenses"]), subtitle="All time spending",
                    icon="↘", tint=RED)
    with c3:
        metric_card("Current Balance", money(totals["balance"]),
                    color=GREEN if totals["balance"] >= 0 else RED,
                    subtitle="Income minus expenses", icon="₹", tint=BLUE)
    with c4:
        metric_card("Transactions", str(totals["count"]),
                    subtitle=f"Savings rate {savings_rate:.1f}%", icon="#", tint="#A78BFA")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Spending by Category")
            st.caption("Where your money goes")
            by_cat = db.get_expenses_by_category()
            if by_cat:
                df = pd.DataFrame(by_cat, columns=["Category", "Amount"])
                fig = px.pie(df, names="Category", values="Amount", hole=0.55,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                empty_state("Add some expenses to see your spending breakdown.")

    with right:
        with st.container(border=True):
            st.subheader("Monthly Income vs Expenses")
            st.caption("How each month compares")
            monthly = pd.DataFrame(db.get_monthly_totals())
            if not monthly.empty:
                long = monthly.melt(id_vars="month", value_vars=["income", "expenses"],
                                    var_name="Type", value_name="Amount")
                long["Type"] = long["Type"].str.capitalize()
                fig = px.bar(long, x="month", y="Amount", color="Type", barmode="group",
                             color_discrete_map={"Income": GREEN, "Expenses": RED},
                             labels={"month": "Month"})
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                empty_state("Add income and expenses to generate your insights.")

    with st.container(border=True):
        st.subheader("Recent Transactions")
        st.caption("Your latest financial activity")
        rows = db.get_transactions(limit=10)
        if rows:
            transactions_table(rows)
        else:
            empty_state("No transactions yet.")
