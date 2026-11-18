# Expense Tracker – Personal Finance Management System

A simple, local web app for recording, categorizing and analyzing daily income and expenses. Built with Python, Streamlit, SQLite, Pandas and Plotly. No paid APIs or external services needed.

## Features

- **Dashboard**: total income, total expenses, balance, transaction count, expense pie chart, monthly income-vs-expense bar chart, recent transactions.
- **Add Transaction**: income/expense with category, description and date; full input validation.
- **View Transactions**: filter by type, category, date range, and search by description.
- **Edit / Delete**: update any transaction; deletion asks for confirmation.
- **Financial Summary**: income, expenses, net savings, highest spending category and monthly breakdown for a chosen period.
- Data is stored permanently in a local SQLite file.

## Technology Stack

Python 3 · Streamlit · SQLite (`sqlite3`) · Pandas · Plotly

## Project Structure

```
expense-tracker/
├── app.py                  # Entry point: layout, sidebar navigation
├── database.py             # SQLite code
├── requirements.txt
├── README.md
├── .gitignore
├── components/
│   ├── dashboard.py        # Dashboard page + shared widgets
│   ├── transactions.py     # Add / View / Edit / Delete pages
│   └── analytics.py        # Financial Summary page
├── tests/
│   └── test_database.py    # unittest tests (temporary database)
└── expenses.db             # created automatically on first run
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run the App

From the project root folder:

```bash
streamlit run app.py
```
