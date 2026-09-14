"""Performance Test routes and Locust report handling."""

import asyncio
import csv
import os
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from database import PerformanceRunConfig, TestRun, TestScenario, get_db


router = APIRouter()


def configure_router(
    *,
    project_key,
    automation_paths,
    workspace_root,
    metrics_client_instance,
    metrics_config_instance,
    perf_artifact_prefix,
    perf_log_limit,
    perf_state_ref,
    as_float,
    as_int,
):
    global _project_key, _automation_paths, _workspace_root
    global metrics_client, metrics_config
    global PERF_ARTIFACT_PREFIX, PERF_LOG_LIMIT, perf_state
    global _as_float, _as_int
    _project_key = project_key
    _automation_paths = automation_paths
    _workspace_root = workspace_root
    metrics_client = metrics_client_instance
    metrics_config = metrics_config_instance
    PERF_ARTIFACT_PREFIX = perf_artifact_prefix
    PERF_LOG_LIMIT = perf_log_limit
    perf_state = perf_state_ref
    _as_float = as_float
    _as_int = as_int
    return router



# ---------------------------------------------------------------------------
# Performance Testing — Locust integration + metrics services status
# ---------------------------------------------------------------------------

PERF_MODE_TO_USER_CLASS = {
    "mixed": "MixedUser",
    "login": "LoginUser",
    "business": "BusinessUser",
    "order_create": "OrderCreateUser",
    "order_cancel": "OrderCancelUser",
    "linked_ticket": "LinkedTicketUser",
}
PERF_MODE_ORDER = ["mixed", "login", "business", "order_create", "order_cancel"]
PERF_LOCUSTFILE_MODE_MAP = {
    "tests/performance/locustfile.py": PERF_MODE_ORDER,
    "tests/performance/business_create_order.py": ["order_create"],
    "tests/performance/linked_ticket.py": ["linked_ticket"],
}


def _normalize_perf_locustfile(value: str) -> str:
    return (value or "").replace("\\", "/").strip()


def _allowed_perf_modes(locustfile: str) -> list[str]:
    normalized = _normalize_perf_locustfile(locustfile)
    if normalized in PERF_LOCUSTFILE_MODE_MAP:
        return PERF_LOCUSTFILE_MODE_MAP[normalized]

    filename = Path(normalized).name.lower()
    if "create_order" in filename or "create-order" in filename:
        return ["order_create"]
    if "cancel_order" in filename or "cancel-order" in filename:
        return ["order_cancel"]
    return PERF_MODE_ORDER


class PerfTestRequest(BaseModel):
    """Body for POST /api/perf/run."""
    project: str = "west-kowloon"
    host: str = "https://anticket.lengliwh.com"
    mode: str = "mixed"
    users: int = 100
    spawn_rate: float = 10.0   # users per second; locust -r accepts fractional values (e.g. 0.5 = 1 user per 2s)
    duration: str = "60s"
    locustfile: str = ""


def _perf_tag_value(value: str | None) -> str | None:
    tag = re.sub(r"[^A-Za-z0-9_]+", "_", value or "").strip("_").lower()
    return tag or None


def _perf_run_tags(mode: str | None, locustfile: str | None = None) -> str:
    tags = ["@performance", "@locust"]
    mode_tag = _perf_tag_value(mode)
    if mode_tag:
        tags.append(f"@{mode_tag}")
    file_tag = _perf_tag_value(Path(_normalize_perf_locustfile(locustfile or "")).stem)
    if file_tag and file_tag != mode_tag:
        tags.append(f"@{file_tag}")
    return ",".join(dict.fromkeys(tags))


def _create_perf_run_record(
    project_key: str,
    req: PerfTestRequest,
    mode: str,
    started_at: datetime,
    artifact_prefix: Path,
) -> int:
    db = get_db()
    try:
        run = TestRun(
            started_at=started_at,
            status="running",
            env="local",
            project_key=project_key,
            tags=_perf_run_tags(mode, req.locustfile),
            run_kind="performance",
            total=0,
            passed=0,
            failed=0,
            errored=0,
            skipped=0,
        )
        db.add(run)
        db.flush()
        db.add(PerformanceRunConfig(
            run_id=run.id,
            host=req.host,
            locustfile=req.locustfile,
            mode=mode,
            users=req.users,
            spawn_rate=req.spawn_rate,
            duration=req.duration,
            artifact_prefix=str(artifact_prefix),
            total_requests=0,
            total_failures=0,
            error_rate=0,
            avg_response_time=0,
            rps=0,
        ))
        db.commit()
        db.refresh(run)
        return run.id
    finally:
        db.close()


