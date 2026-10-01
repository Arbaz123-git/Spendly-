import os
import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "expense_tracker.db")

CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
)
"""

CREATE_EXPENSES_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute(CREATE_USERS_SQL)
        conn.execute(CREATE_EXPENSES_SQL)
        conn.commit()
    finally:
        conn.close()


def create_user(name, email, password):
    conn = get_db()
    try:
        password_hash = generate_password_hash(password)
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return None
        return cursor.lastrowid
    finally:
        conn.close()


def create_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def _sample_expenses():
    today = date.today()
    first_of_month = today.replace(day=1)

    def d(offset_days):
        candidate = first_of_month + timedelta(days=offset_days)
        return min(candidate, today).isoformat()

    return [
        (450.00, "Food", "Weekly groceries", d(1)),
        (150.00, "Transport", "Auto rickshaw fare", d(4)),
        (1200.00, "Bills", "Electricity bill", d(7)),
        (600.00, "Health", "Pharmacy purchase", d(10)),
        (350.00, "Entertainment", "Movie tickets", d(13)),
        (2200.00, "Shopping", "New pair of shoes", d(17)),
        (120.00, "Other", "Miscellaneous expense", d(21)),
        (800.00, "Food", "Dinner with friends", d(25)),
    ]


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing > 0:
            return

        password_hash = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cursor.lastrowid

        for amount, category, description, exp_date in _sample_expenses():
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category, exp_date, description),
            )

        conn.commit()
    finally:
        conn.close()


def _date_filter_clause(user_id, start_date, end_date):
    """Build a WHERE clause scoped to user_id, plus an inclusive date range
    when both start_date and end_date are given. A single bound with no
    matching counterpart is treated as no date filter at all."""
    clause = "user_id = ?"
    params = [user_id]
    if start_date and end_date:
        clause += " AND date >= ? AND date <= ?"
        params += [start_date, end_date]
    return clause, params


def get_summary_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_filter_clause(user_id, start_date, end_date)

        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
            "FROM expenses WHERE " + where,
            params,
        ).fetchone()

        top = conn.execute(
            "SELECT category, SUM(amount) AS cat_total "
            "FROM expenses WHERE " + where + " "
            "GROUP BY category "
            "ORDER BY cat_total DESC, category ASC "
            "LIMIT 1",
            params,
        ).fetchone()

        return {
            "total": totals["total"],
            "count": totals["count"],
            "top_category": top["category"] if top else None,
        }
    finally:
        conn.close()


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_filter_clause(user_id, start_date, end_date)
        return conn.execute(
            "SELECT category, SUM(amount) AS total "
            "FROM expenses WHERE " + where + " "
            "GROUP BY category "
            "ORDER BY total DESC, category ASC",
            params,
        ).fetchall()
    finally:
        conn.close()


def get_transactions_for_user(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_filter_clause(user_id, start_date, end_date)
        return conn.execute(
            "SELECT id, date, description, category, amount "
            "FROM expenses WHERE " + where + " "
            "ORDER BY date DESC, id DESC",
            params,
        ).fetchall()
    finally:
        conn.close()


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        ).fetchone()
    finally:
        conn.close()


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
            "WHERE id = ? AND user_id = ?",
            (amount, category, date, description, expense_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()
