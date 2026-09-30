# Spec: Date Filter For Profile Page

## Overview
Step 6 adds a date-range filter to the profile page's Transaction History and
Category Breakdown sections. Right now `/profile` always shows a user's
entire expense history with no way to narrow it down. This step lets a
logged-in user filter their transactions and category totals to a specific
date range (or a quick preset like "This Month" / "Last 30 Days"), so the
page stays useful once a user has months of expense data. Filtering happens
server-side via a query string on `GET /profile` — no new pages, no AJAX.

## Depends on
- Step 1: Database setup (`expenses` table with a `date` column)
- Step 3: Login / Logout (`session["user_id"]` is set)
- Step 5: Backend routes for profile page (`/profile` already queries live
  data via `get_summary_stats`, `get_category_breakdown`,
  `get_transactions_for_user` in `database/db.py`)

## Routes
- `GET /profile` — modified, not new — description: accepts optional
  `start_date` and `end_date` query params (`YYYY-MM-DD`) to filter
  transactions, stats, and category breakdown to that range; falls back to
  all-time data when no params are given — access level: logged-in

If no new routes: N/A — only `/profile` changes.

## Database changes
No database changes. The `expenses.date` column (TEXT, `YYYY-MM-DD`, already
`NOT NULL`) is sufficient for range filtering with parameterized `BETWEEN` /
comparison queries.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter bar above "Transaction History" with a `<form>` (`GET`,
    action `{{ url_for('profile') }}`) containing two `<input type="date">`
    fields (`start_date`, `end_date`) and a submit button, plus a "Clear"
    link back to `{{ url_for('profile') }}` with no query params.
  - Preserve submitted `start_date` / `end_date` values in the inputs so the
    form reflects the active filter after submit.
  - If a date range is active and produces zero transactions, show an empty
    state message in the Transaction History section instead of an empty
    table.

## Files to change
- `app.py` — `profile()` view reads `start_date` / `end_date` from
  `request.args`, validates them, and passes them through to the three query
  functions and back into the template context
- `database/db.py` — extend `get_summary_stats`, `get_category_breakdown`,
  `get_transactions_for_user` to accept optional `start_date` / `end_date`
  keyword arguments and apply them as parameterized `WHERE date >= ? AND
  date <= ?` conditions when present
- `templates/profile.html` — add the filter form and empty-state markup
- `static/css/profile.css` — style the new filter bar to match the existing
  profile page design system (CSS variables only)

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never f-string or concatenate dates into SQL
- Passwords hashed with werkzeug (unaffected by this step, listed for
  consistency)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- FK enforcement stays manual — `get_db()` continues to run
  `PRAGMA foreign_keys = ON` on every connection (no change needed here)
- Currency must always display as ₹ — never £ or $
- Route function (`profile()`) only fetches data and renders the template —
  date validation/parsing logic belongs in a small helper, not inline
  branching in the route body
- If `start_date` is after `end_date`, ignore both and fall back to all-time
  data rather than raising an error
- Invalid or malformed date strings in query params must be ignored (treated
  as "no filter"), never cause a 500

## Definition of done
- [ ] Visiting `/profile` with no query params shows full all-time
      transaction history and category breakdown (unchanged from Step 5)
- [ ] Submitting the filter form with a `start_date`/`end_date` range shows
      only transactions within that range (inclusive) in Transaction History
- [ ] Summary stats (total spent, transaction count, top category) update to
      reflect only the filtered range
- [ ] Category breakdown percentages recompute and sum to 100% for the
      filtered range
- [ ] The date inputs retain the submitted values after the page reloads
- [ ] A "Clear" action returns to the unfiltered, all-time view
- [ ] Selecting a range with no matching transactions shows an empty-state
      message instead of a broken/empty table
- [ ] An end date before the start date does not error — page falls back to
      all-time data
- [ ] Manually editing the URL with a malformed date (e.g.
      `?start_date=notadate`) does not 500 — page falls back to all-time data
