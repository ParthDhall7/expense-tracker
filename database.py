"""Database layer for the Expense Tracker.

All SQLite work lives here so the UI code never touches SQL directly.
Every query is parameterized (the ? placeholders), which prevents SQL injection.
Every function accepts an optional `db_path` so tests can use a temporary
database instead of the real expenses.db.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

# expenses.db is created next to this file, no matter where the app is launched from.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

EXPENSE_CATEGORIES = [
    "Food", "Travel", "Shopping", "Entertainment",
    "Education", "Healthcare", "Bills", "Others",
]
INCOME_CATEGORIES = ["Salary", "Freelancing", "Investments", "Allowance", "Others"]
TRANSACTION_TYPES = ["Income", "Expense"]


@contextmanager
def get_connection(db_path=None):
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dictionaries
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """Create the transactions table if it does not exist yet."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                amount           REAL NOT NULL,
                category         TEXT NOT NULL,
                description      TEXT,
                date             TEXT NOT NULL,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ---------------------------------------------------------------- validation
def _to_date_string(value):
    """Turn a date object or 'YYYY-MM-DD' string into 'YYYY-MM-DD'. Raise ValueError if invalid."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass
    raise ValueError("Invalid date. Use the format YYYY-MM-DD.")


def validate_transaction(transaction_type, amount, category, description, date_value):
    """Check the inputs and return cleaned values (type, amount, category, description, date).

    Raises ValueError with a user-friendly message if anything is wrong.
    """
    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError("Transaction type must be Income or Expense.")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.")
    if amount != amount or amount in (float("inf"), float("-inf")):  # NaN / infinity
        raise ValueError("Amount must be a valid number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    valid_categories = EXPENSE_CATEGORIES if transaction_type == "Expense" else INCOME_CATEGORIES
    if not category or not str(category).strip():
        raise ValueError("Category is required.")
    if category not in valid_categories:
        raise ValueError(f"'{category}' is not a valid {transaction_type.lower()} category.")

    description = (description or "").strip()
    return transaction_type, round(amount, 2), category, description, _to_date_string(date_value)


def validate_date_range(start, end):
    """Return (start, end) as strings (None allowed). Raise ValueError if start is after end."""
    start = _to_date_string(start) if start else None
    end = _to_date_string(end) if end else None
    if start and end and start > end:
        raise ValueError("Invalid date range: the start date is after the end date.")
    return start, end


# ---------------------------------------------------------------- CRUD
def add_transaction(transaction_type, amount, category, description, date_value, db_path=None):
    """Insert a transaction and return its new id."""
    values = validate_transaction(transaction_type, amount, category, description, date_value)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO transactions (transaction_type, amount, category, description, date) "
            "VALUES (?, ?, ?, ?, ?)",
            values,
        )
        return cur.lastrowid


def get_transaction(transaction_id, db_path=None):
    """Return one transaction as a dict, or None if it does not exist."""
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    return dict(row) if row else None


def update_transaction(transaction_id, transaction_type, amount, category, description,
                       date_value, db_path=None):
    """Update a transaction. Raises ValueError if the id does not exist or inputs are invalid."""
    values = validate_transaction(transaction_type, amount, category, description, date_value)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE transactions SET transaction_type = ?, amount = ?, category = ?, "
            "description = ?, date = ? WHERE id = ?",
            values + (transaction_id,),
        )
        if cur.rowcount == 0:
            raise ValueError(f"Transaction #{transaction_id} does not exist.")


def delete_transaction(transaction_id, db_path=None):
    """Delete a transaction. Raises ValueError if the id does not exist."""
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Transaction #{transaction_id} does not exist.")


# ---------------------------------------------------------------- queries
def _build_where(transaction_type=None, category=None, start=None, end=None, search=None):
    """Build a WHERE clause + parameter list from optional filters (all values are parameters)."""
    start, end = validate_date_range(start, end)
    clauses, params = [], []
    if transaction_type and transaction_type != "All":
        clauses.append("transaction_type = ?")
        params.append(transaction_type)
    if category and category != "All":
        clauses.append("category = ?")
        params.append(category)
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    if search and search.strip():
        clauses.append("description LIKE ?")
        params.append(f"%{search.strip()}%")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def get_transactions(transaction_type=None, category=None, start=None, end=None,
                     search=None, limit=None, db_path=None):
    """Return matching transactions (newest first) as a list of dicts."""
    where, params = _build_where(transaction_type, category, start, end, search)
    sql = f"SELECT * FROM transactions {where} ORDER BY date DESC, id DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(int(limit))
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_totals(start=None, end=None, db_path=None):
    """Return {'income', 'expenses', 'balance', 'count'} for the given period."""
    where, params = _build_where(start=start, end=end)
    sql = (
        "SELECT "
        "COALESCE(SUM(CASE WHEN transaction_type = 'Income'  THEN amount END), 0) AS income, "
        "COALESCE(SUM(CASE WHEN transaction_type = 'Expense' THEN amount END), 0) AS expenses, "
        f"COUNT(*) AS count FROM transactions {where}"
    )
    with get_connection(db_path) as conn:
        row = conn.execute(sql, params).fetchone()
    income, expenses = round(row["income"], 2), round(row["expenses"], 2)
    return {"income": income, "expenses": expenses,
            "balance": round(income - expenses, 2), "count": row["count"]}


def get_expenses_by_category(start=None, end=None, db_path=None):
    """Return [(category, total), ...] for expenses, highest first."""
    where, params = _build_where(transaction_type="Expense", start=start, end=end)
    sql = (f"SELECT category, SUM(amount) AS total FROM transactions {where} "
           "GROUP BY category ORDER BY total DESC")
    with get_connection(db_path) as conn:
        return [(r["category"], round(r["total"], 2)) for r in conn.execute(sql, params).fetchall()]


def get_monthly_totals(start=None, end=None, db_path=None):
    """Return [{'month': 'YYYY-MM', 'income': x, 'expenses': y}, ...] oldest month first."""
    where, params = _build_where(start=start, end=end)
    sql = (
        "SELECT substr(date, 1, 7) AS month, "
        "COALESCE(SUM(CASE WHEN transaction_type = 'Income'  THEN amount END), 0) AS income, "
        "COALESCE(SUM(CASE WHEN transaction_type = 'Expense' THEN amount END), 0) AS expenses "
        f"FROM transactions {where} GROUP BY month ORDER BY month"
    )
    with get_connection(db_path) as conn:
        return [{"month": r["month"], "income": round(r["income"], 2),
                 "expenses": round(r["expenses"], 2)} for r in conn.execute(sql, params).fetchall()]