def _perf_db_status(final_status: str, total_requests: int, total_failures: int) -> str:
    if final_status == "completed":
        if total_requests <= 0:
            return "error"
        return "failed" if total_failures > 0 else "passed"
    if final_status == "stopped":
        return "failed" if total_requests > 0 else "error"
    return "error"


def _perf_endpoint_error_msg(endpoint: dict) -> str:
    requests = _as_int(endpoint.get("requests"))
    failures = _as_int(endpoint.get("failures"))
    error_rate = round((failures / requests) * 100, 2) if requests else 0
    return (
        f"requests={requests}, failures={failures}, error_rate={error_rate}%, "
        f"avg_ms={round(_as_float(endpoint.get('avg_response_time')), 2)}, "
        f"p95_ms={round(_as_float(endpoint.get('p95')), 2)}, "
        f"rps={round(_as_float(endpoint.get('rps')), 2)}"
    )


def _record_perf_run_to_db(
    run_id: int | None,
    project_key: str,
    report: Optional[dict],
    final_status: str,
    finished_at: datetime,
    error_message: str | None = None,
) -> None:
    if not run_id:
        return

    summary = (report or {}).get("summary") or {}
    endpoints = list((report or {}).get("endpoints") or [])
    total_requests = _as_int(summary.get("total_requests") or perf_state.get("total_requests"))
    total_failures = _as_int(summary.get("total_failures") or perf_state.get("total_failures"))

    if not endpoints and total_requests:
        endpoints = [{
            "method": "ALL",
            "endpoint": "Aggregated",
            "requests": total_requests,
            "failures": total_failures,
            "avg_response_time": summary.get("avg_response_time"),
            "p95": 0,
            "rps": summary.get("rps"),
        }]

    db = get_db()
    try:
        run = (
            db.query(TestRun)
            .filter(TestRun.id == run_id, TestRun.project_key == project_key)
            .first()
        )
        if not run:
            return

        db.query(TestScenario).filter(TestScenario.run_id == run_id).delete(synchronize_session=False)

        if endpoints:
            passed = 0
            failed = 0
            for endpoint in endpoints:
                failures = _as_int(endpoint.get("failures"))
                status = "failed" if failures > 0 else "passed"
                passed += 1 if status == "passed" else 0
                failed += 1 if status == "failed" else 0
                method = str(endpoint.get("method") or "ALL").strip()
                endpoint_name = str(endpoint.get("endpoint") or "Aggregated").strip()
                db.add(TestScenario(
                    run_id=run_id,
                    feature="Performance Test",
                    name=f"{method} {endpoint_name}".strip(),
                    status=status,
                    duration_s=round(_as_float(endpoint.get("avg_response_time")) / 1000, 3),
                    error_msg=_perf_endpoint_error_msg(endpoint),
                    tags=run.tags,
                ))

            run.total = len(endpoints)
            run.passed = passed
            run.failed = failed
            run.errored = 0
            run.skipped = 0
        else:
            run.total = 1
            run.passed = 0
            run.failed = 0
            run.errored = 1
            run.skipped = 0
            db.add(TestScenario(
                run_id=run_id,
                feature="Performance Test",
                name="Locust process",
                status="error",
                duration_s=0,
                error_msg=error_message or "Locust ended without generating report data",
                tags=run.tags,
            ))

        run.finished_at = finished_at
        run.status = _perf_db_status(final_status, total_requests, total_failures)
        meta = db.query(PerformanceRunConfig).filter(PerformanceRunConfig.run_id == run_id).first()
        if not meta:
            meta = PerformanceRunConfig(
                run_id=run_id,
                host="",
                locustfile="",
                mode="",
                duration="",
            )
            db.add(meta)
        meta.total_requests = total_requests
        meta.total_failures = total_failures
        meta.error_rate = round((total_failures / total_requests) * 100, 2) if total_requests else 0
        meta.avg_response_time = round(_as_float(summary.get("avg_response_time")), 2)
        meta.rps = round(_as_float(summary.get("rps")), 2)
        db.commit()
    finally:
        db.close()


