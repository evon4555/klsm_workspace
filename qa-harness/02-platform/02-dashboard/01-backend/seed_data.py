"""
Seed script — populate the database with realistic mock test run history.

Run:
    cd <qa-harness root>
    python -m dashboard.backend.seed_data

Generates ~20 test runs over the past 30 days with:
  - Gradually increasing test suite size (team writing more tests)
  - Realistic mix of pass/fail/skip rates
  - Real Playwright/Behave error messages
  - Some flaky tests
  - Multiple environments
"""

import random
from datetime import datetime, timedelta

from database import TestRun, TestScenario, get_db, init_db

# ---------------------------------------------------------------------------
# Scenario templates — realistic feature/scenario combinations
# ---------------------------------------------------------------------------

SCENARIOS = [
    # (feature, scenario_name, tags, is_flaky)
    ("Login & Authentication", "Admin login via API", "@hybrid,@auth", False),
    ("Login & Authentication", "Invalid password shows error", "@ui,@auth", False),
    ("Login & Authentication", "Token refresh after expiry", "@api,@auth", True),  # flaky
    ("Login & Authentication", "Logout clears session", "@ui,@auth", False),
    ("Program Management", "Create a new program via API", "@hybrid,@antank", False),
    ("Program Management", "Edit program name in UI", "@ui,@antank", True),  # flaky
    ("Program Management", "Delete program with confirmation", "@hybrid,@antank", False),
    ("Program Management", "List programs with pagination", "@api,@antank", False),
    ("Ticket System", "Create ticket via API", "@hybrid,@ticket", False),
    ("Ticket System", "Search ticket by keyword", "@ui,@ticket", False),
    ("Ticket System", "Update ticket status", "@api,@ticket", False),
    ("Ticket System", "Ticket list loads correctly", "@ui,@ticket", True),  # flaky
    ("Smoke Tests", "API health check returns 200", "@smoke,@api", False),
    ("Smoke Tests", "Homepage loads successfully", "@smoke,@ui", False),
    ("Smoke Tests", "Hybrid smoke test", "@smoke,@hybrid", False),
    ("User Management", "Create new user via API", "@api,@user", False),
    ("User Management", "User profile page displays correctly", "@ui,@user", False),
    ("User Management", "Change user role", "@hybrid,@user", False),
    ("Reports", "Generate daily report", "@api,@report", False),
    ("Reports", "Export report to PDF", "@ui,@report", True),  # flaky
]

# ---------------------------------------------------------------------------
# Realistic error messages per category
# ---------------------------------------------------------------------------

ERRORS = {
    "SelectorChanged": [
        "locator.click: Error: locator('#btn-submit') resolved to 0 elements\n\n  at tests/pages/login_page.py:42\n\nWaiting for locator('#btn-submit')\n  selector resolved to hidden element",
        "locator.fill: Error: locator('input[name=\"username\"]') resolved to 0 elements\n\n  at tests/pages/login_page.py:28\n\nThe element may have been removed or its selector changed.",
        "Element not found: css=.program-card-title\nExpected at least 1 matching element, got 0.\n\n  at step_impl/program_steps.py:55\n  File \"features/steps/program_steps.py\", line 55, in step_impl",
        "locator.click: Error: locator('.ticket-row >> nth=0 >> .status-badge') resolved to 0 elements\n\nThe page layout may have changed. Check if '.ticket-row' still exists in the DOM.",
        "NoSuchElementException: Unable to locate element: #export-btn\nThe element selector has changed after the recent UI redesign.",
    ],
    "Timeout": [
        "Timeout 30000ms exceeded.\n\n  at page.wait_for_selector('.loading-spinner', state='hidden')\n\nThe page took too long to finish loading. This may be an environment performance issue.",
        "TimeoutError: Timeout 15000ms exceeded while waiting for page.goto('https://anticket.lengliwh.com/programs')\n\nNavigation timeout — the server may be slow or unresponsive.",
        "Timeout 10000ms exceeded.\n\n  at locator.wait_for(state='visible')\n  locator('.modal-dialog')\n\nThe modal did not appear within the expected time.",
    ],
    "AssertionFailed": [
        "AssertionError: Expected page title to contain 'Program List' but got 'Error 500 - Internal Server Error'\n\n  at step_impl/program_steps.py:78\n  assert 'Program List' in page.title()",
        "AssertionError: Expected 5 items in the list but got 3\n\n  at step_impl/ticket_steps.py:44\n  assert len(items) == expected_count\n\nThe number of records returned does not match the expected value.",
        "AssertionError: Status code 200 != 401\n\n  at step_impl/api_steps.py:32\n  assert response.status_code == 200\n\nThe API returned 401 Unauthorized instead of 200 OK.",
        "AssertionError: Expected user role 'admin' but got 'viewer'\n\n  at step_impl/user_steps.py:65\n  assert user_data['role'] == 'admin'",
    ],
    "NetworkError": [
        "ConnectionError: HTTPSConnectionPool(host='anticket.lengliwh.com', port=443): Max retries exceeded\n\nCaused by: NewConnectionError('<urllib3.connection.HTTPSConnection>: Failed to establish a new connection: [Errno 111] Connection refused')",
        "net::ERR_CONNECTION_REFUSED at https://anticket.lengliwh.com/api/v1/programs\n\nThe backend service may be down or unreachable from the test environment.",
        "requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))",
    ],
    "PageNavigation": [
        "page.goto: net::ERR_NAME_NOT_RESOLVED at https://anticket-staging.lengliwh.com/login\n\nThe hostname could not be resolved. Check the environment URL configuration.",
        "Navigation failed because page was closed.\n\n  at page.goto('https://anticket.lengliwh.com/tickets')\n\nThe browser context was closed before navigation completed.",
    ],
    "Authentication": [
        "Authentication failed: POST /api/v1/login returned 401\n\nResponse: {\"error\": \"Invalid credentials\"}\n\nThe test user credentials may have been reset or expired.",
        "Token expired during test execution.\n\nThe access token obtained at the start of the test became invalid before the test completed. Consider refreshing the token mid-test.",
    ],
}


