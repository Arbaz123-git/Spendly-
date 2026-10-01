import database.db as db

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def _create_expense_row(user_id, amount=100.0, category="Food",
                         date="2026-01-10", description="Original"):
    return db.create_expense(user_id, amount, category, date, description)


def _get_expense_row(expense_id):
    conn = db.get_db()
    try:
        return conn.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        conn.close()


# --- login required ---

def test_get_edit_expense_requires_login(client):
    resp = client.get("/expenses/1/edit")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_post_edit_expense_requires_login(client):
    resp = client.post("/expenses/1/edit", data={
        "amount": "50.0", "category": "Food",
        "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


# --- ownership / 404 ---

def test_get_edit_expense_other_users_expense_returns_404(client):
    db.create_user("Owner", "owner1@example.com", "password123")
    db.create_user("Intruder", "intruder1@example.com", "password123")
    owner = db.get_user_by_email("owner1@example.com")
    expense_id = _create_expense_row(owner["id"])

    _login(client, "intruder1@example.com", "password123")
    resp = client.get(f"/expenses/{expense_id}/edit")
    assert resp.status_code == 404


def test_get_edit_expense_nonexistent_id_returns_404(client):
    db.create_user("Test User", "nonexistentget@example.com", "password123")
    _login(client, "nonexistentget@example.com", "password123")

    resp = client.get("/expenses/999999/edit")
    assert resp.status_code == 404


def test_post_edit_expense_other_users_expense_returns_404(client):
    db.create_user("Owner", "owner2@example.com", "password123")
    db.create_user("Intruder", "intruder2@example.com", "password123")
    owner = db.get_user_by_email("owner2@example.com")
    expense_id = _create_expense_row(owner["id"])

    _login(client, "intruder2@example.com", "password123")
    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "999.0", "category": "Food",
        "date": "2026-03-20", "description": "Hacked",
    })
    assert resp.status_code == 404

    row = _get_expense_row(expense_id)
    assert row["amount"] == 100.0


def test_post_edit_expense_nonexistent_id_returns_404(client):
    db.create_user("Test User", "nonexistentpost@example.com", "password123")
    _login(client, "nonexistentpost@example.com", "password123")

    resp = client.post("/expenses/999999/edit", data={
        "amount": "50.0", "category": "Food",
        "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 404


# --- GET pre-fill ---

def test_get_edit_expense_authenticated_shows_prefilled_form(client):
    db.create_user("Test User", "editform@example.com", "password123")
    user = db.get_user_by_email("editform@example.com")
    expense_id = _create_expense_row(
        user["id"], amount=250.0, category="Transport",
        date="2026-02-15", description="Cab ride",
    )
    _login(client, "editform@example.com", "password123")

    resp = client.get(f"/expenses/{expense_id}/edit")
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data
    assert "250.0" in data or "250" in data
    assert "2026-02-15" in data
    assert "Cab ride" in data
    assert 'value="Transport" selected' in data or (
        "selected" in data and "Transport" in data
    )


# --- POST update ---

def test_post_edit_expense_valid_data_redirects_and_updates_row(client):
    db.create_user("Test User", "editvalid@example.com", "password123")
    user = db.get_user_by_email("editvalid@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editvalid@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "99.0", "category": "Health",
        "date": "2026-04-01", "description": "Updated desc",
    })
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    row = _get_expense_row(expense_id)
    assert row["amount"] == 99.0
    assert row["category"] == "Health"
    assert row["date"] == "2026-04-01"
    assert row["description"] == "Updated desc"


# --- validation errors (re-render, no DB change) ---

def test_post_edit_expense_missing_amount_rerenders_with_error(client):
    db.create_user("Test User", "editmissingamount@example.com", "password123")
    user = db.get_user_by_email("editmissingamount@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editmissingamount@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "category": "Food", "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 200
    assert "<form" in resp.data.decode("utf-8")

    row = _get_expense_row(expense_id)
    assert row["amount"] == 100.0


def test_post_edit_expense_zero_amount_rerenders_with_error(client):
    db.create_user("Test User", "editzeroamount@example.com", "password123")
    user = db.get_user_by_email("editzeroamount@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editzeroamount@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "0", "category": "Food",
        "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 200
    assert "<form" in resp.data.decode("utf-8")

    row = _get_expense_row(expense_id)
    assert row["amount"] == 100.0


def test_post_edit_expense_non_numeric_amount_rerenders_with_error(client):
    db.create_user("Test User", "editnonnumeric@example.com", "password123")
    user = db.get_user_by_email("editnonnumeric@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editnonnumeric@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "abc", "category": "Food",
        "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 200
    assert "<form" in resp.data.decode("utf-8")

    row = _get_expense_row(expense_id)
    assert row["amount"] == 100.0


def test_post_edit_expense_invalid_category_rerenders_with_error(client):
    db.create_user("Test User", "editinvalidcategory@example.com", "password123")
    user = db.get_user_by_email("editinvalidcategory@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editinvalidcategory@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "50.0", "category": "NotARealCategory",
        "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 200
    assert "<form" in resp.data.decode("utf-8")

    row = _get_expense_row(expense_id)
    assert row["category"] == "Food"


def test_post_edit_expense_invalid_date_rerenders_with_error(client):
    db.create_user("Test User", "editinvaliddate@example.com", "password123")
    user = db.get_user_by_email("editinvaliddate@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editinvaliddate@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "50.0", "category": "Food",
        "date": "not-a-date", "description": "Lunch",
    })
    assert resp.status_code == 200
    assert "<form" in resp.data.decode("utf-8")

    row = _get_expense_row(expense_id)
    assert row["date"] == "2026-01-10"


def test_post_edit_expense_blank_description_stores_null(client):
    db.create_user("Test User", "editnodescription@example.com", "password123")
    user = db.get_user_by_email("editnodescription@example.com")
    expense_id = _create_expense_row(user["id"])
    _login(client, "editnodescription@example.com", "password123")

    resp = client.post(f"/expenses/{expense_id}/edit", data={
        "amount": "50.0", "category": "Food",
        "date": "2026-03-20", "description": "",
    })
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    row = _get_expense_row(expense_id)
    assert row["description"] is None