def _safe_record_perf_run_to_db(
    run_id: int | None,
    project_key: str,
    report: Optional[dict],
    final_status: str,
    finished_at: datetime,
    error_message: str | None = None,
) -> None:
    try:
        _record_perf_run_to_db(
            run_id,
            project_key,
            report,
            final_status,
            finished_at,
            error_message,
        )
    except Exception as exc:
        detail = f"Could not write performance run record: {exc}"
        existing = perf_state.get("error")
        perf_state["error"] = f"{existing}; {detail}" if existing else detail


def _perf_artifact_prefix(project: str | None) -> Path:
    return _automation_paths(project)["evidence_root"] / "performance" / "latest" / "perf_latest"


@router.get("/api/perf/status")
async def perf_status(project: str = "west-kowloon"):
    """Return the latest Locust run status and metadata."""
    project_key = _project_key(project)
    state = _perf_state_dict()
    if state.get("project") in (None, project_key):
        if state.get("status") == "idle" and state.get("project") is None:
            return {
                **state,
                "project": project_key,
                "artifacts_prefix": str(_perf_artifact_prefix(project_key)),
            }
        return state
    return {
        **state,
        "status": "idle",
        "project": project_key,
        "pid": None,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "config": None,
        "artifacts_prefix": str(_perf_artifact_prefix(project_key)),
        "logs": [],
        "error": None,
        "total_requests": 0,
        "total_failures": 0,
        "error_rate": 0,
        "message": "No performance run is active for this project.",
    }


@router.get("/api/perf/services")
async def perf_service_status():
    """Check connectivity to Prometheus and Grafana."""
    prom, graf = await asyncio.gather(
        metrics_client.check_prometheus(),
        metrics_client.check_grafana(),
    )
    return {
        "prometheus": {"connected": prom, "url": metrics_config.prometheus_url},
        "grafana": {"connected": graf, "url": metrics_config.grafana_url},
    }


@router.get("/api/perf/grafana/panels")
async def perf_grafana_panels():
    """Get Grafana dashboard/panel URLs for iframe embedding."""
    uid = metrics_config.grafana_dashboard_uid
    if not uid:
        return {"panels": [], "dashboard_url": "", "message": "GRAFANA_DASHBOARD_UID not configured"}

    return {
        "dashboard_url": metrics_client.get_grafana_dashboard_url(uid),
        "panels": [
            {
                "title": "Response Time",
                "url": metrics_client.get_grafana_panel_url(uid, panel_id=1),
            },
            {
                "title": "Throughput (RPS)",
                "url": metrics_client.get_grafana_panel_url(uid, panel_id=2),
            },
            {
                "title": "Error Rate",
                "url": metrics_client.get_grafana_panel_url(uid, panel_id=3),
            },
            {
                "title": "Active Users",
                "url": metrics_client.get_grafana_panel_url(uid, panel_id=4),
            },
        ],
    }


@router.get("/api/perf/metrics")
async def perf_metrics():
    """Query real-time performance metrics from Prometheus (or mock data).

    Skips expensive Prometheus queries if Prometheus is not connected,
    returning empty series so the dashboard falls back to CSV report data.
    """
    prom_connected = await metrics_client.check_prometheus()
    if not prom_connected:
        return {"rps": [], "response_time": [], "error_rate": [], "users": []}

    queries = await asyncio.gather(
        metrics_client.query_prometheus('sum(rate(locust_request_count_total[1m]))', step="15s"),
        metrics_client.query_prometheus('histogram_quantile(0.95, sum(rate(locust_request_latency_seconds_bucket[1m])) by (le)) * 1000', step="15s"),
        metrics_client.query_prometheus('sum(rate(locust_request_count_total{status="failure"}[1m])) / clamp_min(sum(rate(locust_request_count_total[1m])), 1) * 100', step="15s"),
        metrics_client.query_prometheus('max(last_over_time(locust_active_users[10s]))', step="15s"),
    )

    rps_data, rt_data, err_data, users_data = queries

    import math
    def extract_series(data):
        """Pull (time, value) pairs out of a Prometheus query_range response.
        Prometheus returns 'NaN' (string) for points where the rate has no
        data; float('NaN') then fails JSON serialization downstream, so we
        skip non-finite values rather than emit them."""
        results = data.get("data", {}).get("result", [])
        if not results:
            return []
        out = []
        for v in results[0].get("values", []):
            try:
                val = float(v[1])
            except (ValueError, TypeError):
                continue
            if not math.isfinite(val):
                continue
            out.append({"time": v[0], "value": val})
        return out

    return {
        "rps": extract_series(rps_data),
        "response_time": extract_series(rt_data),
        "error_rate": extract_series(err_data),
        "users": extract_series(users_data),
    }


