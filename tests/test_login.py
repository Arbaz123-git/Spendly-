import pytest

import database.db as db
from werkzeug.security import check_password_hash


@pytest.fixture
def user():
    db.create_user("Alice Rao", "alice@example.com", "password123")
    return {"name": "Alice Rao", "email": "alice@example.com", "password": "password123"}


def test_get_login_renders_form(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b'action="/login"' in resp.data


def test_valid_login_redirects_and_sets_session(client, user):
    resp = client.post(
        "/login", data={"email": user["email"], "password": user["password"]}
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    with client.session_transaction() as sess:
        assert sess["user_name"] == "Alice Rao"
        assert sess["user_id"] is not None


def test_login_email_case_and_whitespace_insensitive(client, user):
    resp = client.post(
        "/login", data={"email": " Alice@Example.COM ", "password": user["password"]}
    )
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user_name"] == "Alice Rao"


def test_wrong_password_rejected(client, user):
    resp = client.post(
        "/login", data={"email": user["email"], "password": "wrongpassword"}
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_unknown_email_rejected(client):
    resp = client.post(
        "/login", data={"email": "nobody@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_empty_fields_rejected(client):
    resp = client.post("/login", data={"email": "", "password": ""})
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_error_preserves_email_not_password(client, user):
    resp = client.post(
        "/login", data={"email": user["email"], "password": "wrongpassword"}
    )
    assert b'value="alice@example.com"' in resp.data
    assert b"wrongpassword" not in resp.data


def test_nav_shows_signed_in_state_after_login(client, user):
    client.post("/login", data={"email": user["email"], "password": user["password"]})
    resp = client.get("/")
    assert b"Sign out" in resp.data
    assert b"Get started" not in resp.data


def test_logout_clears_session_and_redirects(client, user):
    client.post("/login", data={"email": user["email"], "password": user["password"]})

    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    with client.session_transaction() as sess:
        assert "user_id" not in sess

    resp = client.get("/logout", follow_redirects=True)
    assert b"signed out" in resp.data
    assert b"Sign in" in resp.data


def test_logout_while_logged_out_does_not_error(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_logged_in_user_redirected_away_from_login_and_register(client, user):
    client.post("/login", data={"email": user["email"], "password": user["password"]})

    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    resp = client.get("/register")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_password_stored_as_salted_hash_not_plaintext(client, user):
    stored = db.get_user_by_email(user["email"])
    assert stored["password_hash"] != user["password"]
    assert stored["password_hash"].startswith(("pbkdf2:", "scrypt:"))
    assert check_password_hash(stored["password_hash"], user["password"])

    db.create_user("Bob Rao", "bob@example.com", user["password"])
    other = db.get_user_by_email("bob@example.com")
    assert other["password_hash"] != stored["password_hash"]


def test_login_clears_prior_session_data(client, user):
    with client.session_transaction() as sess:
        sess["junk"] = "leftover"

    client.post("/login", data={"email": user["email"], "password": user["password"]})

    with client.session_transaction() as sess:
        assert "junk" not in sess
