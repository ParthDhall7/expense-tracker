"""Transaction pages: add, view (with filters), edit and delete."""

from datetime import date

import streamlit as st

import database as db
from components.dashboard import transactions_table


def _categories_for(transaction_type):
    return db.EXPENSE_CATEGORIES if transaction_type == "Expense" else db.INCOME_CATEGORIES


def flash(kind, message):
    """Store a message that survives st.rerun() so it shows on the next run."""
    st.session_state["flash"] = (kind, message)


# ------------------------------------------------------------------ add
def render_add():
    st.title("Add Transaction")

    # The type selector sits OUTSIDE the form so the category list updates instantly.
    t_type = st.radio("Transaction Type", db.TRANSACTION_TYPES, horizontal=True, key="add_type")

    with st.form("add_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        category = st.selectbox("Category", _categories_for(t_type))
        description = st.text_input("Description")
        t_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("Save Transaction")

    if submitted:
        try:
            new_id = db.add_transaction(t_type, amount, category, description, t_date)
            flash("success", f"Transaction #{new_id} saved successfully.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
        except Exception:
            st.error("Something went wrong while saving. Please try again.")


# ------------------------------------------------------------------ view
def render_view():
    st.title("View Transactions")

    c1, c2 = st.columns(2)
    f_type = c1.selectbox("Type", ["All"] + db.TRANSACTION_TYPES)
    if f_type == "Income":
        cats = db.INCOME_CATEGORIES
    elif f_type == "Expense":
        cats = db.EXPENSE_CATEGORIES
    else:
        cats = sorted(set(db.EXPENSE_CATEGORIES + db.INCOME_CATEGORIES))
    f_cat = c2.selectbox("Category", ["All"] + cats)

    c3, c4, c5 = st.columns(3)
    use_dates = c3.checkbox("Filter by date range")
    start = c4.date_input("From", value=date.today().replace(day=1), disabled=not use_dates)
    end = c5.date_input("To", value=date.today(), disabled=not use_dates)
    search = st.text_input("Search description")

    try:
        rows = db.get_transactions(
            f_type, f_cat,
            start if use_dates else None, end if use_dates else None, search,
        )
    except ValueError as e:
        st.error(str(e))
        return

    st.caption(f"{len(rows)} transaction(s) found")
    if rows:
        transactions_table(rows)
    else:
        st.info("No transactions match these filters.")


# ------------------------------------------------------------------ edit / delete
def _label(t):
    return f"#{t['id']} | {t['date']} | {t['transaction_type']} | {t['category']} | ₹{t['amount']:,.2f}"


def render_manage():
    st.title("Edit / Delete Transaction")
    rows = db.get_transactions()
    if not rows:
        st.info("There are no transactions to edit or delete.")
        return

    labels = {_label(t): t["id"] for t in rows}
    chosen = st.selectbox("Select a transaction", list(labels))
    t = db.get_transaction(labels[chosen])
    if t is None:  # e.g. deleted in another browser tab
        st.error("That transaction no longer exists.")
        return

    tab_edit, tab_delete = st.tabs(["Edit", "Delete"])

    with tab_edit:
        types = db.TRANSACTION_TYPES
        # Type is outside the form so the category list follows it.
        e_type = st.radio("Transaction Type", types, index=types.index(t["transaction_type"]),
                          horizontal=True, key=f"edit_type_{t['id']}")
        cats = _categories_for(e_type)
        with st.form(f"edit_form_{t['id']}"):
            e_amount = st.number_input("Amount (₹)", min_value=0.0, value=float(t["amount"]),
                                       step=10.0, format="%.2f")
            e_cat = st.selectbox("Category", cats,
                                 index=cats.index(t["category"]) if t["category"] in cats else 0)
            e_desc = st.text_input("Description", value=t["description"] or "")
            e_date = st.date_input("Date", value=date.fromisoformat(t["date"]))
            if st.form_submit_button("Update Transaction"):
                try:
                    db.update_transaction(t["id"], e_type, e_amount, e_cat, e_desc, e_date)
                    flash("success", f"Transaction #{t['id']} updated.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with tab_delete:
        st.warning(f"You are about to delete: {_label(t)}")
        confirm_key = f"confirm_delete_{t['id']}"
        if not st.session_state.get(confirm_key):
            if st.button("Delete this transaction"):
                st.session_state[confirm_key] = True
                st.rerun()
        else:
            st.error("Are you sure? This cannot be undone.")
            yes, no = st.columns(2)
            if yes.button("Yes, delete it"):
                try:
                    db.delete_transaction(t["id"])
                    flash("success", f"Transaction #{t['id']} deleted.")
                except ValueError as e:
                    flash("error", str(e))
                st.session_state.pop(confirm_key, None)
                st.rerun()
            if no.button("Cancel"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
