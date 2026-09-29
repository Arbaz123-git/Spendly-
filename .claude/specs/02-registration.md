# Spec: Registration

## Overview
This step implements user registration for Spendly. The `/register` route currently only renders a static form with no backend logic. This step wires that form up to actually create a user: validating input, hashing the password, inserting a row into the `users` table, and redirecting the new user into the app. This builds directly on Step 1 (database setup) and is a prerequisite for login (a future step) and any authenticated feature (profile, expenses).

## Depends on
- Step 1 — Database setup (`database/db.py` with `get_db()`, `init_db()`, `users` table)

## Routes
- `GET /register` — renders the registration form — public (already implemented, no change needed)
- `POST /register` — validates submitted data, creates the user, and redirects on success — public

## Database changes
No database changes. The `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports everything this feature needs. No new tables, columns, or constraints required.

## Templates
- **Create:** None
- **Modify:** `templates/register.html`
  - Change `<form method="POST" action="/register">` to `<form method="POST" action="{{ url_for('register') }}">` (never hardcode URLs)
  - Preserve submitted `name` and `email` values in the inputs on validation failure (re-render with `value="{{ name }}"` etc.) so the user doesn't retype everything
  - `{% if error %}` block already exists and can be reused for validation/duplicate-email errors

## Files to change
- `app.py` — update `register()` to accept `GET` and `POST`, add validation, call DB insert helper, handle duplicate email, redirect on success
- `templates/register.html` — fix hardcoded form action, preserve field values on error

## Files to create
None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic belongs in `database/db.py`, never inline in `app.py` routes — add a `create_user(name, email, password)` style helper there
- Route function in `app.py` should stay to one responsibility: read form data, call the DB helper, render/redirect — no business logic inline
- Validate on the server: `name`, `email`, `password` all required; email must contain "@"; password minimum 8 characters (matches the form's placeholder hint)
- Catch duplicate email (SQLite `UNIQUE` constraint / `IntegrityError`) and re-render the form with a clear error message — do not let it crash with a 500
- Use `abort()` for real HTTP errors, not bare error strings — validation failures re-render the template with an `error` message instead, matching the existing `register.html` pattern
- On success, redirect (do not render directly) to avoid duplicate form resubmission on refresh

## Definition of done
- [ ] `GET /register` still renders the form exactly as before
- [ ] Submitting the form with valid name/email/password creates a new row in `users` with a hashed password (verify via DB query — password is not stored in plaintext)
- [ ] Submitting with an email that already exists shows an error on the page instead of crashing, and does not insert a duplicate row
- [ ] Submitting with a missing field (name, email, or password) shows a validation error and does not insert a row
- [ ] Submitting with a password under 8 characters shows a validation error and does not insert a row
- [ ] After successful registration, the browser is redirected (not just rendered) to avoid resubmission on refresh
- [ ] The form's `action` uses `url_for('register')`, not a hardcoded path
- [ ] App starts without errors on port 5001 and `/register` works end-to-end in the browser
