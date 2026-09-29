# Spec: Login and Logout

## Overview
This feature implements user authentication for Spendly: verifying credentials on `POST /login` and establishing a Flask session, plus a working `GET /logout` that clears that session. It is the bridge between registration (Step 2) and any logged-in-only feature (profile, expenses), since nothing past this point can identify "the current user" without it. `login.html` already has a wired-up form posting to `login`, but the route itself is GET-only today, so submitting it currently returns a 405. `/logout` is currently a raw-string stub.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`, `PRAGMA foreign_keys = ON`)
- Step 02 — Registration (`create_user()`, `password_hash` column populated via `werkzeug.security.generate_password_hash`, existing `get_user_by_email()` helper)

## Routes
- `POST /login` — validate email/password against `users`, start session on success, re-render `login.html` with error on failure — public
- `GET /logout` — clear the session and redirect to `login` — logged-in (safe to allow logged-out access too; no sensitive data exposed either way)

`GET /login` already exists and stays as-is (renders `login.html`).

## Database changes
No database changes. `get_user_by_email(email)` already exists in `database/db.py` and returns a full `sqlite3.Row` including `password_hash`, which is sufficient for credential verification via `werkzeug.security.check_password_hash`.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — no structural changes expected; already has `{% if error %}` block and flashed-success display consistent with `register.html`. Verify the POST target and field names (`email`, `password`) match what the route reads from `request.form`.
  - `templates/base.html` — add session-aware nav: when `session.get('user_id')` is set, replace the `Sign in` / `Get started` links with a logout link (`url_for('logout')`) and optionally a user greeting; otherwise keep current behavior unchanged.

## Files to change
- `app.py` — implement `POST /login` handling on the existing `login` route (accept both GET and POST), implement `GET /logout`
- `templates/base.html` — conditional nav based on session state

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is available via the existing `werkzeug==3.1.6` dependency.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (already satisfied by reusing `get_user_by_email()`)
- Passwords verified with `werkzeug.security.check_password_hash` against `password_hash` — never compare plaintext
- Use Flask's built-in `session` object (`app.secret_key` is already configured) — no new session/auth packages
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No DB logic inline in `app.py` — if new queries are needed beyond `get_user_by_email()`, add them to `database/db.py`
- `GET /logout` and `POST /login` must render templates or redirect — never a raw string return
- Update the roadmap table in `CLAUDE.md` to mark `GET /logout` as implemented once done

## Definition of done
- [ ] Visiting `/login` and submitting valid credentials (e.g. seeded `demo@spendly.com` / `demo123`) redirects away from `/login` and sets a session (verify via a subsequent request that depends on session, or by inspecting the session cookie)
- [ ] Submitting `/login` with a wrong password re-renders `login.html` with an error message and does not set a session
- [ ] Submitting `/login` with a non-existent email re-renders `login.html` with an error message (not a stack trace or 500)
- [ ] Visiting `/logout` while logged in clears the session and redirects to `/login`
- [ ] Visiting `/logout` while logged out does not error (no raw string, no 500)
- [ ] Nav bar in `base.html` shows a logout option instead of "Sign in"/"Get started" when a session is active, and reverts after logout
- [ ] `pytest` passes with no regressions in existing registration/database tests
