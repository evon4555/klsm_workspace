"""Pytest fixtures shared by the API smoke / contract / functional layers.

What it provides:
  * `endpoints_registry` 鈥?loads 02-tests/api/data/*_endpoints.yml as dicts.
  * `http`               鈥?a requests.Session with sensible defaults.
  * `smoke_results`      鈥?collector that writes a JSON sidecar after the
                           session, consumed by the dashboard backend's
                           /api/api-monitor/endpoints route.

The JSON sidecar lives at:
  07-artifacts/api_smoke/latest.json

Schema:
  {
    "project": "瑗夸節",
    "website_url": "https://anticket.lengliwh.com",
    "ran_at": "2026-05-28T15:30:00Z",
    "summary": {"total": 25, "up": 24, "degraded": 1, "down": 0},
    "endpoints": [
      {"name": "...", "path": "...", "method": "GET",
       "auth_required": false, "expected_status": [200],
       "status": "up|degraded|down|skipped",
       "actual_status_code": 200, "latency_ms": 134,
       "group": "auth", "notes": "...", "last_check": "..."}
    ]
  }
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import time
import warnings
from pathlib import Path
from typing import Any

import pytest
import requests
import urllib3
import yaml

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

# Repo-relative paths so the suite is portable.
_THIS = Path(__file__).resolve()
_AUTOMATION = _THIS.parents[2]
_DATA_DIR = _THIS.parent / "data"
_ARTIFACT_DIR = _AUTOMATION / "07-artifacts" / "api_smoke"
_LAYER_SUMMARY = _ARTIFACT_DIR / "layer_summary.json"
_QA_REPORTS: dict[str, dict[str, Any]] = {}
_QA_SESSION_STARTED_AT: _dt.datetime | None = None
_QA_RUN_TOKEN = ""

# Latency thresholds (ms) for the smoke verdict.
_SLOW_MS = 1000
_TIMEOUT_S = 8.0

# Where the crawler saved the post-login Playwright session.
_STATE_PATH = _ARTIFACT_DIR / "storage_state.json"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "filterwarnings",
        "ignore:Unverified HTTPS request.*:urllib3.exceptions.InsecureRequestWarning",
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    """Start a fresh result bucket for this pytest process."""
    global _QA_SESSION_STARTED_AT, _QA_RUN_TOKEN
    _QA_REPORTS.clear()
    _QA_SESSION_STARTED_AT = _dt.datetime.now(_dt.timezone.utc)
    _QA_RUN_TOKEN = f"{_QA_SESSION_STARTED_AT.strftime('%Y%m%dT%H%M%S%fZ')}-{os.getpid()}"


# ---------------------------------------------------------------------------
# Registry loader
# ---------------------------------------------------------------------------
def _load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def endpoints_registry() -> dict[str, Any]:
    """Loads the 瑗夸節 endpoint registry (wk_endpoints.yml). Add more projects
    by reading their own yml and merging here."""
    return _load_registry(_DATA_DIR / "wk_endpoints.yml")


@pytest.fixture(scope="session")
def base_url(endpoints_registry: dict[str, Any]) -> str:
    """Allow override via env var (useful for staging / mirror URLs)."""
    return os.environ.get("WK_API_BASE_URL", endpoints_registry["website_url"]).rstrip("/")


# ---------------------------------------------------------------------------
# HTTP session 鈥?keep-alive across the whole session
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def http() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        # 瑗夸節 backend rejects calls without these 鈥?observed in HAR by the
        # crawler. cmpappkey is the customer-app identifier; lang drives i18n;
        # Referer is the site-origin anti-CSRF gate. Without cmpappkey the
        # server returns 200 + body {errcode:"1101", success:false} (the
        # classic "200 OK lying" pattern) so smoke would false-pass.
        "User-Agent": "qa-harness/api-smoke (+https://github.com/qa-harness)",
        "Accept": "application/json, text/plain, */*",
        "cmpappkey": "ShanghaiCS",
        "lang": "en",
        "Referer": "https://anticket.lengliwh.com/websitehtml/index.html",
    })
    # We don't verify TLS for internal cert chains.
    s.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return s


# ---------------------------------------------------------------------------
# Result collector 鈫?JSON sidecar
# ---------------------------------------------------------------------------
class _Collector:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def record(self, **row: Any) -> None:
        row["last_check"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        self.rows.append(row)


@pytest.fixture(scope="session")
def smoke_results() -> _Collector:
    return _Collector()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """After the whole pytest session:
      1. flush the L0 smoke rows to latest.json (per-endpoint detail)
      2. write a per-layer summary to layer_summary.json (dashboard
         consumes this to show one card per L0/L1/L2/L3)
    """
    # ---------- L0 smoke detail ----------
    collector: _Collector | None = getattr(session, "_qa_smoke_collector", None)
    if collector is not None and collector.rows:
        _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        out = _ARTIFACT_DIR / "latest.json"
        summary = {
            "total": len(collector.rows),
            "up": sum(1 for r in collector.rows if r["status"] == "up"),
            "degraded": sum(1 for r in collector.rows if r["status"] == "degraded"),
            "down": sum(1 for r in collector.rows if r["status"] == "down"),
            "skipped": sum(1 for r in collector.rows if r["status"] == "skipped"),
        }
        payload = {
            "project": collector.rows[0].get("project", ""),
            "website_url": collector.rows[0].get("website_url", ""),
            "ran_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "summary": summary,
            "endpoints": collector.rows,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[api-smoke] wrote {out}  ({summary['up']} up / {summary['down']} down / "
              f"{summary['degraded']} slow / {summary['skipped']} skipped)")

    # ---------- per-layer summary ----------
    # Directory-level model:
    #   api_smoke      - single-endpoint status/latency monitoring
    #   api_contract   - response shape / schema checks
    #   api_functional - API-only multi-step business checks
    #   api_ui_mixed   - API chains plus final UI assertions
    layer_counts: dict[str, dict[str, int]] = {}
    dashboard_tests: list[dict[str, Any]] = []
    for item in session.items:
        layer = _api_layer(item.nodeid)
        if not layer:
            continue
        result = _QA_REPORTS.get(item.nodeid, {
            "status": "error",
            "duration_s": 0.0,
            "error_msg": "pytest did not emit a result report",
        })
        status = result["status"]
        b = layer_counts.setdefault(
            layer,
            {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "total": 0},
        )
        b["total"] += 1
        b[status] = b.get(status, 0) + 1
        dashboard_tests.append({
            "case_id": _api_case_id(item, layer),
            "name": _api_display_name(item),
            "layer": layer,
            "status": status,
            "duration_s": result.get("duration_s", 0.0),
            "error_msg": result.get("error_msg"),
            "source": item.nodeid.replace("\\", "/"),
        })

    if layer_counts:
        out = _LAYER_SUMMARY
        ordering = ["api_smoke", "api_contract", "api_functional", "api_ui_mixed"]
        payload = {
            "ran_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "layers": [
                {"name": name, **counts}
                for name, counts in sorted(layer_counts.items(),
                                           key=lambda kv: ordering.index(kv[0]))
            ],
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        parts = [f"{l['name']}={l['passed']}/{l['total']}" for l in payload["layers"]]
        print(f"[api-smoke] wrote {out}  ({', '.join(parts)})")

    if dashboard_tests:
        _publish_dashboard_run(dashboard_tests)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Capture call results plus setup-level skips/errors.

    The previous autouse-fixture collector never resumed when a session
    fixture skipped a test, which made 6 collected API cases disappear from
    the dashboard summary. Report hooks receive those outcomes reliably.
    """
    current = _QA_REPORTS.get(report.nodeid)
    if report.when == "setup" and report.outcome in {"failed", "skipped"}:
        _QA_REPORTS[report.nodeid] = {
            "status": "error" if report.failed else "skipped",
            "duration_s": float(report.duration or 0.0),
            "error_msg": _report_message(report),
        }
    elif report.when == "call":
        status = "failed" if report.failed else ("skipped" if report.skipped else "passed")
        _QA_REPORTS[report.nodeid] = {
            "status": status,
            "duration_s": float(report.duration or 0.0),
            "error_msg": _report_message(report) if status != "passed" else None,
        }
    elif report.when == "teardown" and report.failed:
        duration = float(report.duration or 0.0) + float((current or {}).get("duration_s", 0.0))
        _QA_REPORTS[report.nodeid] = {
            "status": "error",
            "duration_s": duration,
            "error_msg": _report_message(report),
        }