@router.get("/api/perf/report")
def perf_latest_report(project: str = "west-kowloon"):
    """Get the latest performance test report parsed from Locust artifacts."""
    project_key = _project_key(project)
    report = _parse_locust_report(_current_perf_artifact_prefix(project_key))
    if report:
        report.setdefault("project", project_key)
        return report

    return {
        "project": project_key,
        "summary": {},
        "endpoints": [],
        "timeseries": {"rps": [], "response_time": [], "error_rate": [], "users": []},
        "status": perf_state["status"],
        "source": "empty",
        "message": "No completed performance report yet.",
    }


def _perf_run_config_dict(run: TestRun, meta: PerformanceRunConfig | None) -> dict:
    return {
        "id": run.id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "project": run.project_key,
        "run_kind": run.run_kind or "performance",
        "tags": run.tags,
        "endpoint_total": run.total or 0,
        "endpoint_passed": run.passed or 0,
        "endpoint_failed": run.failed or 0,
        "host": meta.host if meta else "",
        "locustfile": meta.locustfile if meta else "",
        "mode": meta.mode if meta else "",
        "users": meta.users if meta else 0,
        "spawn_rate": meta.spawn_rate if meta else 0,
        "duration": meta.duration if meta else "",
        "artifact_prefix": meta.artifact_prefix if meta else None,
        "total_requests": meta.total_requests if meta else 0,
        "total_failures": meta.total_failures if meta else 0,
        "error_rate": meta.error_rate if meta else 0,
        "avg_response_time": meta.avg_response_time if meta else 0,
        "rps": meta.rps if meta else 0,
    }


def _perf_endpoint_from_scenario(s: TestScenario) -> dict:
    raw_name = (s.name or "").strip()
    method = "ALL"
    endpoint = raw_name
    if " " in raw_name:
        first, rest = raw_name.split(" ", 1)
        if first.isupper() or first in {"TXN"}:
            method = first
            endpoint = rest

    stats = {}
    for match in re.finditer(r"(requests|failures|error_rate|avg_ms|p95_ms|rps)=([^,]+)", s.error_msg or ""):
        stats[match.group(1)] = match.group(2).strip()

    requests = _as_int(stats.get("requests"))
    failures = _as_int(stats.get("failures"))
    return {
        "method": method,
        "endpoint": endpoint,
        "requests": requests,
        "failures": failures,
        "avg_response_time": round(_as_float(stats.get("avg_ms")), 2),
        "p95": round(_as_float(stats.get("p95_ms")), 2),
        "p99": 0,
        "rps": round(_as_float(stats.get("rps")), 2),
        "error_rate": round(_as_float(stats.get("error_rate")), 2) if stats else (
            round((failures / requests) * 100, 2) if requests else 0
        ),
        "status": s.status,
        "duration_s": s.duration_s or 0,
    }


@router.get("/api/perf/runs")
def list_perf_runs(project: str = "west-kowloon", limit: int = 50):
    """List persisted Locust performance runs for the Performance Test page."""
    project_key = _project_key(project)
    row_limit = max(1, min(limit, 200))
    db = get_db()
    try:
        runs = (
            db.query(TestRun)
            .filter(TestRun.project_key == project_key, TestRun.run_kind == "performance")
            .order_by(TestRun.id.desc())
            .limit(row_limit)
            .all()
        )
        metas = {
            meta.run_id: meta
            for meta in (
                db.query(PerformanceRunConfig)
                .filter(PerformanceRunConfig.run_id.in_([run.id for run in runs]))
                .all()
                if runs else []
            )
        }
        return {
            "project": project_key,
            "runs": [_perf_run_config_dict(run, metas.get(run.id)) for run in runs],
        }
    finally:
        db.close()


