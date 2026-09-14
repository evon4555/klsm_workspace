"""
Behave environment hooks — lifecycle callbacks for the BDD test suite.

This file replaces pytest's conftest.py for the Behave layer.
Behave calls these functions automatically at the right moment:

  before_all(context)          → once at the very start (load settings, configure logging)
  after_all(context)           → once after the last scenario (finalize dashboard run)
  before_scenario(context, s)  → before every Scenario (start Playwright browser)
  after_scenario(context, s)   → after every Scenario (close browser + record result)

The `context` object is Behave's shared state bag — anything you attach here
(e.g. context.page, context.program_page) is available inside step definitions.

--- Three test modes (all use Playwright) ---

  @ui      Pure browser interaction — click, fill, assert UI elements
  @api     API calls via page.request (Playwright built-in HTTP client, no httpx needed)
  @hybrid  API for fast setup/login + UI for real user-facing assertions  ← primary mode

All three modes use a Playwright Page object:
  - UI steps    use  context.page  (browser actions)
  - API steps   use  context.page.request  (shares the same session cookie as the browser)
  - Hybrid uses both in the same scenario

--- Dashboard sync ---

Every CLI behave session is auto-recorded into the harness dashboard database
so the dashboard UI sees its results. When the dashboard's own BehaveRunner
launches behave (it sets BEHAVE_DASHBOARD_RUN_ID), we skip our own recording
to avoid duplicate rows.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings
from test_automation.logging import configure_logging

def _candidate_roots() -> list[Path]:
    starts = [
        Path.cwd().absolute(),
        Path.cwd().resolve(),
        Path(__file__).absolute(),
        Path(__file__).resolve(),
    ]
    candidates: list[Path] = []
    for start in starts:
        candidates.append(start)
        candidates.extend(start.parents)
    return candidates


def _find_dashboard_db() -> Path:
    """Resolve dashboard.db in the numbered workspace layout."""
    roots: list[Path] = []
    if os.environ.get("QA_HARNESS_ROOT"):
        roots.append(Path(os.environ["QA_HARNESS_ROOT"]).expanduser())
    if os.environ.get("QA_WORKSPACE_ROOT"):
        roots.append(Path(os.environ["QA_WORKSPACE_ROOT"]).expanduser() / "qa-harness")
    roots.extend(_candidate_roots())

    for root in roots:
        candidates = [
            root / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

    workspace_root = Path(os.environ.get("QA_WORKSPACE_ROOT", "D:/Workspace"))
    return workspace_root / "qa-harness" / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db"


_DASHBOARD_DB = _find_dashboard_db()


def _dashboard_should_record() -> bool:
    """True if this behave session should write its own test_runs row.

    Skip when:
    - BEHAVE_DASHBOARD_RUN_ID is set (dashboard's BehaveRunner handles recording).
    - dashboard.db doesn't exist (no dashboard installed; nothing to write to).
    """
    if os.environ.get("BEHAVE_DASHBOARD_RUN_ID"):
        return False
    return _DASHBOARD_DB.exists()


def _dashboard_create_run() -> int | None:
    """Insert a test_runs row in 'running' state and return its id."""
    env = os.environ.get("ENV", "local")
    started_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    con = sqlite3.connect(str(_DASHBOARD_DB))
    try:
        cur = con.execute(
            "INSERT INTO test_runs "
            "(started_at, status, env, total, passed, failed, skipped) "
            "VALUES (?, 'running', ?, 0, 0, 0, 0)",
            (started_at, env),
        )
        run_id = cur.lastrowid
        con.commit()
        print(f"  [dashboard-sync] created test_runs id={run_id} env={env}")
        return run_id
    finally:
        con.close()


def _dashboard_record_scenario(run_id: int, scenario) -> None:
    """Insert a test_scenarios row for a finished scenario."""
    duration = sum(getattr(s, "duration", 0.0) or 0.0 for s in scenario.steps)
    err_msg = ""
    for step in scenario.steps:
        if step.status.name == "failed" if hasattr(step.status, "name") else step.status == "failed":
            em = step.error_message or ""
            err_msg = em if isinstance(em, str) else "\n".join(em)
            break
    feature_name = scenario.feature.name if scenario.feature else ""
    tags = ",".join(scenario.effective_tags) if scenario.effective_tags else ""
    status = scenario.status.name if hasattr(scenario.status, "name") else str(scenario.status)
    con = sqlite3.connect(str(_DASHBOARD_DB))
    try:
        con.execute(
            "INSERT INTO test_scenarios "
            "(run_id, feature, name, status, duration_s, error_msg, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, feature_name, scenario.name, status, duration, err_msg, tags),
        )
        con.commit()
    finally:
        con.close()


def _dashboard_finalize_run(run_id: int) -> None:
    """Update test_runs aggregate counts + final status + finished_at.

    Run-level status convention:
      - "passed"  iff every scenario passed (no failed, no error, no untested)
      - "failed"  otherwise — including any 'error' (exception/setup crash) or
                  'untested' (step matched nothing) status, not just 'failed'
                  assertions.

    The error/untested classes used to be silently treated as success because
    only 'failed' was inspected; that hid real test breakage. See
    [[feedback_self_smoke_before_done]] for the audit trail.
    """
    finished_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    con = sqlite3.connect(str(_DASHBOARD_DB))
    try:
        cur = con.execute(
            "SELECT status, COUNT(*) FROM test_scenarios WHERE run_id = ? GROUP BY status",
            (run_id,),
        )
        counts = {row[0]: row[1] for row in cur.fetchall()}
        total = sum(counts.values())
        passed = counts.get("passed", 0)
        failed = counts.get("failed", 0)
        errored = counts.get("error", 0) + counts.get("untested", 0) + counts.get("undefined", 0)
        skipped = counts.get("skipped", 0)
        run_status = "passed" if (total > 0 and failed == 0 and errored == 0) else "failed"
        # 'failed' and 'errored' are stored separately so the dashboard
        # distinguishes product bugs (failed = real assertion mismatch) from
        # test/infra issues (errored = Playwright timeout, undefined step,
        # setup crash). Both still count toward a non-passed run status.
        con.execute(
            "UPDATE test_runs SET finished_at=?, status=?, total=?, passed=?, "
            "failed=?, errored=?, skipped=? WHERE id=?",
            (finished_at, run_status, total, passed, failed, errored, skipped, run_id),
        )
        con.commit()
        print(f"  [dashboard-sync] finalized run #{run_id}: "
              f"total={total} passed={passed} failed={failed} errored={errored} "
              f"skipped={skipped} -> {run_status}")
    finally:
        con.close()


def _warm_up_sit(antank_url: str) -> None:
    """Pre-warm the SIT SPA before any scenario runs.

    2026-06-12: SIT cold-start can take 40-70s for the Vue/SPA to render its
    login/register inputs after nginx Basic Auth round-trip. Without warm-up,
    the FIRST scenario in each behave session reliably errors at selector
    timeout, even with 60s waits. A single up-front GET serializes that cost
    once instead of paying it in the middle of an actual scenario.
    """
    import urllib.request, urllib.error, ssl, base64, os
    user = os.environ.get("WK_BASIC_AUTH_USER")
    pw = os.environ.get("WK_BASIC_AUTH_PASS")
    headers = {}
    if user and pw:
        token = base64.b64encode(f"{user}:{pw}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for path in ("/websitehtml/index.html#/login", "/websitehtml/index.html#/register"):
        try:
            req = urllib.request.Request(f"{antank_url.rstrip('/')}{path}", headers=headers)
            urllib.request.urlopen(req, timeout=15, context=ctx).read(128)
        except Exception as exc:
            print(f"  [warm-up] {path} -> {type(exc).__name__}: {exc}")


def before_all(context):
    """One-time setup: configure logging and load environment settings.

    Settings are read from 06-envs/.env.<ENV> where ENV defaults to 'local'.
    Switch environments via:  ENV=sit behave 01-features/
    """
    configure_logging()
    context.settings = get_settings()
    if os.environ.get("ENV", "").lower() == "sit":
        try:
            _warm_up_sit(str(context.settings.antank_url))
            print("  [warm-up] SIT pre-warmed")
        except Exception as exc:
            print(f"  [warm-up] failed (continuing): {exc}")
    # Dashboard sync: open a new test_runs row unless the dashboard's own
    # BehaveRunner is the caller (it sets BEHAVE_DASHBOARD_RUN_ID and does
    # its own recording).
    if _dashboard_should_record():
        try:
            context._dashboard_run_id = _dashboard_create_run()
        except Exception as exc:
            print(f"  [dashboard-sync] before_all failed (continuing): {exc}")
            context._dashboard_run_id = None
    else:
        context._dashboard_run_id = None


def after_all(context):
    """Finalize the dashboard test_runs row at the end of the session."""
    run_id = getattr(context, "_dashboard_run_id", None)
    if not run_id:
        return
    try:
        _dashboard_finalize_run(run_id)
    except Exception as exc:
        print(f"  [dashboard-sync] after_all failed: {exc}")


def before_scenario(context, scenario):
    """Per-scenario setup: start a fresh Playwright browser for every scenario.

    A new browser page is created per scenario so tests are fully isolated —
    cookies, local storage, and browser state do not leak between scenarios.

    headless=True  → recommended for CI (no visible window)
    headless=False → change locally to watch the browser while debugging

    Scenarios tagged @na document a manual test case that cannot be executed
    by pure-UI automation (e.g. it needs a real email-OTP inbox, or the UI
    control the case assumes does not exist). They are kept in the feature
    file for 1:1 traceability but skipped here; their Not-Applicable status
    and evidence screenshots are recorded in the Kasi workbook by
    tools/update_evidence.py instead.
    """
    if "na" in scenario.tags:
        scenario.skip("NA — not executable by automation; "
                      "see the feature header and tools/update_evidence.py")
        return
    # Scenarios tagged @needs-oauth-mock require a Google/Facebook/X/TikTok/
    # WeChat OAuth provider mock that the harness does not yet host. Skip
    # the whole scenario before opening a browser so the dashboard shows
    # them as Skipped (= "blocked on infra") rather than Failed (= "broken").
    # Setting OAUTH_MOCK_URL lifts the skip; see
    # 01-system/10-change-management.md and antank_third_party_login.feature.
    if "needs-oauth-mock" in scenario.tags and not os.environ.get("OAUTH_MOCK_URL"):
        scenario.skip("@needs-oauth-mock — OAUTH_MOCK_URL is not set; "
                      "OAuth provider mock not yet hosted by the harness")
        return
    context._playwright = sync_playwright().start()
    context.browser = context._playwright.chromium.launch(headless=True)
    # SIT website got a nginx HTTP Basic Auth layer 2026-06-11. If creds are
    # supplied via WK_BASIC_AUTH_USER + WK_BASIC_AUTH_PASS, pass them through
    # to the browser context so navigations don't hit a 401. No-op when unset.
    _basic_user = os.environ.get("WK_BASIC_AUTH_USER")
    _basic_pass = os.environ.get("WK_BASIC_AUTH_PASS")
    _new_page_kwargs = {}
    if _basic_user and _basic_pass:
        _new_page_kwargs["http_credentials"] = {
            "username": _basic_user, "password": _basic_pass,
        }
    context.page    = context.browser.new_page(**_new_page_kwargs)


def after_scenario(context, scenario):
    """Per-scenario teardown: close browser, release Playwright, record result."""
    shot_dir = os.environ.get("QA_SHOT_DIR")
    if shot_dir and hasattr(context, "page"):
        try:
            Path(shot_dir).mkdir(parents=True, exist_ok=True)
            tc = ""
            for word in scenario.name.split():
                if word.startswith("SIT-TC-") or word.startswith("UAT-TC-"):
                    tc = word
                    break
            status = "fail" if scenario.status.name != "passed" else "pass"
            fname = f"{tc or scenario.name[:30]}-{status}-{datetime.now().strftime('%Y-%m-%d')}.png"
            context.page.screenshot(path=str(Path(shot_dir) / fname), full_page=False)
        except Exception as exc:
            print(f"  [shot] capture failed: {exc}")
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "_playwright"):
        context._playwright.stop()
    run_id = getattr(context, "_dashboard_run_id", None)
    if run_id:
        try:
            _dashboard_record_scenario(run_id, scenario)
        except Exception as exc:
            print(f"  [dashboard-sync] scenario insert failed (continuing): {exc}")
