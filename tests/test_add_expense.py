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


def _get_expense_rows(user_id):
    conn = db.get_db()
    try:
        return conn.execute(
            "SELECT amount, category, date, description FROM expenses "
            "WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def test_get_add_expense_requires_login(client):
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_post_add_expense_requires_login(client):
    resp = client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_get_add_expense_authenticated_shows_form(client):
    db.create_user("Test User", "addform@example.com", "password123")
    _login(client, "addform@example.com", "password123")

    resp = client.get("/expenses/add")
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    for category in CATEGORIES:
        assert category in data, f"Expected category '{category}' in form"

    assert "<form" in data, "Expected a <form element in the add-expense page"
    assert 'method="POST"' in data or 'method="post"' in data, (
        "Expected the form to use method POST"
    )


def test_post_add_expense_valid_data_redirects_and_inserts_row(client):
    db.create_user("Test User", "addvalid@example.com", "password123")
    _login(client, "addvalid@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    user = db.get_user_by_email("addvalid@example.com")
    rows = _get_expense_rows(user["id"])
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


def test_post_add_expense_missing_amount_rerenders_with_error(client):
    db.create_user("Test User", "missingamount@example.com", "password123")
    _login(client, "missingamount@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data

    user = db.get_user_by_email("missingamount@example.com")
    assert len(_get_expense_rows(user["id"])) == 0


def test_post_add_expense_zero_amount_rerenders_with_error(client):
    db.create_user("Test User", "zeroamount@example.com", "password123")
    _login(client, "zeroamount@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data

    user = db.get_user_by_email("zeroamount@example.com")
    assert len(_get_expense_rows(user["id"])) == 0


def test_post_add_expense_non_numeric_amount_rerenders_with_error(client):
    db.create_user("Test User", "nonnumeric@example.com", "password123")
    _login(client, "nonnumeric@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data

    user = db.get_user_by_email("nonnumeric@example.com")
    assert len(_get_expense_rows(user["id"])) == 0


def test_post_add_expense_invalid_category_rerenders_with_error(client):
    db.create_user("Test User", "invalidcategory@example.com", "password123")
    _login(client, "invalidcategory@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "NotARealCategory",
            "date": "2026-03-20",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data

    user = db.get_user_by_email("invalidcategory@example.com")
    assert len(_get_expense_rows(user["id"])) == 0


def test_post_add_expense_invalid_date_rerenders_with_error(client):
    db.create_user("Test User", "invaliddate@example.com", "password123")
    _login(client, "invaliddate@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Lunch",
        },
    )
    assert resp.status_code == 200

    data = resp.data.decode("utf-8")
    assert "<form" in data

    user = db.get_user_by_email("invaliddate@example.com")
    assert len(_get_expense_rows(user["id"])) == 0


def test_post_add_expense_blank_description_is_optional_and_stores_null(client):
    db.create_user("Test User", "nodescription@example.com", "password123")
    _login(client, "nodescription@example.com", "password123")

    resp = client.post(
        "/expenses/add",
        data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    user = db.get_user_by_email("nodescription@example.com")
    rows = _get_expense_rows(user["id"])
    assert len(rows) == 1
    assert rows[0]["description"] is None
