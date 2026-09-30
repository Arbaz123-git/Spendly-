"""
Tests for Step 6: Date filter for the profile page.

Spec: .claude/specs/06-date-filter-profile-page.md

Covers `GET /profile?start_date=...&end_date=...`:
- auth guard (unchanged from Step 5)
- happy path: no params -> all-time data (unchanged from Step 5)
- inclusive range filtering of Transaction History
- summary stats (total spent, transaction count, top category) recompute
  for the filtered range
- Category Breakdown percentages recompute and sum to 100% for the
  filtered range
- form retains submitted start_date / end_date values
- Clear action returns to the unfiltered, all-time view
- empty-state message when a range matches zero transactions
- reversed range (end before start) falls back to all-time data, no error
- malformed date strings fall back to all-time data, no 500
- single missing param (only start_date or only end_date) falls back to
  all-time data, per db.py's paired start+end requirement
- no new DB schema / tables are introduced by this feature
"""

import re

import database.db as db


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def _create_user_with_expenses(email, expenses, name="Filter Test User", password="password123"):
    db.create_user(name, email, password)
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
    return user


# Fixed, deterministic dataset spanning a full month so range filters are
# unambiguous and independent of "today" (unlike db.py's seed helper).
EXPENSES = [
    (450.00, "Food", "Weekly groceries", "2026-03-01"),
    (150.00, "Transport", "Auto rickshaw fare", "2026-03-05"),
    (1200.00, "Bills", "Electricity bill", "2026-03-10"),
    (600.00, "Health", "Pharmacy purchase", "2026-03-15"),
    (350.00, "Entertainment", "Movie tickets", "2026-03-20"),
    (2200.00, "Shopping", "New pair of shoes", "2026-03-25"),
    (120.00, "Other", "Miscellaneous expense", "2026-03-28"),
    (800.00, "Food", "Dinner with friends", "2026-03-31"),
]


def _percentages(html):
    return [int(p) for p in re.findall(r"width:\s*(\d+)%", html)]


def _description_count(html):
    return html.count('data-label="Description"')


class TestAuthGuard:
    def test_filtered_profile_requires_login(self, client):
        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-31")
        assert resp.status_code == 302, "Unauthenticated filtered request must redirect"
        assert resp.headers["Location"].endswith("/login"), (
            "Unauthenticated filtered request must redirect to /login"
        )


class TestNoParamsUnchanged:
    def test_no_query_params_shows_all_time_history(self, client):
        _create_user_with_expenses("noparams@example.com", EXPENSES)
        _login(client, "noparams@example.com", "password123")

        resp = client.get("/profile")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")
        assert _description_count(data) == len(EXPENSES), (
            "With no filter params, all transactions should be listed"
        )

    def test_no_query_params_category_breakdown_sums_to_100(self, client):
        _create_user_with_expenses("noparams2@example.com", EXPENSES)
        _login(client, "noparams2@example.com", "password123")

        resp = client.get("/profile")
        data = resp.data.decode("utf-8")
        percents = _percentages(data)
        assert percents, "Expected category breakdown bars to be rendered"
        assert sum(percents) == 100


class TestInclusiveRangeFiltering:
    def test_range_includes_boundary_dates(self, client):
        _create_user_with_expenses("boundary@example.com", EXPENSES)
        _login(client, "boundary@example.com", "password123")

        # Range boundaries exactly match two expense dates (03-01 and 03-10);
        # both must be included (inclusive range).
        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-10")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")

        assert _description_count(data) == 3, (
            "Expected 3 transactions between 2026-03-01 and 2026-03-10 inclusive"
        )
        assert "Weekly groceries" in data, "Start-date boundary expense must be included"
        assert "Electricity bill" in data, "End-date boundary expense must be included"
        assert "New pair of shoes" not in data, "Out-of-range expense must be excluded"

    def test_range_excludes_transactions_outside_window(self, client):
        _create_user_with_expenses("outside@example.com", EXPENSES)
        _login(client, "outside@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-20&end_date=2026-03-25")
        data = resp.data.decode("utf-8")

        assert _description_count(data) == 2
        assert "Movie tickets" in data
        assert "New pair of shoes" in data
        assert "Weekly groceries" not in data
        assert "Dinner with friends" not in data