@router.get("/api/perf/runs/{run_id}")
def get_perf_run_detail(run_id: int, project: str = "west-kowloon"):
    """Get one persisted Locust run with endpoint summaries."""
    project_key = _project_key(project)
    db = get_db()
    try:
        run = (
            db.query(TestRun)
            .filter(
                TestRun.id == run_id,
                TestRun.project_key == project_key,
                TestRun.run_kind == "performance",
            )
            .first()
        )
        if not run:
            return {"error": "Performance run not found"}
        meta = db.query(PerformanceRunConfig).filter(PerformanceRunConfig.run_id == run_id).first()
        scenarios = (
            db.query(TestScenario)
            .filter(TestScenario.run_id == run_id)
            .order_by(TestScenario.id.asc())
            .all()
        )
        endpoints = [_perf_endpoint_from_scenario(s) for s in scenarios]
        detail = _perf_run_config_dict(run, meta)
        detail["summary"] = {
            "total_requests": detail["total_requests"],
            "total_failures": detail["total_failures"],
            "error_rate": detail["error_rate"],
            "avg_response_time": detail["avg_response_time"],
            "rps": detail["rps"],
            "virtual_users": detail["users"],
            "start_time": detail["started_at"],
            "end_time": detail["finished_at"],
        }
        detail["endpoints"] = endpoints
        return detail
    finally:
        db.close()


@router.get("/api/perf/locustfiles")
def list_perf_locustfiles(project: str = "west-kowloon"):
    """List top-level Locust entry files available to the dashboard."""
    project_key = _project_key(project)
    tests_root = _automation_paths(project_key)["tests_root"]
    perf_dir = tests_root / "performance"
    if not perf_dir.exists():
        return {
            "project": project_key,
            "files": [],
            "modes": {},
            "testsRoot": str(tests_root).replace("\\", "/"),
            "performanceDir": str(perf_dir).replace("\\", "/"),
            "message": "No performance directory found for this project.",
        }

    files = []
    modes = {}
    entry_files = sorted(
        perf_dir.glob("*.py"),
        key=lambda p: (p.name != "locustfile.py", p.name.lower()),
    )
    for path in entry_files:
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(tests_root).as_posix()
        locustfile = f"tests/{rel}"
        files.append(locustfile)
        modes[locustfile] = _allowed_perf_modes(locustfile)
    return {
        "project": project_key,
        "files": files,
        "modes": modes,
        "testsRoot": str(tests_root).replace("\\", "/"),
        "performanceDir": str(perf_dir).replace("\\", "/"),
        "message": (
            None if files else
            "No Locust entry files found. Add a .py file under the project's 02-tests/performance directory."
        ),
    }


@router.post("/api/perf/stop")
async def stop_perf_test():
    """Forcibly stop the running Locust test.

    Sets stop_requested so _monitor_perf_process can distinguish a
    user-initiated stop ('stopped') from an unexpected crash ('failed').
    """
    if perf_state["status"] != "running":
        return {"status": perf_state["status"], "message": "No test currently running"}
    pid = perf_state.get("pid")
    if not pid:
        return {"error": "Marked as running but no PID recorded"}
    perf_state["stop_requested"] = True
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        return {"status": "stopping", "pid": pid}
    except ProcessLookupError:
        perf_state["stop_requested"] = False
        return {"status": "already_stopped", "pid": pid}
    except Exception as e:
        perf_state["stop_requested"] = False
        return {"error": str(e)}


