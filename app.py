import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash

from database.db import (
    get_db, init_db, seed_db, create_user, get_user_by_email, get_user_by_id,
    get_transactions_for_user, get_summary_stats, get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# ------------------------------------------------------------------ #
# Validation helpers                                                  #
# ------------------------------------------------------------------ #

def validate_registration(name, email, password):
    if not name or not email or not password:
        return "All fields are required."
    if "@" not in email:
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


# ------------------------------------------------------------------ #
# Profile formatting helpers                                          #
# ------------------------------------------------------------------ #

def _format_currency(amount):
    return f"₹{amount:,.0f}"


def _format_date(iso_date):
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{dt.day} {dt.strftime('%b %Y')}"


def _format_member_since(created_at):
    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    return f"{dt.day} {dt.strftime('%b %Y')}"


def _format_transactions(rows):
    return [
        {
            "date": _format_date(row["date"]),
            "description": row["description"],
            "category": row["category"],
            "amount": _format_currency(row["amount"]),
        }
        for row in rows
    ]


def _format_stats(summary):
    top_category = summary["top_category"] or "—"
    return [
        {"label": "Total spent", "value": _format_currency(summary["total"])},
        {"label": "Transactions", "value": str(summary["count"])},
        {"label": "Top category", "value": top_category},
    ]


def _parse_date_range(args):
    """Validate start_date/end_date query params (YYYY-MM-DD).
    Returns (start_date, end_date) as strings when both are present, valid,
    and start_date <= end_date; otherwise (None, None) — no date filter."""
    start_raw = args.get("start_date", "").strip()
    end_raw = args.get("end_date", "").strip()
    if not start_raw and not end_raw:
        return None, None
    if not start_raw or not end_raw:
        flash("Please provide both a start and end date to filter.", "filter-error")
        return None, None
    try:
        start_dt = datetime.strptime(start_raw, "%Y-%m-%d")
        end_dt = datetime.strptime(end_raw, "%Y-%m-%d")
    except ValueError:
        flash("That date range wasn't valid — showing all-time data instead.", "filter-error")
        return None, None
    if start_dt > end_dt:
        flash("Start date must be before end date — showing all-time data instead.", "filter-error")
        return None, None
    return start_raw, end_raw


def _compute_percentages(amounts):
    total = sum(amounts)
    if total <= 0:
        return [0] * len(amounts)

    raw = [amt / total * 100 for amt in amounts]
    floored = [int(r) for r in raw]
    remainder = 100 - sum(floored)

    if floored:
        floored[0] += remainder

    return floored


def _format_categories(rows):
    if not rows:
        return []
    amounts = [row["total"] for row in rows]
    percentages = _compute_percentages(amounts)
    return [
        {
            "name": row["category"],
            "amount": _format_currency(row["total"]),
            "percent": pct,
        }
        for row, pct in zip(rows, percentages)
    ]


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = validate_registration(name, email, password)
    if error is None and create_user(name, email, password) is None:
        error = "An account with that email already exists."

    if error:
        return render_template("register.html", error=error, name=name, email=email)

    flash("Account created — please sign in", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email) if email and password else None
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        )

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been signed out.", "success")
    return redirect(url_for("login"))


# ------------------------------------------------------------------ #
# Profile route                                                       #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db_user = get_user_by_id(user_id)
    start_date, end_date = _parse_date_range(request.args)

    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "member_since": _format_member_since(db_user["created_at"]),
    }

    stats = _format_stats(get_summary_stats(user_id, start_date, end_date))
    transactions = _format_transactions(
        get_transactions_for_user(user_id, start_date, end_date)
    )
    categories = _format_categories(
        get_category_breakdown(user_id, start_date, end_date)
    )

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        filters={"start_date": start_date or "", "end_date": end_date or ""},
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


# ------------------------------------------------------------------ #
# Database initialization                                            #
# ------------------------------------------------------------------ #

with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