class TestSummaryStatsRecompute:
    def test_stats_total_and_count_reflect_filtered_range(self, client):
        _create_user_with_expenses("stats@example.com", EXPENSES)
        _login(client, "stats@example.com", "password123")

        # 2026-03-01 (450) + 2026-03-05 (150) + 2026-03-10 (1200) = 1800, count 3
        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-10")
        data = resp.data.decode("utf-8")

        assert "₹1,800" in data, "Filtered total spent should reflect only in-range expenses"

    def test_stats_top_category_reflects_filtered_range(self, client):
        _create_user_with_expenses("topcat@example.com", EXPENSES)
        _login(client, "topcat@example.com", "password123")

        # Within 2026-03-01..2026-03-10, Bills (1200) is the largest single
        # category total, ahead of Food (450) and Transport (150).
        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-10")
        data = resp.data.decode("utf-8")

        assert "Bills" in data, "Top category for the filtered range should be shown"


class TestCategoryBreakdownRecompute:
    def test_category_percentages_sum_to_100_for_filtered_range(self, client):
        _create_user_with_expenses("catpct@example.com", EXPENSES)
        _login(client, "catpct@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-20")
        data = resp.data.decode("utf-8")

        percents = _percentages(data)
        assert percents, "Expected category breakdown bars for the filtered range"
        assert sum(percents) == 100, (
            "Filtered category breakdown percentages must sum to 100%"
        )

    def test_category_breakdown_excludes_categories_outside_range(self, client):
        _create_user_with_expenses("catexclude@example.com", EXPENSES)
        _login(client, "catexclude@example.com", "password123")

        # Only the 2026-03-01 Food expense falls in this narrow range.
        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-01")
        data = resp.data.decode("utf-8")

        assert "Food" in data
        assert "Shopping" not in data, (
            "Categories with no expenses in the filtered range should not appear"
        )


class TestFormRetainsValues:
    def test_inputs_echo_submitted_start_and_end_date(self, client):
        _create_user_with_expenses("echo@example.com", EXPENSES)
        _login(client, "echo@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-05&end_date=2026-03-20")
        data = resp.data.decode("utf-8")

        assert 'value="2026-03-05"' in data, "start_date input should retain submitted value"
        assert 'value="2026-03-20"' in data, "end_date input should retain submitted value"


class TestClearAction:
    def test_clear_link_present_with_no_query_string(self, client):
        _create_user_with_expenses("clearlink@example.com", EXPENSES)
        _login(client, "clearlink@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-05&end_date=2026-03-20")
        data = resp.data.decode("utf-8")

        assert 'href="/profile"' in data, (
            "Clear action must link back to /profile with no query params"
        )

    def test_visiting_profile_without_params_after_filter_shows_all_time_again(self, client):
        _create_user_with_expenses("clearflow@example.com", EXPENSES)
        _login(client, "clearflow@example.com", "password123")

        client.get("/profile?start_date=2026-03-05&end_date=2026-03-20")
        resp = client.get("/profile")
        data = resp.data.decode("utf-8")

        assert _description_count(data) == len(EXPENSES), (
            "Clearing the filter (revisiting /profile) must restore all-time data"
        )


class TestEmptyState:
    def test_zero_matches_shows_empty_state_message_not_broken_table(self, client):
        _create_user_with_expenses("emptystate@example.com", EXPENSES)
        _login(client, "emptystate@example.com", "password123")

        resp = client.get("/profile?start_date=2026-01-01&end_date=2026-01-31")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")

        assert _description_count(data) == 0
        assert "No transactions" in data or "no transactions" in data.lower(), (
            "Expected an empty-state message when the range matches zero transactions"
        )

    def test_zero_matches_stats_show_zero_total(self, client):
        _create_user_with_expenses("emptystats@example.com", EXPENSES)
        _login(client, "emptystats@example.com", "password123")

        resp = client.get("/profile?start_date=2026-01-01&end_date=2026-01-31")
        data = resp.data.decode("utf-8")

        assert "₹0" in data, "Summary stats should show zero total for a non-matching range"