@router.post("/api/perf/run")
async def start_perf_test(req: PerfTestRequest):
    """Trigger a Locust performance test.
    Returns immediately; the test runs in the background."""
    if perf_state["status"] == "running":
        return {"error": "A performance test is already running", "status": "running"}

    project_key = _project_key(req.project)
    paths = _automation_paths(project_key)
    locustfile_value = _normalize_perf_locustfile(req.locustfile)
    if not locustfile_value:
        return {
            "error": (
                f"No Locust file selected for project {project_key}. "
                f"Add a .py file under {str(paths['tests_root'] / 'performance').replace('\\', '/')}."
            )
        }
    locustfile = paths["automation_root"] / locustfile_value
    if not locustfile.exists() and locustfile_value.startswith("tests/"):
        locustfile = paths["tests_root"] / locustfile_value.removeprefix("tests/")
    if not locustfile.exists():
        available = list_perf_locustfiles(project_key).get("files", [])
        return {
            "error": (
                f"Locust file not found for project {project_key}: {locustfile_value}. "
                f"Resolved path: {str(locustfile).replace('\\', '/')}. "
                f"Available files: {', '.join(available) if available else 'none'}."
            )
        }

    mode = (req.mode or "mixed").strip().lower()
    allowed_modes = _allowed_perf_modes(locustfile_value)
    if mode not in allowed_modes:
        return {
            "error": (
                f"Mode {req.mode!r} is not valid for {req.locustfile}. "
                f"Allowed modes: {', '.join(allowed_modes)}"
            )
        }

    user_class = PERF_MODE_TO_USER_CLASS.get(mode)
    if not user_class:
        return {"error": f"Unsupported performance mode: {req.mode}"}

    artifact_prefix = _perf_artifact_prefix(project_key)
    artifact_prefix.parent.mkdir(parents=True, exist_ok=True)
    for old_csv in artifact_prefix.parent.glob(f"{artifact_prefix.name}_*.csv"):
        try:
            old_csv.unlink()
        except OSError:
            pass

    import sys
    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(locustfile),
        "--headless",
        "-u", str(req.users),
        "-r", str(req.spawn_rate),
        "--run-time", req.duration,
        "--host", req.host,
        "--csv", str(artifact_prefix),
        user_class,
    ]

    env_vars = dict(os.environ)
    env_vars["LOCUST_PROMETHEUS"] = "1"
    env_vars["PERF_MODE"] = mode
    env_vars["QA_PROJECT_KEY"] = project_key
    env_vars["QA_PROJECT_AUTOMATION_ROOT"] = str(paths["automation_root"])
    env_vars["QA_WORKSPACE_ROOT"] = str(_workspace_root)

    started_at = datetime.utcnow()
    try:
        run_id = _create_perf_run_record(project_key, req, mode, started_at, artifact_prefix)
    except Exception as exc:
        return {"error": f"Could not create dashboard run record: {exc}"}

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(paths["automation_root"]),
            env=env_vars,
        )
        perf_state.update({
            "status": "running",
            "project": project_key,
            "run_id": run_id,
            "pid": process.pid,
            "started_at": started_at.isoformat(),
            "finished_at": None,
            "exit_code": None,
            "config": {
                "run_id": run_id,
                "project": project_key,
                "host": req.host,
                "mode": mode,
                "users": req.users,
                "spawn_rate": req.spawn_rate,
                "duration": req.duration,
                "locustfile": req.locustfile,
            },
            "logs": deque(maxlen=PERF_LOG_LIMIT),
            "error": None,
            "total_requests": 0,
            "total_failures": 0,
            "error_rate": 0,
            "artifacts_prefix": str(artifact_prefix),
        })
        asyncio.create_task(_monitor_perf_process(process, project_key, artifact_prefix, run_id))
        return {
            "status": "started",
            "run_id": run_id,
            "pid": process.pid,
            "config": {
                "run_id": run_id,
                "project": project_key,
                "host": req.host,
                "mode": mode,
                "users": req.users,
                "spawn_rate": req.spawn_rate,
                "duration": req.duration,
                "locustfile": req.locustfile,
                "artifacts_prefix": str(artifact_prefix),
            },
        }
    except Exception as exc:
        finished_at = datetime.utcnow()
        _safe_record_perf_run_to_db(run_id, project_key, None, "failed", finished_at, str(exc))
        perf_state.update({
            "status": "error",
            "run_id": run_id,
            "pid": None,
            "finished_at": finished_at.isoformat(),
            "exit_code": None,
            "error": str(exc),
        })
        return {"error": str(exc), "run_id": run_id}



