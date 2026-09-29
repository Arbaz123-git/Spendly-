import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": session.get("user_name", "Demo User"),
        "email": "demo@spendly.com",
        "member_since": "12 Jan 2026",
    }

    stats = [
        {"label": "Total spent", "value": "₹5,870"},
        {"label": "Transactions", "value": "8"},
        {"label": "Top category", "value": "Shopping"},
    ]

    transactions = [
        {"date": "25 Sep 2026", "description": "Dinner with friends", "category": "Food", "amount": "₹800"},
        {"date": "21 Sep 2026", "description": "Miscellaneous expense", "category": "Other", "amount": "₹120"},
        {"date": "17 Sep 2026", "description": "New pair of shoes", "category": "Shopping", "amount": "₹2,200"},
        {"date": "13 Sep 2026", "description": "Movie tickets", "category": "Entertainment", "amount": "₹350"},
        {"date": "10 Sep 2026", "description": "Pharmacy purchase", "category": "Health", "amount": "₹600"},
        {"date": "7 Sep 2026", "description": "Electricity bill", "category": "Bills", "amount": "₹1,200"},
        {"date": "4 Sep 2026", "description": "Auto rickshaw fare", "category": "Transport", "amount": "₹150"},
        {"date": "1 Sep 2026", "description": "Weekly groceries", "category": "Food", "amount": "₹450"},
    ]

    categories = [
        {"name": "Shopping", "amount": "₹2,200", "percent": 37},
        {"name": "Bills", "amount": "₹1,200", "percent": 20},
        {"name": "Food", "amount": "₹1,250", "percent": 21},
        {"name": "Health", "amount": "₹600", "percent": 10},
        {"name": "Entertainment", "amount": "₹350", "percent": 6},
        {"name": "Transport", "amount": "₹150", "percent": 3},
        {"name": "Other", "amount": "₹120", "percent": 2},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
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