class TestReversedRangeFallback:
    def test_reversed_range_does_not_error(self, client):
        _create_user_with_expenses("reversed@example.com", EXPENSES)
        _login(client, "reversed@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-31&end_date=2026-03-01")
        assert resp.status_code == 200, "Reversed range must not raise a 4xx/5xx error"

    def test_reversed_range_falls_back_to_all_time_transactions(self, client):
        _create_user_with_expenses("reversed2@example.com", EXPENSES)
        _login(client, "reversed2@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-31&end_date=2026-03-01")
        data = resp.data.decode("utf-8")

        assert _description_count(data) == len(EXPENSES), (
            "start_date after end_date should be ignored, falling back to all-time data"
        )

    def test_reversed_range_falls_back_for_category_breakdown_too(self, client):
        _create_user_with_expenses("reversed3@example.com", EXPENSES)
        _login(client, "reversed3@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-31&end_date=2026-03-01")
        data = resp.data.decode("utf-8")

        percents = _percentages(data)
        assert sum(percents) == 100


class TestMalformedDateFallback:
    def test_malformed_start_date_does_not_500(self, client):
        _create_user_with_expenses("malformed@example.com", EXPENSES)
        _login(client, "malformed@example.com", "password123")

        resp = client.get("/profile?start_date=notadate&end_date=2026-03-20")
        assert resp.status_code == 200, "Malformed start_date must not cause a server error"

    def test_malformed_start_date_falls_back_to_all_time(self, client):
        _create_user_with_expenses("malformed2@example.com", EXPENSES)
        _login(client, "malformed2@example.com", "password123")

        resp = client.get("/profile?start_date=notadate&end_date=2026-03-20")
        data = resp.data.decode("utf-8")

        assert _description_count(data) == len(EXPENSES)

    def test_malformed_end_date_falls_back_to_all_time(self, client):
        _create_user_with_expenses("malformed3@example.com", EXPENSES)
        _login(client, "malformed3@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-01&end_date=31-03-2026")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")
        assert _description_count(data) == len(EXPENSES), (
            "Malformed end_date (wrong format) must fall back to all-time data"
        )

    def test_sql_injection_attempt_in_date_param_does_not_500(self, client):
        _create_user_with_expenses("injection@example.com", EXPENSES)
        _login(client, "injection@example.com", "password123")

        resp = client.get(
            "/profile?start_date=2026-03-01';DROP TABLE expenses;--&end_date=2026-03-20"
        )
        assert resp.status_code == 200, (
            "SQL-injection-like input in date params must not cause a server error "
            "(parameterized queries should treat it as an invalid date string)"
        )

    def test_empty_string_date_params_fall_back_to_all_time(self, client):
        _create_user_with_expenses("emptystr@example.com", EXPENSES)
        _login(client, "emptystr@example.com", "password123")

        resp = client.get("/profile?start_date=&end_date=")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")
        assert _description_count(data) == len(EXPENSES)


class TestSingleParamFallback:
    def test_only_start_date_falls_back_to_all_time(self, client):
        _create_user_with_expenses("onlystart@example.com", EXPENSES)
        _login(client, "onlystart@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-01")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")
        assert _description_count(data) == len(EXPENSES)

    def test_only_end_date_falls_back_to_all_time(self, client):
        _create_user_with_expenses("onlyend@example.com", EXPENSES)
        _login(client, "onlyend@example.com", "password123")

        resp = client.get("/profile?end_date=2026-03-20")
        assert resp.status_code == 200
        data = resp.data.decode("utf-8")
        assert _description_count(data) == len(EXPENSES)


class TestNoSchemaChanges:
    def test_no_new_tables_introduced_by_date_filter_feature(self, client):
        _create_user_with_expenses("schema@example.com", EXPENSES)
        _login(client, "schema@example.com", "password123")

        client.get("/profile?start_date=2026-03-01&end_date=2026-03-20")

        conn = db.get_db()
        try:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
        finally:
            conn.close()

        assert tables == {"users", "expenses"}, (
            "Date filter feature must not introduce new DB tables/schema"
        )


class TestOtherUsersDataIsolation:
    def test_date_filter_only_affects_logged_in_users_own_expenses(self, client):
        _create_user_with_expenses("ownerA@example.com", EXPENSES)
        _create_user_with_expenses(
            "ownerB@example.com",
            [(999.00, "Food", "Should not appear for A", "2026-03-05")],
        )
        _login(client, "ownerA@example.com", "password123")

        resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-10")
        data = resp.data.decode("utf-8")

        assert "Should not appear for A" not in data, (
            "Filtered results must be scoped to the logged-in user only"
        )