async def _monitor_perf_process(
    process,
    project_key: str | None = None,
    artifact_prefix: Path | None = None,
    run_id: int | None = None,
):
    """Drain Locust logs and update the in-memory run status when it exits."""
    try:
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    perf_state["logs"].append(decoded)

        exit_code = await process.wait()

        # Parse the Aggregated row from the stats CSV to find out if the test
        # actually produced traffic. Locust exits 1 whenever any HTTP request
        # failed (default --exit-code-on-error 1), but that's a target-server
        # symptom, not a process crash. We want "completed" status when traffic
        # was generated, surfacing the failure count separately.
        prefix = artifact_prefix or _current_perf_artifact_prefix(project_key)
        stats_path = prefix.parent / f"{prefix.name}_stats.csv"
        total_requests = 0
        total_failures = 0
        if stats_path.exists():
            try:
                for row in _read_csv_rows(stats_path):
                    name = (_row_value(row, "Name", "name") or "").strip().lower()
                    rtype = (_row_value(row, "Type", "type") or "").strip().lower()
                    if name == "aggregated" or rtype == "aggregated":
                        total_requests = _as_int(_row_value(row, "Request Count", "request_count"))
                        total_failures = _as_int(_row_value(row, "Failure Count", "failure_count"))
                        break
            except Exception:
                pass

        if perf_state.get("stop_requested"):
            final_status = "stopped"
            final_error = None
        elif total_requests > 0:
            # Traffic was generated → the test ran. Exit code 1 with traffic just
            # means some HTTP requests failed, not that locust crashed.
            final_status = "completed"
            final_error = None
        else:
            # No traffic at all → real crash (couldn't even start hitting the target).
            final_status = "failed"
            final_error = f"Locust exited with code {exit_code} without generating traffic"

        finished_at = datetime.utcnow()
        error_rate = round((total_failures / total_requests) * 100, 2) if total_requests else 0
        perf_state.update({
            "status": final_status,
            "finished_at": finished_at.isoformat(),
            "exit_code": exit_code,
            "pid": None,
            "error": final_error,
            "stop_requested": False,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "error_rate": error_rate,
        })
        report = _parse_locust_report(prefix)
        _safe_record_perf_run_to_db(
            run_id or perf_state.get("run_id"),
            project_key or perf_state.get("project") or "west-kowloon",
            report,
            final_status,
            finished_at,
            final_error,
        )
    except Exception as exc:
        finished_at = datetime.utcnow()
        perf_state.update({
            "status": "error",
            "finished_at": finished_at.isoformat(),
            "exit_code": None,
            "pid": None,
            "error": str(exc),
        })
        _safe_record_perf_run_to_db(
            run_id or perf_state.get("run_id"),
            project_key or perf_state.get("project") or "west-kowloon",
            None,
            "failed",
            finished_at,
            str(exc),
        )


def _perf_state_dict() -> dict:
    return {
        "status": perf_state["status"],
        "project": perf_state.get("project"),
        "run_id": perf_state.get("run_id"),
        "pid": perf_state["pid"],
        "started_at": perf_state["started_at"],
        "finished_at": perf_state["finished_at"],
        "exit_code": perf_state["exit_code"],
        "config": perf_state["config"],
        "artifacts_prefix": perf_state["artifacts_prefix"],
        "logs": list(perf_state["logs"]),
        "error": perf_state["error"],
        "total_requests": perf_state.get("total_requests", 0),
        "total_failures": perf_state.get("total_failures", 0),
        "error_rate": perf_state.get("error_rate", 0),
    }


def _current_perf_artifact_prefix(project: str | None = None) -> Path:
    if perf_state.get("status") == "running" and perf_state.get("artifacts_prefix"):
        if project is None or perf_state.get("project") in (None, _project_key(project)):
            return Path(perf_state["artifacts_prefix"])
    if project is not None:
        return _perf_artifact_prefix(project)
    return Path(perf_state.get("artifacts_prefix") or PERF_ARTIFACT_PREFIX)


