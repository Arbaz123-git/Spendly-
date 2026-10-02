# Spec: Delete Expense

## Overview
Step 9 lets a logged-in user permanently delete one of their own expenses.
The existing stub route `GET /expenses/<id>/delete` is replaced with a real
handler scoped to the current user. To avoid destructive one-click GET links
(a GET request should never mutate data), deletion is implemented as a
`POST /expenses/<id>/delete` triggered from a small confirmation form in the
profile transactions table, next to the existing "Edit" link. A new query
helper, `delete_expense`, is added to `database/db.py`.

## Depends on
- Step 1: Database setup (`expenses` table exists)
- Step 3: Login / Logout (`session["user_id"]` is set and enforced)
- Step 5: Profile page renders transactions with an Actions column
- Step 8: Edit Expense (`get_expense_by_id` already enforces per-user ownership
  and establishes the Actions-column pattern this step extends)

## Routes
- `POST /expenses/<int:id>/delete` — delete the given expense if it belongs
  to the logged-in user, then redirect to `/profile` — logged-in only

The existing stub is a `GET` route; it is changed to `POST` only, since
deletion is a mutation and must not be reachable via a plain link or GET.

## Database changes
No new tables or columns. All required columns already exist in `expenses`.

## Templates
- **Modify:** `templates/profile.html`
  - In the existing `profile-td-actions` cell (next to the "Edit" link), add
    a small inline form:
    ```html
    <form method="POST" action="{{ url_for('delete_expense', id=tx.id) }}"
          class="profile-delete-form"
          onsubmit="return confirm('Delete this expense?');">
        <button type="submit" class="profile-delete-link">Delete</button>
    </form>
    ```
  - No new page is created; this only adds a button + form to the existing row.

## Files to change
- `database/db.py`
  - Add `delete_expense(expense_id, user_id)` — issues a parameterised
    `DELETE FROM expenses WHERE id = ? AND user_id = ?` for ownership safety;
    returns the number of rows deleted (`cursor.rowcount`) so the caller can
    detect a no-op delete.
- `app.py`
  - Import `delete_expense` from `database.db`.
  - Replace the stub:
    ```python
    @app.route("/expenses/<int:id>/delete")
    def delete_expense(id):
        return "Delete expense — coming in Step 9"
    ```
    with:
    ```python
    @app.route("/expenses/<int:id>/delete", methods=["POST"])
    def delete_expense(id):
        if not session.get("user_id"):
            return redirect(url_for("login"))

        expense = get_expense_by_id(id, session["user_id"])
        if expense is None:
            abort(404)

        delete_expense_row(id, session["user_id"])
        flash("Expense deleted.", "success")
        return redirect(url_for("profile"))
    ```
    (Using `get_expense_by_id`, already imported for the edit feature, to
    check ownership/existence before deleting and return a 404 otherwise.
    The DB helper is imported under an alias, e.g. `delete_expense as
    delete_expense_row`, to avoid clashing with the route function name.)
- `templates/profile.html`
  - Add the delete form described above inside `profile-td-actions`.
- `static/css/profile.css`
  - Add minimal styling for `.profile-delete-form` (inline-block, no layout
    shift next to the Edit link) and `.profile-delete-link` (match the
    existing `.profile-edit-link` sizing/color using CSS variables; use a
    "danger" variable if one exists, otherwise reuse existing link styling).

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (unaffected by this feature, carried over
  as a standing rule)
- Foreign keys PRAGMA must be enabled on every connection (already done in
  `get_db()`)
- Deletion must be a `POST` route — never a `GET` — since it mutates data
- `delete_expense` (DB helper) must scope its `DELETE` to
  `id = ? AND user_id = ?` to prevent one user deleting another user's expense
- Unauthenticated POST to `/expenses/<id>/delete` must redirect to `/login`
- If the expense does not exist or belongs to another user, return a 404
  (checked via `get_expense_by_id` before calling the delete helper)
- After a successful delete, redirect to `url_for("profile")` with a flash
  message — do not render any other template
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline `<style>` tags — add styles to `static/css/profile.css`
- Currency must always display as ₹ — never £ or $
- Never hardcode URLs in templates — use `url_for('delete_expense', id=...)`

## Definition of done
- [ ] Each transaction row in `/profile` has a "Delete" button next to "Edit"
- [ ] Clicking "Delete" shows a browser confirmation dialog before submitting
- [ ] Confirming deletion removes the expense and redirects to `/profile`
- [ ] The deleted expense no longer appears in the transaction list or stats
- [ ] A success flash message is shown after deletion
- [ ] Sending `POST /expenses/<id>/delete` while logged out redirects to `/login`
- [ ] Sending `POST /expenses/<id>/delete` for a non-existent expense returns 404
- [ ] Sending `POST /expenses/<id>/delete` for another user's expense returns 404
  and does not delete the row
- [ ] Sending `GET /expenses/<id>/delete` no longer works (405, since the route
  is POST-only)
