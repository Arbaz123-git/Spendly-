import pytest

import database.db as db


# Never `from app import app` at module top level — collection happens
# before this fixture patches DB_PATH, which would hit the real
# expense_tracker.db. The patch must run first, then the import.
@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))

    from app import app as flask_app

    flask_app.config.update(TESTING=True)
    db.init_db()
    return flask_app


def count_users(email):
    conn = db.get_db()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?", (email,)
        ).fetchone()[0]
    finally:
        conn.close()
