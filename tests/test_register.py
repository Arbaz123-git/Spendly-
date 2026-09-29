import pytest
from werkzeug.security import check_password_hash

import database.db as db
from tests.conftest import count_users


def test_get_register_renders_form(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"Create your account" in resp.data
    assert b'action="/register"' in resp.data


def test_valid_registration_creates_user_and_redirects(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    user = db.get_user_by_email("alice@example.com")
    assert user is not None
    assert user["password_hash"] != "password123"
    assert check_password_hash(user["password_hash"], "password123")


def test_valid_registration_shows_success_message_after_redirect(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "alice2@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert b"Account created" in resp.data
    assert b"auth-success" in resp.data


def test_duplicate_email_shows_error_and_does_not_duplicate(client):
    data = {"name": "Alice Rao", "email": "dup@example.com", "password": "password123"}
    client.post("/register", data=data)

    resp = client.post("/register", data=data)
    assert resp.status_code == 200
    assert b"already exists" in resp.data
    assert count_users("dup@example.com") == 1


def test_duplicate_email_case_and_whitespace_insensitive(client):
    client.post(
        "/register",
        data={"name": "Alice Rao", "email": "case@example.com", "password": "password123"},
    )
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": " Case@Example.com ", "password": "password123"},
    )
    assert resp.status_code == 200
    assert b"already exists" in resp.data
    assert count_users("case@example.com") == 1


@pytest.mark.parametrize(
    "name,email,password",
    [
        ("", "missing@example.com", "password123"),
        ("Alice Rao", "", "password123"),
        ("Alice Rao", "missing2@example.com", ""),
        ("   ", "missing3@example.com", "password123"),
    ],
)
def test_missing_fields_rejected(client, name, email, password):
    resp = client.post(
        "/register", data={"name": name, "email": email, "password": password}
    )
    assert resp.status_code == 200
    assert b"required" in resp.data
    assert count_users(email.strip().lower()) == 0


def test_invalid_email_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 200
    assert count_users("not-an-email") == 0


def test_short_password_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "short@example.com", "password": "short12"},
    )
    assert resp.status_code == 200
    assert count_users("short@example.com") == 0


def test_password_exactly_eight_chars_accepted(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "eight@example.com", "password": "eightchr"},
    )
    assert resp.status_code == 302
    assert count_users("eight@example.com") == 1


def test_error_preserves_name_and_email_not_password(client):
    resp = client.post(
        "/register",
        data={"name": "Alice Rao", "email": "not-an-email", "password": "secretpw"},
    )
    assert b'value="Alice Rao"' in resp.data
    assert b'value="not-an-email"' in resp.data
    assert b"secretpw" not in resp.data
