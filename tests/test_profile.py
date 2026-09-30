import re

import database.db as db


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def _create_user_with_expenses(email, expenses):
    db.create_user("Test User", email, "password123")
    user = db.get_user_by_email(email)
    conn = db.get_db()
    try:
        for amount, category, description, exp_date in expenses:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (user["id"], amount, category, exp_date, description),
            )
        conn.commit()
    finally:
        conn.close()


SEED_EXPENSES = [
    (450.00, "Food", "Weekly groceries", "2026-09-01"),
    (150.00, "Transport", "Auto rickshaw fare", "2026-09-04"),
    (1200.00, "Bills", "Electricity bill", "2026-09-07"),
    (600.00, "Health", "Pharmacy purchase", "2026-09-10"),
    (350.00, "Entertainment", "Movie tickets", "2026-09-13"),
    (2200.00, "Shopping", "New pair of shoes", "2026-09-17"),
    (120.00, "Other", "Miscellaneous expense", "2026-09-21"),
    (800.00, "Food", "Dinner with friends", "2026-09-25"),
]


def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_profile_shows_real_expense_data(client):
    _create_user_with_expenses("expenses@example.com", SEED_EXPENSES)
    _login(client, "expenses@example.com", "password123")

    resp = client.get("/profile")
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "expenses@example.com" in data
    assert "₹5,870" in data
    assert "Shopping" in data
    assert data.count('data-label="Description"') == 8


def test_profile_category_percentages_sum_to_100(client):
    _create_user_with_expenses("categories@example.com", SEED_EXPENSES)
    _login(client, "categories@example.com", "password123")

    resp = client.get("/profile")
    data = resp.data.decode("utf-8")

    percents = [int(p) for p in re.findall(r"width:\s*(\d+)%", data)]
    assert len(percents) == 7
    assert sum(percents) == 100


def test_profile_zero_expenses_for_new_user(client):
    db.create_user("New User", "new@spendly.com", "password123")
    _login(client, "new@spendly.com", "password123")

    resp = client.get("/profile")
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "new@spendly.com" in data
    assert "₹0" in data
    assert data.count('data-label="Description"') == 0
