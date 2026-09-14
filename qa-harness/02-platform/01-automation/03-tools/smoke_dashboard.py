"""smoke_dashboard.py - end-to-end self-test for the qa-harness stack.

Run this AFTER any change to 02-platform/02-dashboard,
02-platform/01-automation, west-kowloon/02-automation/01-features,
west-kowloon/02-automation/03-src, or 02-platform/03-infra.

Exits 0 if every check passes. Non-zero otherwise. Prints a SUMMARY line
that you can paste into a reply.

Total runtime: ~90 seconds (most of it spent waiting for a tiny Locust run).

Invocation:
    cd D:\\Workspace\\qa-harness
    .\\02-platform\\01-automation\\.venv\\Scripts\\python.exe 02-platform\\01-automation\\03-tools\\smoke_dashboard.py
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _looks_like_numbered_root(path: Path) -> bool:
    return (
        (path / "01-system").is_dir()
        and (path / "02-platform" / "01-automation").is_dir()
        and (path / "02-platform" / "02-dashboard").is_dir()
    )


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


def find_repo_root() -> Path:
    override = os.getenv("QA_HARNESS_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    for candidate in _candidate_roots():
        if _looks_like_numbered_root(candidate):
            return candidate.resolve()

    raise RuntimeError(
        "Cannot locate qa-harness root. Set QA_HARNESS_ROOT to the root "
        "containing 01-system and 02-platform."
    )


REPO_ROOT = find_repo_root()
AUTOMATION_ROOT = REPO_ROOT / "02-platform" / "01-automation"
DASHBOARD_ROOT = REPO_ROOT / "02-platform" / "02-dashboard"
WORKSPACE_ROOT = Path(os.environ.get("QA_WORKSPACE_ROOT", REPO_ROOT.parent)).resolve()
WESTK_ROOT = Path(os.environ.get("QA_WESTK_ROOT", WORKSPACE_ROOT / "west-kowloon")).resolve()
PROJECT_AUTOMATION_ROOT = WESTK_ROOT / "02-automation"
DASHBOARD_DB = DASHBOARD_ROOT / "01-backend" / "dashboard.db"
PYTHON_EXE = AUTOMATION_ROOT / ".venv" / "Scripts" / "python.exe"

BACKEND = "http://127.0.0.1:8002"
FRONTEND = "http://127.0.0.1:5174"
PROMETHEUS = "http://127.0.0.1:9090"
GRAFANA = "http://127.0.0.1:3000"
LOCUST = "http://127.0.0.1:9646"
SMOKE_FEATURE = os.environ.get(
    "QA_SMOKE_FEATURE", "01-features/ui_e2e/antank_forgot_password.feature"
)
SMOKE_SCENARIO_NAME = os.environ.get(
    "QA_SMOKE_SCENARIO_NAME", "SIT-TC-WEB-AUTH-070 "
)
PERF_HOST = os.environ.get("QA_PERF_HOST", "https://anticket.lengliwh.com")
PERF_LOCUSTFILE = os.environ.get(
    "QA_PERF_LOCUSTFILE", "02-tests/performance/locustfile.py"
)

PROM_DS_UID = "PBFA97CFB590B2093"  # Grafana datasource UID for Prometheus

results: list[tuple[str, bool, str]] = []   # (name, passed, detail)


def check(name: str, passed: bool, detail: str = "") -> None:
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))
    results.append((name, passed, detail))


def port_up(port: int, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except OSError:
        return False


def http_get(url: str, timeout: float = 5.0, basic_auth: str = "") -> tuple[int, str]:
    """Return (status_code, body_text). 0 status on connection error."""
    req = urllib.request.Request(url)
    if basic_auth:
        import base64
        req.add_header(
            "Authorization",
            "Basic " + base64.b64encode(basic_auth.encode()).decode(),
        )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception:
        return 0, ""


def http_post(url: str, body: dict, timeout: float = 10.0) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


# --------------------------------------------------------------------------
def phase_ports():
    print("\n=== Phase 1: ports listening ===")
    expected = {9090: "Prometheus", 3100: "Loki", 3000: "Grafana",
                8002: "Backend", 5174: "Frontend"}
    for p, name in expected.items():
        check(f"port {p} ({name})", port_up(p))


def phase_backend_routes():
    print("\n=== Phase 2: critical backend endpoints return 200 ===")
    routes = [
        "/api/perf/services",
        "/api/perf/status",
        "/api/perf/metrics",     # the NaN bug killed this one
        "/api/perf/grafana/panels",
        "/api/perf/report",
        "/api/runs",
        "/api/features",
        "/api/observability/status",
        "/api/evidence-status",
    ]
    for r in routes:
        code, _ = http_get(BACKEND + r, timeout=10)
        check(f"GET {r}", code == 200, f"HTTP {code}")


def phase_grafana_panel_urls():
    print("\n=== Phase 3: Grafana panel URLs are auto-refresh-able ===")
    code, body = http_get(BACKEND + "/api/perf/grafana/panels")
    if code != 200:
        check("grafana panels endpoint reachable", False, f"HTTP {code}")
        return
    data = json.loads(body)
    panels = data.get("panels", [])
    check("at least 1 panel returned", len(panels) > 0, f"{len(panels)} panels")
    for p in panels[:1]:
        url = p.get("url", "")
        check("panel URL contains refresh=", "refresh=" in url, url[:80])
        check("panel URL uses tight window (now-15m or shorter)",
              any(w in url for w in ("now-15m", "now-5m", "now-10m")),
              url[:80])


def phase_frontend():
    print("\n=== Phase 4: frontend serves + proxies ===")
    code, _ = http_get(FRONTEND, timeout=5)
    check("frontend /", code == 200, f"HTTP {code}")
    code, body = http_get(FRONTEND + "/api/runs", timeout=10)
    check("frontend /api/runs proxy", code == 200, f"HTTP {code}")


def phase_automation_sync():
    """Run one fast behave scenario and confirm dashboard.db sync is accurate.

    The point of this phase is to verify the dashboard-sync HOOK (every CLI
    behave run inserts a test_runs row with the right aggregate status), not
    that AUTH-070 itself passes — that scenario is occasionally flaky on
    SIT network. So we accept either passed or failed, as long as the row
    exists and its status accurately reflects what behave returned.
    """
    print("\n=== Phase 5: behave CLI -> dashboard.db sync ===")
    if not DASHBOARD_DB.exists():
        check("dashboard.db present", False, str(DASHBOARD_DB))
        return
    con = sqlite3.connect(str(DASHBOARD_DB))
    before = con.execute("SELECT MAX(id) FROM test_runs").fetchone()[0] or 0
    con.close()

    cmd = [
        str(PYTHON_EXE), "-m", "behave",
        "--no-capture", "--no-color",
        SMOKE_FEATURE,
        "--name", SMOKE_SCENARIO_NAME,
    ]
    env_var_env = {**os.environ, "ENV": "sit"}
    # Retry once on transient network failure so a SIT goto blip doesn't
    # red-light the smoke. The dashboard-sync hook still records both runs.
    for attempt in range(1, 3):
        proc = subprocess.run(
            cmd, cwd=str(PROJECT_AUTOMATION_ROOT),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=180, env=env_var_env,
        )
        if proc.returncode == 0:
            break
        print(f"    behave attempt {attempt}/2 returned exit={proc.returncode}; retrying")

    con = sqlite3.connect(str(DASHBOARD_DB))
    after = con.execute("SELECT MAX(id) FROM test_runs").fetchone()[0] or 0
    row_status = None
    row_passed = None
    row_failed = None
    if after > before:
        row = con.execute(
            "SELECT status, passed, failed FROM test_runs WHERE id=?", (after,),
        ).fetchone()
        row_status, row_passed, row_failed = row[0], row[1], row[2]
    con.close()
    check("new test_runs row inserted", after > before,
          f"id {before} -> {after}")
    # The CORE invariant for this phase: behave's exit code and the
    # dashboard-sync status must agree. If both pass, great. If both fail,
    # also fine — just means the sync correctly captured an environment
    # blip. Disagreement = real bug in the sync hook.
    consistent = (
        (proc.returncode == 0 and row_status == "passed") or
        (proc.returncode != 0 and row_status == "failed")
    )
    check("dashboard-sync status matches behave exit",
          consistent,
          f"behave exit={proc.returncode} db status={row_status} passed={row_passed} failed={row_failed}")


def phase_perf_chain():
    """Trigger a 20s Locust test; verify every link in the data flow."""
    print("\n=== Phase 6: perf chain Locust -> Prometheus -> Grafana ===")

    # Wait for any prior perf test to finish so we don't error on
    # "test already running" (e.g., from a previous smoke run).
    for _ in range(30):
        code, body = http_get(BACKEND + "/api/perf/status")
        if code == 200 and json.loads(body).get("status") != "running":
            break
        time.sleep(1)

    code, body = http_post(BACKEND + "/api/perf/run", {
        "host": PERF_HOST,
        "users": 2, "spawn_rate": 1, "duration": "20s",
        "locustfile": PERF_LOCUSTFILE,
    })
    started = code == 200 and "started" in body
    check("POST /api/perf/run accepted", started, f"HTTP {code}")
    if not started:
        return

    # Mid-flight (t ≈ 8s): every link should be live.
    time.sleep(8)
    check("Locust port 9646 listening", port_up(9646))

    # Prometheus target health
    code, body = http_get(PROMETHEUS + "/api/v1/targets")
    target_up = False
    if code == 200:
        targets = json.loads(body).get("data", {}).get("activeTargets", [])
        for t in targets:
            if t.get("labels", {}).get("job") == "locust":
                target_up = (t.get("health") == "up")
                break
    check("Prometheus target locust=up", target_up)

    # Grafana sees the data via datasource proxy
    q = urllib.parse.quote("sum(locust_request_count_total)")
    code, body = http_get(
        f"{GRAFANA}/api/datasources/proxy/uid/{PROM_DS_UID}/api/v1/query?query={q}",
        basic_auth="admin:admin",
    )
    total_via_grafana = "no data"
    if code == 200:
        result = json.loads(body).get("data", {}).get("result", [])
        if result:
            total_via_grafana = result[0]["value"][1]
    check("Grafana proxy returns locust data",
          total_via_grafana not in ("no data", "0"),
          f"total requests = {total_via_grafana}")

    # /api/perf/metrics didn't crash on partial data (the NaN bug class)
    code, _ = http_get(BACKEND + "/api/perf/metrics")
    check("perf/metrics 200 mid-run (no NaN crash)", code == 200, f"HTTP {code}")

    # Wait for test to finish naturally
    print("    waiting ~15s for the 20s test to auto-stop ...")
    time.sleep(15)
    code, body = http_get(BACKEND + "/api/perf/status")
    if code == 200:
        status = json.loads(body)
        check("perf test ended cleanly",
              status.get("status") in ("stopped", "completed", "failed"),
              f"status={status.get('status')} exit_code={status.get('exit_code')}")
        check("perf test produced requests",
              (status.get("total_requests") or 0) > 0,
              f"total_requests={status.get('total_requests')}")


def main() -> int:
    print(f"qa-harness smoke - {_dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"repo: {REPO_ROOT}")

    phase_ports()
    if not all(p for n, p, _ in results):
        print("\nABORTING: not all base services are up. Start them via "
              "start-all.bat then re-run.")
        return 2

    phase_backend_routes()
    phase_grafana_panel_urls()
    phase_frontend()
    phase_automation_sync()
    phase_perf_chain()

    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    failed = total - passed

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"SUMMARY: PASS - {passed}/{total} checks")
    else:
        print(f"SUMMARY: FAIL - {failed}/{total} checks failed")
        print("\nFailed checks:")
        for n, p, d in results:
            if not p:
                print(f"  - {n}  ({d})")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