def _parse_locust_report(prefix: Path) -> Optional[dict]:
    stats_path = prefix.parent / f"{prefix.name}_stats.csv"
    history_path = prefix.parent / f"{prefix.name}_stats_history.csv"
    if not stats_path.exists():
        return None

    rows = _read_csv_rows(stats_path)
    if not rows:
        return None

    aggregated = None
    endpoints = []
    for row in rows:
        row_type = (_row_value(row, "Type", "type") or "").strip()
        name = (_row_value(row, "Name", "name") or "").strip()
        if not name and not row_type:
            continue

        if name.lower() == "aggregated" or row_type.lower() == "aggregated":
            aggregated = row
            continue

        endpoint = {
            "method": row_type or "ALL",
            "endpoint": name,
            "requests": _as_int(_row_value(row, "Request Count", "request_count")),
            "failures": _as_int(_row_value(row, "Failure Count", "failure_count")),
            "avg_response_time": _as_float(_row_value(row, "Average Response Time", "avg_response_time")),
            "min_response_time": _as_float(_row_value(row, "Min Response Time", "min_response_time")),
            "max_response_time": _as_float(_row_value(row, "Max Response Time", "max_response_time")),
            "p50": _as_float(_row_value(row, "50%", "50_percentile", "Median Response Time", "median_response_time")),
            "p90": _as_float(_row_value(row, "90%", "90_percentile")),
            "p95": _as_float(_row_value(row, "95%", "95_percentile")),
            "p99": _as_float(_row_value(row, "99%", "99_percentile")),
            "rps": round(_as_float(_row_value(row, "Requests/s", "requests_per_sec")), 2),
        }
        endpoint["error_rate"] = round((endpoint["failures"] / endpoint["requests"]) * 100, 2) if endpoint["requests"] else 0
        endpoints.append(endpoint)

    summary_row = aggregated or {}
    total_requests = _as_int(_row_value(summary_row, "Request Count", "request_count"))
    total_failures = _as_int(_row_value(summary_row, "Failure Count", "failure_count"))
    duration_s = _history_duration_seconds(history_path)
    timeseries = _parse_locust_history(history_path)

    start_time = perf_state["started_at"]
    end_time = perf_state["finished_at"] if perf_state["status"] in {"completed", "failed", "error"} else None

    return {
        "summary": {
            "total_requests": total_requests,
            "total_failures": total_failures,
            "error_rate": round((total_failures / total_requests) * 100, 2) if total_requests else 0,
            "avg_response_time": round(_as_float(_row_value(summary_row, "Average Response Time", "avg_response_time")), 2),
            "rps": round(_as_float(_row_value(summary_row, "Requests/s", "requests_per_sec")), 2),
            "duration_s": duration_s,
            "virtual_users": perf_state["config"]["users"] if perf_state["config"] else None,
            "start_time": start_time,
            "end_time": end_time,
        },
        "endpoints": endpoints,
        "timeseries": timeseries,
        "status": perf_state["status"],
        "source": "locust_csv",
    }


def _parse_locust_history(history_path: Path) -> dict:
    empty = {"rps": [], "response_time": [], "error_rate": [], "users": []}
    if not history_path.exists():
        return empty

    rows = _read_csv_rows(history_path)
    if not rows:
        return empty

    series = {key: [] for key in empty}
    for idx, row in enumerate(rows):
        timestamp_raw = _row_value(row, "Timestamp", "timestamp")
        ts = _as_float(timestamp_raw) if timestamp_raw else float(idx)
        total_rps = _as_float(_row_value(row, "Total RPS", "total_rps", "Requests/s"))
        avg_rt = _as_float(_row_value(row, "Total Average Response Time", "total_average_response_time", "Average Response Time"))
        user_count = _as_float(_row_value(row, "User Count", "user_count", "Users"))
        fail_ps = _as_float(_row_value(row, "Failures/s", "failures_per_sec", "Total Failure Count/s"))

        series["rps"].append({"time": ts, "value": round(total_rps, 2)})
        series["response_time"].append({"time": ts, "value": round(avg_rt, 2)})
        series["error_rate"].append({
            "time": ts,
            "value": round((fail_ps / total_rps) * 100, 2) if total_rps else 0,
        })
        series["users"].append({"time": ts, "value": round(user_count, 2)})

    return series


def _history_duration_seconds(history_path: Path) -> int:
    rows = _read_csv_rows(history_path)
    if len(rows) < 2:
        if perf_state["started_at"] and perf_state["finished_at"]:
            started = datetime.fromisoformat(perf_state["started_at"])
            finished = datetime.fromisoformat(perf_state["finished_at"])
            return int((finished - started).total_seconds())
        return 0

    first = _as_float(_row_value(rows[0], "Timestamp", "timestamp"))
    last = _as_float(_row_value(rows[-1], "Timestamp", "timestamp"))
    if first and last and last >= first:
        return int(last - first)
    return 0


def _read_csv_rows(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _row_value(row: dict, *keys: str) -> Optional[str]:
    normalized = {(_normalize_key(k)): v for k, v in row.items() if k is not None}
    for key in keys:
        if _normalize_key(key) in normalized:
            return normalized[_normalize_key(key)]
    return None


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