def _api_layer(nodeid: str) -> str | None:
    node = nodeid.replace("\\", "/")
    allowed = ("api_smoke", "api_contract", "api_functional", "api_ui_mixed")
    for layer in allowed:
        if f"/{layer}/" in f"/{node}":
            return layer
    return None


def _api_case_id(item: pytest.Item, layer: str) -> str:
    import re

    raw_name = item.name
    sit_match = re.search(r"sit_tc_([a-z0-9_]+?)_(\d{3})(?:_|$)", raw_name, re.IGNORECASE)
    if sit_match:
        module = sit_match.group(1).replace("_", "-").upper()
        return f"SIT-TC-{module}-{sit_match.group(2)}"

    param = raw_name.split("[", 1)[1].rsplit("]", 1)[0] if "[" in raw_name else ""
    logical = param or raw_name.removeprefix("test_")
    logical = re.sub(r"[^A-Za-z0-9._:/-]+", "-", logical).strip("-").upper()
    return f"{layer.replace('_', '-').upper()}::{logical}"


def _api_display_name(item: pytest.Item) -> str:
    import re

    raw_name = item.name
    if "[" in raw_name:
        param = raw_name.split("[", 1)[1].rsplit("]", 1)[0]
        return param.replace("_", " ")[:200]
    return re.sub(r"\s+", " ", raw_name.removeprefix("test_").replace("_", " ")).strip()[:200]


