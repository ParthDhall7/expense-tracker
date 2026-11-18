"""Unit tests for database.py.

Run from the project root:  python -m unittest discover -s tests -v
Every test uses its own temporary database file, never the real expenses.db.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db.init_db(self.path)

    def tearDown(self):
        os.remove(self.path)

    def add(self, t="Expense", amount=100, cat="Food", desc="lunch", d="2026-01-15"):
        return db.add_transaction(t, amount, cat, desc, d, db_path=self.path)

    # 1-2. valid adds
    def test_add_income_and_expense(self):
        i = self.add("Income", 5000, "Salary", "pay")
        e = self.add("Expense", 200, "Food")
        self.assertEqual(db.get_transaction(i, self.path)["transaction_type"], "Income")
        self.assertEqual(db.get_transaction(e, self.path)["amount"], 200)

    # 3-4. invalid amounts
    def test_zero_and_negative_amount_rejected(self):
        for bad in (0, -5, "abc", None, float("nan")):
            with self.assertRaises(ValueError):
                self.add(amount=bad)
        self.assertEqual(db.get_totals(db_path=self.path)["count"], 0)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            self.add(t="Gift")                      # bad type
        with self.assertRaises(ValueError):
            self.add(cat="")                        # empty category
        with self.assertRaises(ValueError):
            self.add(t="Income", cat="Food")        # category does not match type
        with self.assertRaises(ValueError):
            self.add(d="2026-13-45")                # bad date
        with self.assertRaises(ValueError):
            self.add(d="")                          # empty date

    # 5. edit
    def test_update_transaction(self):
        tid = self.add()
        db.update_transaction(tid, "Expense", 250.5, "Travel", "taxi", "2026-02-01", self.path)
        row = db.get_transaction(tid, self.path)
        self.assertEqual((row["amount"], row["category"], row["date"]), (250.5, "Travel", "2026-02-01"))

    def test_update_missing_and_invalid(self):
        with self.assertRaises(ValueError):
            db.update_transaction(999, "Expense", 10, "Food", "", "2026-01-01", self.path)
        tid = self.add()
        with self.assertRaises(ValueError):
            db.update_transaction(tid, "Expense", -1, "Food", "", "2026-01-01", self.path)

    # 6. delete
    def test_delete_transaction(self):
        tid = self.add()
        db.delete_transaction(tid, self.path)
        self.assertIsNone(db.get_transaction(tid, self.path))
        with self.assertRaises(ValueError):
            db.delete_transaction(tid, self.path)   # already gone

    # 7-8. filters
    def test_filters(self):
        self.add("Expense", 100, "Food", "pizza night", "2026-01-10")
        self.add("Expense", 50, "Travel", "bus", "2026-02-10")
        self.add("Income", 900, "Salary", "january pay", "2026-01-31")
        g = lambda **kw: db.get_transactions(db_path=self.path, **kw)
        self.assertEqual(len(g(category="Food")), 1)
        self.assertEqual(len(g(transaction_type="Income")), 1)
        self.assertEqual(len(g(start="2026-02-01", end="2026-02-28")), 1)
        self.assertEqual(len(g(search="PIZZA")), 1)
        self.assertEqual(len(g(search="zzz")), 0)
        with self.assertRaises(ValueError):
            g(start="2026-03-01", end="2026-01-01")  # invalid range

    def test_sql_injection_is_harmless(self):
        self.add(desc="normal")
        self.assertEqual(len(db.get_transactions(search="'; DROP TABLE transactions; --",
                                                 db_path=self.path)), 0)
        self.assertEqual(db.get_totals(db_path=self.path)["count"], 1)

    # 9. totals
    def test_totals_and_summaries(self):
        self.add("Income", 1000, "Salary", "", "2026-01-05")
        self.add("Expense", 300, "Food", "", "2026-01-06")
        self.add("Expense", 200, "Travel", "", "2026-02-06")
        self.assertEqual(db.get_totals(db_path=self.path),
                         {"income": 1000, "expenses": 500, "balance": 500, "count": 3})
        self.assertEqual(db.get_totals("2026-01-01", "2026-01-31", self.path)["expenses"], 300)
        self.assertEqual(db.get_expenses_by_category(db_path=self.path)[0], ("Food", 300))
        self.assertEqual(db.get_monthly_totals(db_path=self.path), [
            {"month": "2026-01", "income": 1000, "expenses": 300},
            {"month": "2026-02", "income": 0, "expenses": 200},
        ])
        # totals change after a delete
        db.delete_transaction(1, self.path)
        self.assertEqual(db.get_totals(db_path=self.path)["income"], 0)

    # 10. persistence
    def test_data_persists_after_reconnect(self):
        self.add(desc="persist me")
        db.init_db(self.path)                        # "restart": init must not wipe data
        self.assertEqual(db.get_transactions(db_path=self.path)[0]["description"], "persist me")

    def test_empty_database(self):
        self.assertEqual(db.get_totals(db_path=self.path)["balance"], 0)
        self.assertEqual(db.get_transactions(db_path=self.path), [])


if __name__ == "__main__":
    unittest.main()
