"""API Monitor routes and smoke-run state."""

import json
import os
import re
import subprocess
import sys
import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from database import ApiMonitorEndpointResult, ApiMonitorRun, get_db


router = APIRouter()
_backend_root = Path(__file__).resolve().parents[1]
_repo_root = Path(os.environ.get("QA_HARNESS_ROOT", _backend_root.parents[2])).resolve()
_workspace_root = Path(os.environ.get("QA_WORKSPACE_ROOT", _repo_root.parent)).resolve()
ARTIFACTS_ROOT = _workspace_root / "west-kowloon" / "02-automation" / "07-artifacts"


def configure_router(*, project_key, project_match_values, automation_paths):
    global _project_key, _project_match_values, _automation_paths
    _project_key = project_key
    _project_match_values = project_match_values
    _automation_paths = automation_paths
    return router


# ---------------------------------------------------------------------------
# API Monitor — smoke test results for the public-website APIs
# ---------------------------------------------------------------------------
# The smoke runner (project 02-automation/02-tests/api/) writes its result JSON to
#   project 02-automation/07-artifacts/api_smoke/latest.json
# We serve it as-is so the React page can render without inventing its own
# format. If the JSON is missing (suite never ran), return an empty payload
# rather than 404 so the UI can show "no data yet" instead of an error.

_API_SMOKE_PATH = ARTIFACTS_ROOT / "api_smoke" / "latest.json"
_API_LAYER_PATH = ARTIFACTS_ROOT / "api_smoke" / "layer_summary.json"
_API_SMOKE_LOG_LIMIT = 200
_API_SMOKE_PYTHON = (
    _repo_root / "02-platform" / "01-automation" / ".venv" / "Scripts" / "python.exe"
)
if not _API_SMOKE_PYTHON.exists():
    _API_SMOKE_PYTHON = Path(sys.executable)
_api_smoke_lock = threading.Lock()
_api_smoke_state = {
    "running": False,
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "exit_code": None,
    "env": None,
    "project": None,
    "command": None,
    "log": [],
    "error": None,
    "artifact_updated": False,
}


class ApiSmokeRunRequest(BaseModel):
    """Body for POST /api/api-monitor/run-smoke."""
    project: str = "west-kowloon"
    env: str = "sit"


def _api_smoke_path(project: str | None) -> Path:
    return _automation_paths(project)["artifacts_root"] / "api_smoke" / "latest.json"


def _api_layer_path(project: str | None) -> Path:
    return _automation_paths(project)["artifacts_root"] / "api_smoke" / "layer_summary.json"


def _parse_ran_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Both "2026-05-29T12:51:27" and "2026-05-29T12:51:27+00:00" supported
        s = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        # Strip tz so SQLite comparisons stay sane (we store naive UTC)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _api_smoke_state_unlocked() -> dict:
    return {
        "running": _api_smoke_state["running"],
        "status": _api_smoke_state["status"],
        "started_at": _api_smoke_state["started_at"],
        "finished_at": _api_smoke_state["finished_at"],
        "exit_code": _api_smoke_state["exit_code"],
        "env": _api_smoke_state["env"],
        "project": _api_smoke_state.get("project"),
        "command": _api_smoke_state["command"],
        "log": list(_api_smoke_state["log"][-80:]),
        "error": _api_smoke_state["error"],
        "artifact_updated": _api_smoke_state["artifact_updated"],
    }


def _api_smoke_state_dict() -> dict:
    with _api_smoke_lock:
        return _api_smoke_state_unlocked()