def _report_message(report: pytest.TestReport) -> str | None:
    text = getattr(report, "longreprtext", "") or str(getattr(report, "longrepr", "") or "")
    text = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
    return text[-4000:] or None


def _publish_dashboard_run(tests: list[dict[str, Any]]) -> None:
    """Best-effort local publish; test success never depends on the UI."""
    finished_at = _dt.datetime.now(_dt.timezone.utc)
    started_at = _QA_SESSION_STARTED_AT or finished_at
    payload = {
        "project": os.environ.get("QA_DASHBOARD_PROJECT", "west-kowloon"),
        "env": os.environ.get("ENV", "sit"),
        "run_token": _QA_RUN_TOKEN or f"pytest-{os.getpid()}",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "tests": tests,
    }
    base_url = os.environ.get("QA_DASHBOARD_URL", "http://127.0.0.1:8002").rstrip("/")
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.post(f"{base_url}/api/runs/import-api", json=payload, timeout=10)
        response.raise_for_status()
        body = response.json()
        action = "imported" if body.get("imported") else "already present"
        print(f"[api-test-run] {action} as dashboard run #{body.get('id')}")
    except Exception as exc:
        warnings.warn(f"API results were not published to the local dashboard: {exc}")
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def _attach_collector(request: pytest.FixtureRequest, smoke_results: _Collector) -> None:
    """Hook the collector onto the session so pytest_sessionfinish can find it."""
    request.session._qa_smoke_collector = smoke_results  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Helpers exported to tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def smoke_thresholds() -> dict[str, float]:
    return {"slow_ms": _SLOW_MS, "timeout_s": _TIMEOUT_S}


# ---------------------------------------------------------------------------
# Authenticated HTTP 鈥?reuses the cookie jar saved by
# 04-tools/crawl_api_endpoints.py (storage_state.json).
#
# This is the API+UI Mix pattern in two lines: Playwright logs in once,
# saves cookies; pytest+requests picks them up here and hits APIs with the
# same session. No re-login needed (until the cookie expires).
# ---------------------------------------------------------------------------
def _load_cookies_from_state(http: requests.Session, base_url: str) -> int:
    state = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    site_host = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    n = 0
    # Clear any stale cookies from a previous load.
    http.cookies.clear()
    for c in state.get("cookies", []):
        if site_host in (c.get("domain") or "").lstrip("."):
            http.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
            n += 1
    return n


def _session_is_alive(http: requests.Session, base_url: str) -> bool:
    """Quick liveness ping. Backend returns body.success=false +
    errcode='1205' (or similar) when the session is expired even though
    HTTP status is 200."""
    try:
        r = http.post(base_url + "/ucenter/rest/getLogonInfo.xhtml", timeout=8)
        body = r.json()
        return body.get("errcode") == "0000" and body.get("data") is not None
    except Exception:
        return False


def _refresh_session_via_crawler(base_url: str) -> None:
    """Re-run the Playwright login flow to overwrite storage_state.json."""
    import os, sys

    sys.path.insert(0, str(_AUTOMATION / "04-tools"))
    from crawl_api_endpoints import login_and_save_state
    email = os.environ.get("TA_WEBSITE_USERNAME")
    password = os.environ.get("TA_WEBSITE_PASSWORD")
    if not (email and password):
        raise RuntimeError(
            "session expired and TA_WEBSITE_USERNAME / TA_WEBSITE_PASSWORD "
            "not set 鈥?cannot auto-refresh"
        )
    print("[authed_http] session expired 鈥?re-running headless login")
    login_and_save_state(base_url, email, password)


@pytest.fixture(scope="session")
def authed_http(http: requests.Session, base_url: str) -> requests.Session:
    """Logged-in requests.Session backed by Playwright's storage_state.json.

    If the cached session has expired (errcode 1205), automatically re-runs
    the headless login flow to refresh 鈥?one extra captcha solve, then
    everything continues. Skips the test if no credentials are configured
    and no fresh session can be obtained.
    """
    # Load env so re-login has TA_WEBSITE_* available.
    env_name = os.environ.get("ENV", "sit")
    env_file = _AUTOMATION / "06-envs" / f".env.{env_name}"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    if not _STATE_PATH.exists():
        try:
            _refresh_session_via_crawler(base_url)
        except Exception as exc:
            pytest.skip(f"no storage_state.json and refresh failed: {exc}")

    n = _load_cookies_from_state(http, base_url)
    print(f"\n[authed_http] loaded {n} cookies from {_STATE_PATH.name}")

    if not _session_is_alive(http, base_url):
        try:
            _refresh_session_via_crawler(base_url)
            n = _load_cookies_from_state(http, base_url)
            print(f"[authed_http] post-refresh: loaded {n} cookies")
            if not _session_is_alive(http, base_url):
                pytest.skip("authed_http: session still not alive after refresh")
        except Exception as exc:
            pytest.skip(f"authed_http: session expired and refresh failed: {exc}")

    return http