def seed():
    """Insert mock data into the database."""
    init_db()
    db = get_db()

    try:
        # Check if data already exists
        existing = db.query(TestRun).count()
        if existing > 5:
            print(f"Database already has {existing} runs. Skipping seed.")
            print("To reseed, delete dashboard/backend/dashboard.db first.")
            return

        now = datetime.utcnow()
        runs_to_create = 20

        for i in range(runs_to_create):
            # Spread runs over the last 30 days
            days_ago = 30 - (i * 30 // runs_to_create)
            hours = random.randint(8, 18)
            run_time = now - timedelta(days=days_ago, hours=random.randint(0, 12))
            run_time = run_time.replace(hour=hours, minute=random.randint(0, 59))

            # Gradually increase the number of scenarios (team writes more tests)
            base_count = 8 + (i * 12 // runs_to_create)  # 8 → 20
            scenario_count = min(base_count + random.randint(-1, 2), len(SCENARIOS))
            selected_scenarios = SCENARIOS[:scenario_count]

            env = random.choice(["local", "local", "local", "sit", "sit", "uat"])
            tags = random.choice([None, "@smoke", "@hybrid", "@antank", "@api,@ui"])

            # Determine pass rate for this run (generally improving over time)
            base_pass_rate = 0.65 + (i / runs_to_create) * 0.25  # 65% → 90%
            # Add some randomness
            pass_rate = min(max(base_pass_rate + random.uniform(-0.15, 0.1), 0.4), 1.0)

            # Create the run
            duration_total = 0
            scenario_results = []

            for feature, name, sc_tags, is_flaky in selected_scenarios:
                # Determine status
                r = random.random()
                if is_flaky and random.random() < 0.4:
                    # Flaky tests fail ~40% of the time
                    status = "failed"
                elif r > pass_rate:
                    status = random.choice(["failed", "failed", "failed", "skipped"])
                else:
                    status = "passed"

                # Duration
                if status == "passed":
                    dur = random.uniform(1.0, 8.0)
                elif status == "failed":
                    dur = random.uniform(2.0, 15.0)  # Failed tests often take longer (timeouts)
                else:
                    dur = random.uniform(0.1, 0.5)

                duration_total += dur

                # Error message for failed scenarios
                error_msg = None
                if status == "failed":
                    # Pick error category based on what makes sense
                    if is_flaky:
                        cat = random.choice(["Timeout", "SelectorChanged"])
                    elif "api" in sc_tags.lower():
                        cat = random.choice(["NetworkError", "AssertionFailed", "Authentication"])
                    elif "ui" in sc_tags.lower():
                        cat = random.choice(["SelectorChanged", "SelectorChanged", "Timeout", "PageNavigation"])
                    else:
                        cat = random.choice(["SelectorChanged", "Timeout", "AssertionFailed"])

                    if cat in ERRORS:
                        error_msg = random.choice(ERRORS[cat])

                scenario_results.append({
                    "feature": feature,
                    "name": name,
                    "status": status,
                    "duration_s": round(dur, 3),
                    "error_msg": error_msg,
                    "tags": sc_tags,
                })

            passed = sum(1 for s in scenario_results if s["status"] == "passed")
            failed = sum(1 for s in scenario_results if s["status"] == "failed")
            skipped = sum(1 for s in scenario_results if s["status"] == "skipped")
            total = len(scenario_results)

            run_status = "passed" if failed == 0 else "failed"
            run_duration = timedelta(seconds=duration_total + random.uniform(5, 15))

            run = TestRun(
                started_at=run_time,
                finished_at=run_time + run_duration,
                status=run_status,
                env=env,
                tags=tags,
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
            )
            db.add(run)
            db.flush()

            for s in scenario_results:
                db.add(TestScenario(
                    run_id=run.id,
                    feature=s["feature"],
                    name=s["name"],
                    status=s["status"],
                    duration_s=s["duration_s"],
                    error_msg=s["error_msg"],
                    tags=s["tags"],
                ))

            print(f"  Run #{run.id}: {env:5s} | {total} scenarios | "
                  f"{passed}P {failed}F {skipped}S | {run_status}")

        db.commit()
        print(f"\nSeeded {runs_to_create} test runs successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