def _file_mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _run_api_smoke(env: str, project: str) -> None:
    paths = _automation_paths(project)
    smoke_path = _api_smoke_path(project)
    cmd = [str(_API_SMOKE_PYTHON), "-m", "pytest", "02-tests/api/api_smoke", "-q"]
    proc_env = dict(os.environ)
    proc_env["ENV"] = env
    proc_env["QA_PROJECT_KEY"] = project
    proc_env["QA_PROJECT_AUTOMATION_ROOT"] = str(paths["automation_root"])
    proc_env["QA_WORKSPACE_ROOT"] = str(_workspace_root)
    proc_env["PYTHONIOENCODING"] = "utf-8"
    proc_env["PYTHONUTF8"] = "1"
    artifact_mtime_before = _file_mtime_ns(smoke_path)

    try:
        with _api_smoke_lock:
            _api_smoke_state["log"].append(f"[api-smoke] project={project}")
            _api_smoke_state["log"].append(f"[api-smoke] cwd={paths['automation_root']}")
            _api_smoke_state["log"].append(f"[api-smoke] {' '.join(cmd)}")

        proc = subprocess.Popen(
            cmd,
            cwd=paths["automation_root"],
            env=proc_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            with _api_smoke_lock:
                _api_smoke_state["log"].append(line.rstrip("\n"))
                _api_smoke_state["log"] = _api_smoke_state["log"][-_API_SMOKE_LOG_LIMIT:]
        proc.wait()

        artifact_mtime_after = _file_mtime_ns(smoke_path)
        artifact_updated = artifact_mtime_after is not None and artifact_mtime_after != artifact_mtime_before
        status = "passed" if proc.returncode == 0 else "failed"
        error = None
        if not artifact_updated:
            error = "API smoke did not update latest.json; dashboard data may still be from the previous run."
            status = "error" if proc.returncode == 0 else "failed"

        with _api_smoke_lock:
            _api_smoke_state["exit_code"] = proc.returncode
            _api_smoke_state["status"] = status
            _api_smoke_state["artifact_updated"] = artifact_updated
            _api_smoke_state["error"] = error
            if error:
                _api_smoke_state["log"].append(f"[api-smoke warning] {error}")

        if artifact_updated:
            db = get_db()
            try:
                _ingest_latest_api_smoke_json(db, project)
            finally:
                db.close()
    except Exception as exc:  # noqa: BLE001
        with _api_smoke_lock:
            _api_smoke_state["status"] = "error"
            _api_smoke_state["exit_code"] = -1
            _api_smoke_state["error"] = str(exc)
            _api_smoke_state["artifact_updated"] = False
            _api_smoke_state["log"].append(f"[api-smoke error] {exc}")
    finally:
        with _api_smoke_lock:
            _api_smoke_state["running"] = False
            _api_smoke_state["finished_at"] = _utc_now_iso()


def _ingest_latest_api_smoke_json(db, project: str = "west-kowloon") -> None:
    """If latest.json on disk is newer than the latest DB row, append a new
    ApiMonitorRun + per-endpoint results. Idempotent — called freely on every
    endpoints/trends request."""
    import json as _json
    project_key = _project_key(project)
    smoke_path = _api_smoke_path(project_key)
    if not smoke_path.exists():
        return
    try:
        payload = _json.loads(smoke_path.read_text(encoding="utf-8"))
    except Exception:
        return
    ran_at_dt = _parse_ran_at(payload.get("ran_at"))
    if ran_at_dt is None:
        return
    latest_db = (
        db.query(ApiMonitorRun)
        .filter(ApiMonitorRun.project.in_(list(_project_match_values(project_key))))
        .order_by(ApiMonitorRun.ran_at.desc())
        .first()
    )
    if latest_db and latest_db.ran_at >= ran_at_dt:
        return  # already ingested
    summary = payload.get("summary") or {}
    run = ApiMonitorRun(
        ran_at=ran_at_dt,
        project=project_key,
        website_url=payload.get("website_url") or "",
        total=int(summary.get("total") or 0),
        up=int(summary.get("up") or 0),
        degraded=int(summary.get("degraded") or 0),
        down=int(summary.get("down") or 0),
        skipped=int(summary.get("skipped") or 0),
    )
    db.add(run)
    db.flush()  # need run.id for FK
    for row in payload.get("endpoints") or []:
        db.add(ApiMonitorEndpointResult(
            run_id=run.id,
            name=str(row.get("name") or ""),
            method=str(row.get("method") or ""),
            path=str(row.get("path") or ""),
            status=str(row.get("status") or "skipped"),
            actual_status_code=row.get("actual_status_code"),
            latency_ms=row.get("latency_ms"),
            group=row.get("group"),
            auth_required=bool(row.get("auth_required") or False),
            notes=row.get("notes"),
            body_warning=row.get("body_warning"),
        ))
    db.commit()


@router.post("/api/api-monitor/run-smoke")
def start_api_monitor_smoke(req: ApiSmokeRunRequest):
    """Trigger the project API smoke pytest layer in the background."""
    project_key = _project_key(req.project)
    with _api_smoke_lock:
        if _api_smoke_state["running"]:
            return _api_smoke_state_unlocked()
        _api_smoke_state.update(
            running=True,
            status="running",
            started_at=_utc_now_iso(),
            finished_at=None,
            exit_code=None,
            env=req.env,
            project=project_key,
            command=f"{_API_SMOKE_PYTHON} -m pytest 02-tests/api/api_smoke -q",
            log=[],
            error=None,
            artifact_updated=False,
        )
    threading.Thread(target=_run_api_smoke, args=(req.env, project_key), daemon=True).start()
    return _api_smoke_state_dict()


@router.get("/api/api-monitor/run-smoke")
def get_api_monitor_smoke_run(project: str = "west-kowloon"):
    """Return the current or most recent API smoke trigger status."""
    project_key = _project_key(project)
    state = _api_smoke_state_dict()
    if state.get("project") in (None, project_key):
        return state
    return {
        "running": False,
        "status": "idle",
        "project": project_key,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "env": None,
        "command": None,
        "log": [],
        "error": None,
        "artifact_updated": False,
    }


@router.get("/api/api-monitor/endpoints")
async def get_api_monitor_endpoints(project: str = "west-kowloon"):
    """Return the latest API smoke run result, or an empty payload if never run.
    Side effect: ingest the JSON into DB if newer than the latest DB row."""
    import json as _json
    project_key = _project_key(project)
    smoke_path = _api_smoke_path(project_key)
    db = get_db()
    try:
        _ingest_latest_api_smoke_json(db, project_key)
    finally:
        db.close()
    if not smoke_path.exists():
        return {
            "project": project_key,
            "projectKey": project_key,
            "website_url": "",
            "ran_at": None,
            "summary": {"total": 0, "up": 0, "degraded": 0, "down": 0, "skipped": 0},
            "endpoints": [],
            "_note": f"No smoke run on record yet for {project_key}. Run from the project automation root: pytest 02-tests/api/api_smoke -v",
        }
    try:
        payload = _json.loads(smoke_path.read_text(encoding="utf-8"))
        payload.setdefault("project", project_key)
        payload["projectKey"] = project_key
        return payload
    except Exception as exc:
        return {
            "project": project_key,
            "projectKey": project_key,
            "website_url": "",
            "ran_at": None,
            "summary": {"total": 0, "up": 0, "degraded": 0, "down": 0, "skipped": 0},
            "endpoints": [],
            "_error": f"failed to read {smoke_path.name}: {exc}",
        }


@router.get("/api/api-monitor/trends")
async def get_api_monitor_trends(
    hours: int = 24,
    endpoint_name: str | None = None,
    project: str = "west-kowloon",
):
    """Time series for the API monitor trend chart.

    Returns:
      summary: list of run-level points {ran_at, total, up, degraded, down, skipped}
      latency: list of run-level avg-latency points {ran_at, avg_latency_ms}
      endpoint: present only if endpoint_name given — per-run latency + status for that one endpoint

    `hours` clamps the lookback window (1..720). Default 24h.
    """
    hours = max(1, min(int(hours or 24), 720))
    project_key = _project_key(project)
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    db = get_db()
    try:
        _ingest_latest_api_smoke_json(db, project_key)
        runs = (
            db.query(ApiMonitorRun)
            .filter(
                ApiMonitorRun.ran_at >= cutoff,
                ApiMonitorRun.project.in_(list(_project_match_values(project_key))),
            )
            .order_by(ApiMonitorRun.ran_at.asc())
            .all()
        )
        summary_series = [
            {
                "ran_at": r.ran_at.isoformat(timespec="seconds") + "Z",
                "total": r.total,
                "up": r.up,
                "degraded": r.degraded,
                "down": r.down,
                "skipped": r.skipped,
            }
            for r in runs
        ]
        # Avg latency per run (only counts endpoints that have latency_ms)
        latency_series = []
        endpoint_series = []
        for r in runs:
            lat_rows = [e.latency_ms for e in r.endpoints if e.latency_ms is not None]
            avg = round(sum(lat_rows) / len(lat_rows), 1) if lat_rows else None
            latency_series.append({
                "ran_at": r.ran_at.isoformat(timespec="seconds") + "Z",
                "avg_latency_ms": avg,
                "sample_count": len(lat_rows),
            })
            if endpoint_name:
                match = next((e for e in r.endpoints if e.name == endpoint_name), None)
                if match is not None:
                    endpoint_series.append({
                        "ran_at": r.ran_at.isoformat(timespec="seconds") + "Z",
                        "status": match.status,
                        "latency_ms": match.latency_ms,
                        "actual_status_code": match.actual_status_code,
                    })
        out = {
            "project": project_key,
            "hours": hours,
            "run_count": len(runs),
            "summary": summary_series,
            "latency": latency_series,
        }
        if endpoint_name:
            out["endpoint_name"] = endpoint_name
            out["endpoint"] = endpoint_series
        return out
    finally:
        db.close()


@router.get("/api/api-monitor/layers")
async def get_api_monitor_layers(project: str = "west-kowloon"):
    """Per-layer (api_smoke / api_contract / api_functional / ui_smoke / api_ui_mixed) test result counts
    from the latest pytest run of project 02-automation/02-tests."""
    import json as _json
    project_key = _project_key(project)
    layer_path = _api_layer_path(project_key)
    if not layer_path.exists():
        return {
            "project": project_key,
            "ran_at": None,
            "layers": [],
            "_note": "No layer summary on record yet. Run from the project automation root: pytest 02-tests/api -v",
        }
    try:
        payload = _json.loads(layer_path.read_text(encoding="utf-8"))
        payload.setdefault("project", project_key)
        return payload
    except Exception as exc:
        return {"project": project_key, "ran_at": None, "layers": [], "_error": str(exc)}


