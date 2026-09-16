"""
Test Automation Dashboard — FastAPI Backend

Start the server:
    cd <qa-harness root>
    pip install -r dashboard/backend/requirements.txt
    uvicorn dashboard.backend.main:app --reload --port 8002

API endpoints:
    POST /api/runs               -> start a new behave test run
    GET  /api/runs               -> list recent runs (newest first)
    GET  /api/runs/{id}          -> run detail + scenario results
    POST /api/runs/{id}/rerun    -> rerun only the failed scenarios from a run
    WS   /ws/runs/{id}           -> live log stream (WebSocket)
    GET  /api/features           -> list features and tags from .feature files
    GET  /api/stats/trends       -> pass rate trend data for charts
    GET  /api/stats/errors/{id}  -> smart error analysis for a run
    GET  /api/stats/flaky        -> flaky test detection
"""

import asyncio
import csv
import json
import os
import re
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

# Auto-load env vars from the current project automation env folder.
# This must run BEFORE main.py reads GRAFANA_DASHBOARD_UID etc. below.
_backend_root = Path(__file__).resolve().parent
_dashboard_root = _backend_root.parent
_platform_root = _dashboard_root.parent
_repo_root = _platform_root.parent
_workspace_root = Path(os.environ.get("QA_WORKSPACE_ROOT", _repo_root.parent)).resolve()
_westk_root = Path(os.environ.get("QA_WESTK_ROOT", _workspace_root / "west-kowloon")).resolve()
_project_automation_root = _westk_root / "02-automation"
if not _project_automation_root.exists():
    _project_automation_root = _repo_root / "02-platform" / "01-automation"
_features_root = _project_automation_root / "01-features"
_tests_root = _project_automation_root / "02-tests"
_tools_root = _project_automation_root / "04-tools"
_envs_root = _project_automation_root / "06-envs"
_artifacts_root = _project_automation_root / "07-artifacts"
_project_evidence_root = _westk_root / "03-evidence"
_env_name = os.environ.get("ENV", "local")
_env_files = [
    _envs_root / f".env.{_env_name}",
    _repo_root / "02-platform" / "01-automation" / "06-envs" / f".env.{_env_name}",
]
for _ef in _env_files:
    if not _ef.exists():
        continue
    for _line in _ef.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import (
    DASHBOARD_SCHEMA_VERSION, DB_PATH, ApiMonitorEndpointResult, ApiMonitorRun,
    PerformanceRunConfig, ScenarioBug, TestRun, TestScenario, get_db, init_db,
    reconcile_interrupted_runs,
)
from error_analyzer import analyze_run_errors, detect_flaky_tests
from metrics_client import (
    MetricsClient, MetricsConfig, generate_mock_perf_report,
    generate_mock_flamegraph, generate_mock_logs,
)
from project_catalog import ProjectCatalog, ProjectCatalogError
from runner import DEFAULT_DASHBOARD_TAGS, BehaveRunner
from story_case_generator import (
    STORY_RULES,
    generate_login_registration_core_workbook,
    generate_story_workbook,
    generated_file_path,
)

project_catalog = ProjectCatalog(
    workspace_root=_workspace_root,
    harness_root=_repo_root,
    config_path=_dashboard_root / "projects.json",
)
PROJECT_CATALOG = project_catalog.projects
DEFAULT_PROJECT_KEY = project_catalog.default_project

# Make the qa-harness tools dir importable so we can load package_scanner.
import sys as _sys  # local alias; the top-level `import sys` happens later
_tools_dir = _repo_root / "01-system" / "03-tools"
if str(_tools_dir) not in _sys.path:
    _sys.path.insert(0, str(_tools_dir))
try:
    import package_scanner  # noqa: E402
except Exception as _e:
    package_scanner = None
    print(f"[warn] package_scanner not available: {_e}")

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    init_db()
    recovered = reconcile_interrupted_runs()
    app_instance.state.recovered_interrupted_runs = recovered
    yield


app = FastAPI(title="Test Automation Dashboard API", lifespan=lifespan)

# Allow Vite dev servers to call the backend directly when not using the proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = str(_project_automation_root)
FEATURES_ROOT = _features_root
TESTS_ROOT = _tests_root
TOOLS_ROOT = _tools_root
ARTIFACTS_ROOT = _artifacts_root
PROJECT_EVIDENCE_ROOT = _project_evidence_root

runner = BehaveRunner(PROJECT_ROOT, FEATURES_ROOT, ARTIFACTS_ROOT,
                      project_key="west-kowloon")
_runner_cache: dict[str, BehaveRunner] = {"west-kowloon": runner}

# Metrics client for Prometheus / Grafana integration
metrics_config = MetricsConfig(
    prometheus_url=os.environ.get("PROMETHEUS_URL", "http://localhost:9090"),
    grafana_url=os.environ.get("GRAFANA_URL", "http://localhost:3000"),
    grafana_api_key=os.environ.get("GRAFANA_API_KEY", ""),
    grafana_dashboard_uid=os.environ.get("GRAFANA_DASHBOARD_UID", ""),
    pyroscope_url=os.environ.get("PYROSCOPE_URL", "http://localhost:4040"),
    loki_url=os.environ.get("LOKI_URL", "http://localhost:3100"),
    toxiproxy_url=os.environ.get("TOXIPROXY_URL", "http://localhost:8474"),
)
metrics_client = MetricsClient(metrics_config)

PERF_EVIDENCE_ROOT = Path(
    os.environ.get("QA_PERF_EVIDENCE_ROOT", _project_evidence_root / "performance")
).resolve()
PERF_ARTIFACT_PREFIX = PERF_EVIDENCE_ROOT / "latest" / "perf_latest"
PERF_ARTIFACT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
PERF_LOG_LIMIT = 200
perf_state = {
    "status": "idle",
    "project": None,
    "run_id": None,
    "pid": None,
    "started_at": None,
    "finished_at": None,
    "exit_code": None,
    "config": None,
    "artifacts_prefix": str(PERF_ARTIFACT_PREFIX),
    "logs": deque(maxlen=PERF_LOG_LIMIT),
    "error": None,
    "total_requests": 0,
    "total_failures": 0,
    "error_rate": 0,
}


@app.get("/api/projects")
def list_projects():
    """Return the project catalog that drives the dashboard project switcher."""
    projects = []
    for item in PROJECT_CATALOG:
        project_root = _workspace_root / item["workspace"]
        package_count = None
        if package_scanner is not None and project_root.exists():
            try:
                package_count = len(package_scanner.find_packages(project_root))
            except Exception:
                package_count = None
        projects.append({
            **item,
            "exists": project_root.exists(),
            "root": str(project_root).replace("\\", "/"),
            "requirementRoot": str(project_root / "01-requirements").replace("\\", "/"),
            "packageCount": package_count,
        })
    return {
        "configVersion": project_catalog.version,
        "configPath": str(project_catalog.config_path).replace("\\", "/"),
        "defaultProject": DEFAULT_PROJECT_KEY,
        "workspaceRoot": str(_workspace_root).replace("\\", "/"),
        "projects": projects,
    }


@app.get("/api/health")
def dashboard_health():
    return {
        "status": "ok",
        "database": str(DB_PATH).replace("\\", "/"),
        "schemaVersion": DASHBOARD_SCHEMA_VERSION,
        "projectConfigVersion": project_catalog.version,
        "recoveredInterruptedRuns": getattr(
            app.state, "recovered_interrupted_runs", 0
        ),
    }


# Serve evidence screenshots over HTTP so they can be embedded as <img> in
# ZenTao bugs. ZenTao SaaS strips data: URLs (verified 2026-05-23) but keeps
# <img src="http://..."> intact, so this is how screenshots reach a bug page.
_SHOTS_DIR = ARTIFACTS_ROOT / "screenshots"
if _SHOTS_DIR.exists():
    app.mount("/screenshots",
              StaticFiles(directory=str(_SHOTS_DIR)),
              name="screenshots")


@app.get("/project-screenshots/{project}/{asset_path:path}", include_in_schema=False)
def project_screenshot(project: str, asset_path: str):
    """Serve screenshot evidence from the explicitly selected project."""
    shots_root = _automation_paths(project)["artifacts_root"] / "screenshots"
    target = (shots_root / asset_path).resolve()
    try:
        target.relative_to(shots_root.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="screenshot not found") from exc
    if not target.is_file():
        raise HTTPException(status_code=404, detail="screenshot not found")
    return FileResponse(target)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    """Body for POST /api/runs."""
    project: str = "west-kowloon"            # dashboard project key
    tags: Optional[str] = None              # e.g. "@hybrid" or "@api,@antank"
    features: Optional[list[str]] = None    # feature-file paths — restrict run to these modules
    names: Optional[list[str]] = None       # scenario names (regex-matched via --name)
    env: str = "local"                      # local | sit | uat
    package_id: Optional[str] = None        # workspace-relative package context; audit only for now


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/runs")
async def create_run(req: RunRequest):
    """Start a new behave test run. Returns immediately with the run ID.
    The actual behave process runs in the background (asyncio task).
    Connect to /ws/runs/{id} for live log streaming."""
    project_key = _project_key(req.project)
    paths = _automation_paths(project_key)
    if not paths["features_root"].exists():
        return {
            "error": (
                f"No feature directory for project {project_key}: "
                f"{paths['features_root']}"
            )
        }
    effective_tags = req.tags or DEFAULT_DASHBOARD_TAGS
    db = get_db()
    try:
        run = TestRun(
            started_at=datetime.utcnow(),
            status="running",
            env=req.env,
            project_key=project_key,
            tags=effective_tags,
            run_kind="full",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id
    finally:
        db.close()

    # Fire-and-forget: run behave in the background
    asyncio.create_task(_execute_run(run_id, effective_tags, req.env,
                                     names=req.names, features=req.features,
                                     project=project_key))

    return {"id": run_id, "status": "running"}


@app.get("/api/runs")
def list_runs(
    project: str = "west-kowloon",
    kind: str = "full",
    include_reruns: bool = False,
):
    """List recent functional test runs for the Test Run page.

    Performance runs belong to the dedicated Performance Test page. Mixing
    them into this history makes transaction metrics look like functional
    scenarios, which leaves Case ID and automation metadata empty.
    """
    project_key = _project_key(project)
    requested_kind = (kind or "full").strip().lower()
    db = get_db()
    try:
        query = db.query(TestRun).filter(TestRun.project_key == project_key)
        if requested_kind == "all":
            if not include_reruns:
                query = query.filter(~TestRun.run_kind.in_(["rerun_single", "rerun_failed"]))
        elif requested_kind in {"full", "dashboard", "history"}:
            visible_kinds = ["full"]
            if include_reruns:
                visible_kinds.extend(["rerun_single", "rerun_failed"])
            query = query.filter(TestRun.run_kind.in_(visible_kinds))
        else:
            query = query.filter(TestRun.run_kind == requested_kind)
        runs = query.order_by(TestRun.id.desc()).limit(20).all()
        return [_run_dict(r) for r in runs]
    finally:
        db.close()


@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: int):
    """Get a single run's summary + all its scenario results.

    Scenarios linked to a ZenTao bug get a live `zentao_bug_status` field
    (active | resolved | closed | unknown) so the dashboard reflects the
    bug's current lifecycle stage, not just whether one was ever opened."""
    db = get_db()
    try:
        run = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not run:
            return {"error": "Run not found"}
        scenarios = (
            db.query(TestScenario)
            .filter(TestScenario.run_id == run_id)
            .all()
        )
        latest_attempts = _scenario_latest_attempts(db, scenarios, run.project_key)
        scenario_dicts = _enrich_bug_statuses([
            _scenario_dict(
                s,
                run.project_key,
                run=run,
                latest_attempt=latest_attempts.get(
                    _case_id_from_scenario_fields(s.name, s.tags)
                ),
            )
            for s in scenarios
        ])
        return {
            **_run_dict(run),
            "scenarios": scenario_dicts,
        }
    finally:
        db.close()


@app.post("/api/runs/{run_id}/rerun")
async def rerun_failed(run_id: int):
    """Rerun failed or errored scenarios from a previous run.
    Creates a new run with the same env/tags but filtered to problem scenario names."""
    db = get_db()
    try:
        original = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not original:
            return {"error": "Run not found"}

        problem_scenarios = (
            db.query(TestScenario)
            .filter(
                TestScenario.run_id == run_id,
                TestScenario.status.in_(["failed", "error", "undefined", "untested"]),
            )
            .all()
        )
        if not problem_scenarios:
            return {"error": "No failed or errored scenarios to rerun"}

        problem_names = [s.name for s in problem_scenarios]

        # Capture the original run's settings into plain locals NOW, while the
        # session is still open. db.commit() below expires every attribute on
        # `original` (expire_on_commit defaults to True), and db.close() in the
        # finally block detaches the instance — so any `original.<attr>` access
        # afterwards triggers a refresh on a session-less object and raises
        # DetachedInstanceError. That exception fired before _execute_run was
        # ever scheduled, which is why Rerun produced a 500 and no log.
        orig_tags = original.tags or DEFAULT_DASHBOARD_TAGS
        orig_env = original.env
        orig_project = original.project_key or "west-kowloon"
        parent_run_id = (
            original.id
            if (original.run_kind or "full") == "full"
            else (original.parent_run_id or original.id)
        )

        new_run = TestRun(
            started_at=datetime.utcnow(),
            status="running",
            env=orig_env,
            project_key=orig_project,
            tags=orig_tags,
            run_kind="rerun_failed",
            parent_run_id=parent_run_id,
            rerun_scope="failed_or_errored",
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)
        new_id = new_run.id
    finally:
        db.close()

    asyncio.create_task(
        _execute_run(new_id, orig_tags, orig_env, names=problem_names,
                     project=orig_project)
    )

    return {"id": new_id, "status": "running"}


@app.post("/api/scenarios/{scenario_id}/rerun")
async def rerun_one_scenario(scenario_id: int):
    """Rerun ONE scenario from a previous run — pinpoint debugging without
    re-executing the entire suite. Spawns a new run with `--name <scenario>`
    so behave only executes that single matching scenario; env/tags are
    inherited from the original run (so SIT data + tag filters stay)."""
    db = get_db()
    try:
        s = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
        if not s:
            return {"error": f"scenario {scenario_id} not found"}

        # Pull the source run's env + tags so the rerun matches the original
        # selection criteria. Capture before commit/close (see comment above
        # in rerun_failed for the DetachedInstanceError trap).
        src = db.query(TestRun).filter(TestRun.id == s.run_id).first()
        env = src.env if src else "sit"
        tags = (src.tags if src else None) or DEFAULT_DASHBOARD_TAGS
        project_key = (src.project_key if src else None) or "west-kowloon"
        parent_run_id = (
            src.id
            if src and (src.run_kind or "full") == "full"
            else ((src.parent_run_id if src else None) or s.run_id)
        )
        name = s.name

        new_run = TestRun(
            started_at=datetime.utcnow(),
            status="running",
            env=env,
            project_key=project_key,
            tags=tags,
            run_kind="rerun_single",
            parent_run_id=parent_run_id,
            rerun_scope="single",
            source_scenario_id=s.id,
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)
        new_id = new_run.id
    finally:
        db.close()

    asyncio.create_task(
        _execute_run(new_id, tags, env, names=[name], project=project_key)
    )

    return {"id": new_id, "status": "running", "scenario": name}


# ---------------------------------------------------------------------------
# Evidence sync — run tools/update_evidence.py to refresh the Kasi workbook
# (screenshots + result columns), scoped to the selected feature modules.
# ---------------------------------------------------------------------------

import subprocess          # noqa: E402
import sys                 # noqa: E402
import threading           # noqa: E402

_sync_state = {
    "running": False, "log": [], "started_at": None,
    "finished_at": None, "exit_code": None, "scope": None,
}


class SyncRequest(BaseModel):
    """Body for POST /api/sync-evidence."""
    project: str = "west-kowloon"
    features: Optional[list[str]] = None   # feature-file paths — scope the sync
    env: str = "sit"


def _cases_for_features(features, project: str = "west-kowloon") -> list[str]:
    """Read selected .feature files and collect case IDs for evidence sync.

    West Kowloon's legacy update_evidence.py expects short numeric IDs. Newer
    projects use the full SIT-TC-... ID as the cross-project evidence key.
    """
    paths = _automation_paths(project)
    cases: set[str] = set()
    project_key = _project_key(project)
    for feat in features or []:
        fpath = paths["automation_root"] / feat
        if not fpath.exists() and feat.startswith("features/"):
            fpath = paths["features_root"] / feat.removeprefix("features/")
        if not fpath.exists() and "/" not in feat and "\\" not in feat:
            fpath = paths["features_root"] / feat
        if fpath.exists():
            text = fpath.read_text(encoding="utf-8")
            full_ids = {
                match.group(1).upper()
                for match in re.finditer(r"\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b", text, re.I)
            }
            if project_key == "west-kowloon":
                cases.update(case_id.rsplit("-", 1)[-1] for case_id in full_ids)
            else:
                cases.update(full_ids)
    return sorted(cases)


def _run_sync(cases: list[str], env: str, project: str):
    """Run tools/update_evidence.py as a subprocess, streaming stdout into
    the in-memory _sync_state log."""
    paths = _automation_paths(project)
    tool_path = paths["tools_root"] / "update_evidence.py"
    if not tool_path.exists():
        _sync_state["log"].append(f"[sync error] update_evidence.py not found: {tool_path}")
        _sync_state["exit_code"] = -1
        _sync_state["running"] = False
        _sync_state["finished_at"] = datetime.utcnow().isoformat()
        return
    cmd = [sys.executable, str(tool_path)] + cases
    proc_env = dict(os.environ)
    proc_env["ENV"] = env
    proc_env["QA_PROJECT_KEY"] = project
    proc_env["QA_PROJECT_AUTOMATION_ROOT"] = str(paths["automation_root"])
    proc_env["QA_WORKSPACE_ROOT"] = str(_workspace_root)
    proc_env["PYTHONIOENCODING"] = "utf-8"
    proc_env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.Popen(
            cmd, cwd=paths["automation_root"], env=proc_env, text=True,
            encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        for line in proc.stdout:
            _sync_state["log"].append(line.rstrip("\n"))
            _sync_state["log"] = _sync_state["log"][-400:]
        proc.wait()
        _sync_state["exit_code"] = proc.returncode
    except Exception as exc:                                  # noqa: BLE001
        _sync_state["log"].append(f"[sync error] {exc}")
        _sync_state["exit_code"] = -1
    finally:
        _sync_state["running"] = False
        _sync_state["finished_at"] = datetime.utcnow().isoformat()


@app.post("/api/sync-evidence")
def start_sync_evidence(req: SyncRequest):
    """Refresh the Kasi test-case workbook (result columns + embedded step
    screenshots) by running tools/update_evidence.py. Scoped to the selected
    feature modules; empty selection = every case. Returns immediately;
    poll GET /api/sync-evidence for progress."""
    if _sync_state["running"]:
        return {"status": "already running", "scope": _sync_state["scope"]}

    project_key = _project_key(req.project)
    cases = _cases_for_features(req.features, project_key)
    scope = (", ".join(Path(f).stem for f in req.features)
             if req.features else "all cases")
    _sync_state.update(running=True, log=[], exit_code=None,
                       started_at=datetime.utcnow().isoformat(),
                       finished_at=None, scope=f"{project_key}: {scope}")
    threading.Thread(target=_run_sync, args=(cases, req.env, project_key), daemon=True).start()
    return {"status": "running", "project": project_key, "scope": scope, "cases": cases or "all"}


@app.get("/api/sync-evidence")
def sync_evidence_status():
    """Current evidence-sync status + the tail of the log."""
    return {
        "running": _sync_state["running"],
        "scope": _sync_state["scope"],
        "started_at": _sync_state["started_at"],
        "finished_at": _sync_state["finished_at"],
        "exit_code": _sync_state["exit_code"],
        "log": _sync_state["log"][-80:],
    }


@app.get("/api/evidence-status")
def evidence_status(project: str = "west-kowloon"):
    """Per-case 'synced to the Kasi workbook' status, written by
    tools/update_evidence.py (artifacts/evidence_sync.json). The Test Results
    table joins this by case ID to show a 'Sync to Excel' column.

    Runtime Behave screenshots are also merged from
    case-screenshot-manifest-latest.json so projects without a workbook sync
    tool can still show case-level screenshot availability.
    """
    import json
    project_key = _project_key(project)
    paths = _automation_paths(project_key)
    f = _automation_paths(project_key)["artifacts_root"] / "evidence_sync.json"
    payload = {"project": project_key, "updated_at": None, "cases": {}}
    if not f.exists():
        pass
    else:
        try:
            loaded = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payload.update(loaded)
        except Exception:                                  # noqa: BLE001
            payload = {"project": project_key, "updated_at": None, "cases": {}}
    payload.setdefault("project", project_key)
    payload["cases"] = _normalise_evidence_cases(payload.get("cases") or {})
    _merge_runtime_screenshot_manifest(payload, paths["artifacts_root"])
    return payload


def _case_id_key(value: object) -> str | None:
    match = re.search(r"\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b", str(value or ""), re.I)
    return match.group(1).upper() if match else None


def _case_short_key(value: object) -> str | None:
    full = _case_id_key(value)
    if full:
        return full.rsplit("-", 1)[-1]
    match = re.fullmatch(r"\d{3,}", str(value or "").strip())
    return match.group(0) if match else None


def _normalise_evidence_cases(raw_cases: dict) -> dict:
    normalised: dict[str, dict] = {}
    if not isinstance(raw_cases, dict):
        return normalised
    for key, value in raw_cases.items():
        rec = dict(value or {}) if isinstance(value, dict) else {}
        full = _case_id_key(rec.get("case_id") or key)
        short = _case_short_key(rec.get("case_id") or key)
        if full:
            rec["case_id"] = full
            normalised[full] = rec
        if short:
            normalised[short] = rec
    return normalised


def _merge_runtime_screenshot_manifest(payload: dict, artifacts_root: Path) -> None:
    candidates = sorted(
        artifacts_root.rglob("case-screenshot-manifest-run-*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    if not candidates:
        candidates = sorted(
            artifacts_root.rglob("case-screenshot-manifest-latest.json"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
    if not candidates:
        return

    latest_manifest = None
    latest_manifest_path = None
    evidence_cases = payload.setdefault("cases", {})
    seen_with_screenshots: set[str] = set()
    seen_any: set[str] = set()

    for manifest_path in candidates:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:                                  # noqa: BLE001
            continue
        cases = manifest.get("cases") or {}
        if not isinstance(cases, dict):
            continue
        if latest_manifest is None:
            latest_manifest = manifest
            latest_manifest_path = manifest_path

        for raw_case_id, raw_case in cases.items():
            case_id = _case_id_key(raw_case_id)
            if not case_id or not isinstance(raw_case, dict):
                continue
            screenshots = raw_case.get("screenshots") or []
            if not isinstance(screenshots, list):
                screenshots = []
            short = case_id.rsplit("-", 1)[-1]
            rec = dict(evidence_cases.get(case_id) or evidence_cases.get(short) or {})
            has_screenshots = len(screenshots) > 0

            # Keep the newest per-case runtime metadata, but do not let a
            # later skipped/no-screenshot rerun wipe out the latest usable
            # screenshot evidence from a full run.
            if case_id not in seen_any:
                rec.update({
                    "case_id": case_id,
                    "latest_runtime_run_id": manifest.get("run_id"),
                    "latest_runtime_status": raw_case.get("status"),
                    "latest_runtime_scenario": raw_case.get("scenario"),
                    "latest_runtime_manifest": str(manifest_path).replace("\\", "/"),
                    "latest_runtime_finished_at": raw_case.get("finished_at") or manifest.get("updated_at"),
                })
                seen_any.add(case_id)

            if has_screenshots and case_id not in seen_with_screenshots:
                rec.update({
                    "case_id": case_id,
                    "has_screenshot": True,
                    "shots": len(screenshots),
                    "screenshot_count": len(screenshots),
                    "screenshots": screenshots,
                    "runtime_run_id": manifest.get("run_id"),
                    "runtime_status": raw_case.get("status"),
                    "runtime_scenario": raw_case.get("scenario"),
                    "runtime_manifest": str(manifest_path).replace("\\", "/"),
                    "runtime_finished_at": raw_case.get("finished_at") or manifest.get("updated_at"),
                    "status": "Runtime screenshots",
                })
                seen_with_screenshots.add(case_id)
            else:
                rec.setdefault("case_id", case_id)
                rec.setdefault("has_screenshot", False)
                rec.setdefault("shots", 0)
                rec.setdefault("screenshot_count", 0)
                rec.setdefault("screenshots", [])
                rec.setdefault("status", "No screenshot")

            rec.setdefault("synced", False)
            evidence_cases[case_id] = rec
            evidence_cases[short] = rec

    if latest_manifest is not None:
        payload["updated_at"] = payload.get("updated_at") or latest_manifest.get("updated_at")
        payload["runtime_screenshot_manifest"] = str(latest_manifest_path).replace("\\", "/")
        payload["runtime_run_id"] = latest_manifest.get("run_id")


# ---------------------------------------------------------------------------
# Quality evidence packages — durable manifests promoted into 03-evidence.
# The dashboard uses this as the evidence-backed layer for Quality System
# deliverables and gates. Runtime artifacts remain under 02-automation.
# ---------------------------------------------------------------------------

QUALITY_REQUIRED_DELIVERABLES = ["p5-d1", "p5-d2", "p5-d4", "p6-d3", "p6-d4"]


def _rel_to_evidence(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_workspace_root)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _safe_manifest_payload(path: Path) -> tuple[dict | None, dict | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001
        return None, {"path": _rel_to_evidence(path), "error": str(exc)}


def _package_from_manifest(path: Path, manifest: dict) -> dict:
    gate = manifest.get("gate") or {}
    source = manifest.get("source") or {}
    summary = manifest.get("summary") or {}
    artifacts = manifest.get("artifacts") or []
    deliverables = manifest.get("qualityDeliverables") or []
    report = path.parent / "evidence-report.md"
    trusted = bool(gate.get("trusted")) and manifest.get("status") != "rejected"

    return {
        "packageId": manifest.get("packageId") or path.parent.name,
        "path": _rel_to_evidence(path.parent),
        "manifestPath": _rel_to_evidence(path),
        "reportPath": _rel_to_evidence(report) if report.exists() else None,
        "project": manifest.get("project"),
        "module": manifest.get("module"),
        "subproject": manifest.get("subproject"),
        "evidenceType": manifest.get("evidenceType"),
        "status": manifest.get("status"),
        "promotedAt": manifest.get("promotedAt"),
        "promotedBy": manifest.get("promotedBy"),
        "environment": manifest.get("environment"),
        "build": manifest.get("build"),
        "runId": source.get("dashboardRunId"),
        "summary": {
            "scenarioCount": summary.get("scenarioCount", 0),
            "executed": summary.get("executed", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "errored": summary.get("errored", 0),
            "skipped": summary.get("skipped", 0),
            "passRate": summary.get("passRate", 0),
            "testCaseIds": summary.get("testCaseIds", []),
        },
        "qualityDeliverables": deliverables,
        "artifactCount": len(artifacts),
        "gate": {
            "status": gate.get("status", "UNKNOWN"),
            "trusted": trusted,
            "blockingIssues": gate.get("blockingIssues", []),
            "warnings": gate.get("warnings", []),
            "checkedAt": gate.get("checkedAt"),
        },
    }


@app.get("/api/quality/evidence")
def quality_evidence_status(project: str = "west-kowloon"):
    """Evidence package coverage for Quality System deliverables.

    Scans the selected project's 03-evidence/**/manifest.json files. Only packages
    whose manifest gate is trusted count as evidence-backed deliverables.
    """
    project_key = _project_key(project)
    manifests_root = _automation_paths(project_key)["evidence_root"]
    packages = []
    errors = []
    for path in sorted(manifests_root.rglob("manifest.json")) if manifests_root.exists() else []:
        manifest, error = _safe_manifest_payload(path)
        if error:
            errors.append(error)
            continue
        if manifest.get("schemaVersion") != "wk-evidence-manifest/v1":
            errors.append({
                "path": _rel_to_evidence(path),
                "error": f"unsupported schemaVersion: {manifest.get('schemaVersion')}",
            })
            continue
        packages.append(_package_from_manifest(path, manifest))

    packages.sort(key=lambda p: p.get("promotedAt") or "", reverse=True)
    deliverables: dict[str, dict] = {}
    for package in packages:
        for deliverable_id in package.get("qualityDeliverables", []):
            entry = deliverables.setdefault(deliverable_id, {
                "packageCount": 0,
                "trustedCount": 0,
                "latestPackage": None,
                "blockingIssues": [],
            })
            entry["packageCount"] += 1
            if package["gate"]["trusted"]:
                entry["trustedCount"] += 1
                if not entry["latestPackage"]:
                    entry["latestPackage"] = package
            else:
                entry["blockingIssues"].extend(package["gate"].get("blockingIssues") or [])
                if not entry["latestPackage"]:
                    entry["latestPackage"] = package

    missing_trusted = [
        d for d in QUALITY_REQUIRED_DELIVERABLES
        if deliverables.get(d, {}).get("trustedCount", 0) == 0
    ]
    blocking = []
    if not packages:
        blocking.append("No promoted evidence packages found under 03-evidence.")
    if missing_trusted:
        blocking.append(
            "Missing trusted evidence for deliverables: " + ", ".join(missing_trusted)
        )
    if errors:
        blocking.append(f"{len(errors)} manifest(s) could not be loaded.")

    trusted_packages = [p for p in packages if p["gate"]["trusted"]]
    return {
        "project": project_key,
        "evidenceRoot": str(manifests_root).replace("\\", "/"),
        "requiredDeliverables": QUALITY_REQUIRED_DELIVERABLES,
        "summary": {
            "packageCount": len(packages),
            "trustedPackageCount": len(trusted_packages),
            "deliverableCount": len(deliverables),
            "trustedDeliverableCount": sum(
                1 for d in deliverables.values() if d.get("trustedCount", 0) > 0
            ),
        },
        "gate": {
            "trusted": not blocking,
            "status": "PASS" if not blocking else "FAIL",
            "blockingIssues": blocking,
            "checkedAt": datetime.utcnow().isoformat(),
        },
        "deliverables": deliverables,
        "packages": packages,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Case history — execution-result history for one test case. Runtime evidence
# is attached to the matching execution row; screenshot batches and bugs are
# not emitted as independent history events.
# Endpoint:  GET /api/history/case/{case_id}
# case_id may be a full "SIT-TC-...-034" id. A bare 3-digit id remains
# backward-compatible with the legacy "SIT-TC-WEB-AUTH-034" cases.
# ---------------------------------------------------------------------------

# Derive from the repo root rather than hardcoding the install drive — keeps
# this file portable across machines / parallel checkouts. _repo_root was
# computed near the top of main.py and points at the qa-harness repo root.
_KASI_XLSX = (
    _westk_root / "01-requirements" / "02-subprojects" / "02-website" /
    "02-modules" / "01-login-registration" / "2026-06-16" / "03-test-design" /
    "test-cases-registration-login.xlsx"
)


def _normalise_case_id(raw: str) -> tuple[str, str]:
    """Return (full_case_id, trailing_digits) for full ids or legacy digits."""
    value = (raw or "").strip().upper()
    full = re.search(r"\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b", value)
    if full:
        case_full = full.group(1)
        digits_match = re.search(r"(\d{3,})$", case_full)
        return (case_full, digits_match.group(1) if digits_match else "")

    digits = re.sub(r"\D", "", value)
    if not digits:
        return ("", "")
    digits = digits.zfill(3)
    return (f"SIT-TC-WEB-AUTH-{digits}", digits)


def _behave_runs_for_case(db, case_full: str) -> list[dict]:
    """All Behave scenarios for this case across runs (joined with run)."""
    from sqlalchemy import func, or_
    q = (db.query(TestScenario, TestRun)
           .join(TestRun, TestScenario.run_id == TestRun.id)
           .filter(or_(TestScenario.name.like(f"%{case_full}%"),
                       TestScenario.tags.like(f"%{case_full}%"),
                       TestScenario.name.like(f"%{case_full} %"))))
    out = []
    for s, r in q.all():
        technical_status = str(s.status or "").strip().lower()
        execution_result = _execution_result_from_technical_status(technical_status)
        if not execution_result:
            continue
        automation_type = _automation_type_for_scenario(s, r)
        run_kind = r.run_kind or "full"
        out.append({
            "type": "behave",
            "timestamp": (
                _run_event_timestamp(r).isoformat()
                if _run_event_timestamp(r) else None
            ),
            "run_id": r.id,
            "run_kind": run_kind,
            "parent_run_id": r.parent_run_id,
            "rerun_scope": r.rerun_scope,
            "is_rerun": run_kind.startswith("rerun"),
            "scenario_id": s.id,
            "case_id": case_full,
            "scenario_name": s.name,
            "status": "passed" if execution_result == "Pass" else "failed",
            "execution_result": execution_result,
            "technical_status": technical_status,
            "duration_s": s.duration_s,
            "error_msg": s.error_msg,
            "env": r.env,
            "automation_type": automation_type,
            "tags": s.tags,
        })
    return out


def _behave_attempt_summary_for_case(db, case_full: str) -> dict:
    """Attempt counters include skipped/running rows; timeline does not."""
    from sqlalchemy import or_

    q = (db.query(TestScenario, TestRun)
           .join(TestRun, TestScenario.run_id == TestRun.id)
           .filter(or_(TestScenario.name.like(f"%{case_full}%"),
                       TestScenario.tags.like(f"%{case_full}%"),
                       TestScenario.name.like(f"%{case_full} %"))))
    attempts = q.all()
    execution_results = [
        (s, r) for s, r in attempts
        if _execution_result_from_technical_status(s.status)
    ]
    reruns = [
        (s, r) for s, r in attempts
        if (r.run_kind or "full") != "full"
    ]
    return {
        "attempts": len(attempts),
        "execution_results": len(execution_results),
        "reruns": len(reruns),
    }


def _attach_evidence_to_execution_events(events: list[dict], evidence: list[dict]) -> None:
    """Attach runtime evidence to matching execution rows.

    Case history is execution-centric: evidence is proof for a run, not a
    separate history event. Only evidence with screenshots is surfaced.
    """
    evidence_by_run: dict[str, list[dict]] = {}
    for item in evidence:
        if int(item.get("screenshot_count") or 0) <= 0:
            continue
        run_id = item.get("run_id")
        if run_id is None:
            continue
        evidence_by_run.setdefault(str(run_id), []).append(item)

    for event in events:
        matches = evidence_by_run.get(str(event.get("run_id")), [])
        screenshot_files: list[str] = []
        screenshot_urls: list[str] = []
        evidence_locations: list[str] = []
        for item in matches:
            screenshot_files.extend([
                path for path in (item.get("screenshot_files") or []) if path
            ])
            screenshot_urls.extend([
                url for url in (item.get("screenshot_urls") or []) if url
            ])
            if item.get("case_dir"):
                evidence_locations.append(str(item["case_dir"]))
        event["screenshot_count"] = len(screenshot_files) + len(screenshot_urls)
        event["screenshot_files"] = screenshot_files
        event["screenshot_urls"] = screenshot_urls
        event["evidence_locations"] = evidence_locations


def _execution_result_from_technical_status(status: str | None) -> str | None:
    """Map raw runner states to the human execution result shown in history."""
    value = str(status or "").strip().lower()
    if value in {"passed", "pass", "success", "succeeded"}:
        return "Pass"
    if value in {"failed", "fail", "error", "errored", "undefined", "untested"}:
        return "Fail"
    return None


def _runtime_manifest_evidence_for_case(case_full: str) -> list[dict]:
    out: list[dict] = []
    for project in PROJECT_CATALOG:
        artifacts_root = _automation_paths(project["key"])["artifacts_root"]
        if not artifacts_root.exists():
            continue
        for manifest_path in sorted(artifacts_root.rglob("case-screenshot-manifest-run-*.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:                                  # noqa: BLE001
                continue
            case = (manifest.get("cases") or {}).get(case_full)
            if not isinstance(case, dict):
                continue
            screenshots = case.get("screenshots") or []
            if not isinstance(screenshots, list):
                screenshots = []
            out.append({
                "type": "evidence",
                "timestamp": case.get("finished_at") or manifest.get("updated_at"),
                "evidence_dir": f"runtime-run-{manifest.get('run_id')}",
                "case_dir": str(
                    artifacts_root / "batch_session_configuration" /
                    f"run-{manifest.get('run_id')}" / case_full
                ),
                "screenshot_count": len(screenshots),
                "screenshot_urls": [],
                "screenshot_files": [
                    shot.get("path") for shot in screenshots
                    if isinstance(shot, dict) and shot.get("path")
                ],
                "manifest": str(manifest_path).replace("\\", "/"),
                "project": project["key"],
                "run_id": manifest.get("run_id"),
            })
    return out


def _evidence_runs_for_case(case_short: str, case_full: str | None = None) -> list[dict]:
    """Each `evidence_<TIMESTAMP>/tc<XXX>` directory = one update_evidence.py
    run that touched this case. We read its screenshot list."""
    base = ARTIFACTS_ROOT / "screenshots"
    out = []
    if base.exists():
        for ev_dir in sorted(base.glob("evidence_*")):
            case_dir = ev_dir / f"tc{case_short}"
            if not case_dir.is_dir():
                continue
            shots = sorted(case_dir.glob("*.png"))
            if not shots:
                continue
            # Parse timestamp from evidence dir name 'evidence_YYYYMMDD_HHMMSS'
            m = re.match(r"evidence_(\d{8})_(\d{6})", ev_dir.name)
            ts = None
            if m:
                from datetime import datetime as _dt
                try:
                    ts = _dt.strptime(m.group(1) + m.group(2),
                                       "%Y%m%d%H%M%S").isoformat()
                except Exception:                                # noqa: BLE001
                    pass
            # Build HTTP URLs for each screenshot (served by /screenshots mount)
            rel = case_dir.relative_to(base).as_posix()
            urls = [f"/screenshots/{rel}/{p.name}" for p in shots]
            out.append({
                "type": "evidence",
                "timestamp": ts,
                "evidence_dir": ev_dir.name,
                "case_dir": str(case_dir),
                "screenshot_count": len(shots),
                "screenshot_urls": urls,
            })
    if case_full:
        out.extend(_runtime_manifest_evidence_for_case(case_full))
    return out


def _bugs_for_case(db, scenario_ids: list[int]) -> list[dict]:
    """ZenTao bugs linked to any scenario with this case name. Status
    enrichment via the same TTL cache as get_run_detail."""
    if not scenario_ids:
        return []
    bugs = (db.query(ScenarioBug)
              .filter(ScenarioBug.scenario_id.in_(scenario_ids))
              .all())
    token = _zentao_token()
    out = []
    for b in bugs:
        item = {
            "type": "bug",
            "timestamp": (b.opened_at.isoformat() if b.opened_at else None),
            "bug_id": b.zentao_bug_id,
            "url": b.zentao_bug_url,
            "title": b.title,
            "scenario_id": b.scenario_id,
            "status": None,
        }
        if token:
            try:
                item["status"] = _fetch_bug_status(int(b.zentao_bug_id), token)
            except Exception:                                # noqa: BLE001
                pass
        out.append(item)
    return out


def _current_xlsx_snapshot(case_full: str) -> Optional[dict]:
    """Read the case's current row from the Kasi workbook (latest only —
    xlsx is overwritten on each update_evidence.py run)."""
    if not _KASI_XLSX.exists():
        return None
    try:
        import openpyxl
        wb = openpyxl.load_workbook(_KASI_XLSX, read_only=True, data_only=True)
        ws = wb["Test Cases"]
        # header lookup (handles the Label-column insertion + variants)
        headers = {}
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=1, column=c).value
            if v is not None:
                headers[str(v).strip()] = c
        cid_col = headers.get("Test Case ID")
        if not cid_col:
            return None
        st_col   = next((c for h, c in headers.items() if h.startswith("Status")), None)
        act_col  = headers.get("Actual Result")
        date_col = headers.get("Execution Date")
        for r in range(2, ws.max_row + 1):
            v = str(ws.cell(row=r, column=cid_col).value or "").strip()
            if v == case_full:
                return {
                    "type": "xlsx_current",
                    "row": r,
                    "status":   ws.cell(row=r, column=st_col).value if st_col else None,
                    "actual":   ws.cell(row=r, column=act_col).value if act_col else None,
                    "exec_date": str(ws.cell(row=r, column=date_col).value) if date_col else None,
                }
        return None
    except Exception:                                        # noqa: BLE001
        return None


@app.get("/api/history/case/{case_id}")
def case_history(case_id: str):
    """Execution history for a single test case. Newest first."""
    case_full, case_short = _normalise_case_id(case_id)
    if not case_full:
        return {"error": f"invalid case_id {case_id!r}"}
    db = get_db()
    try:
        behave  = _behave_runs_for_case(db, case_full)
        attempts = _behave_attempt_summary_for_case(db, case_full)
        ev      = _evidence_runs_for_case(case_short, case_full)
        bugs    = _bugs_for_case(db, [b["scenario_id"] for b in behave])
        current = _current_xlsx_snapshot(case_full)
    finally:
        db.close()

    _attach_evidence_to_execution_events(behave, ev)
    events = behave
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return {
        "case_id": case_full,
        "current_xlsx": current,
        "counts": {
            "attempts": attempts["attempts"],
            "reruns": attempts["reruns"],
            "execution_results": len(behave),
            "behave_runs":     len(behave),
            "evidence_batches": len([
                item for item in ev if int(item.get("screenshot_count") or 0) > 0
            ]),
            "bugs":            len(bugs),
        },
        "linked_bugs": bugs,
        "events": events,
    }


# ---------------------------------------------------------------------------
# ZenTao bug push — human-verified one-click open-bug from a failed scenario
# ---------------------------------------------------------------------------

ZENTAO_BASE = "https://lengliwh.chandao.net"


def _zt_use_system_proxy() -> bool:
    return os.environ.get("ZENTAO_USE_SYSTEM_PROXY", "").lower() in {"1", "true", "yes"}


def _zt_session():
    """Create a ZenTao HTTP session with proxy use disabled by default."""
    import requests as _r
    session = _r.Session()
    session.trust_env = _zt_use_system_proxy()
    return session
ZENTAO_DEFAULT_PRODUCT_ID = int(
    project_catalog.config("west-kowloon").get("zentaoProductId") or 146
)


def _project_config(project: str | None) -> dict:
    try:
        return project_catalog.config(project)
    except ProjectCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _project_key(project: str | None) -> str:
    return _project_config(project)["key"]


def _project_match_values(project: str | None) -> set[str]:
    try:
        return project_catalog.match_values(project)
    except ProjectCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _project_workspace_root(project: str | None) -> Path:
    try:
        return project_catalog.project_root(project)
    except ProjectCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _automation_root_for_project(project: str | None) -> Path:
    try:
        return project_catalog.automation_root(project)
    except ProjectCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _automation_paths(project: str | None) -> dict[str, Path]:
    try:
        return project_catalog.paths(project)
    except ProjectCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _runner_for_project(project: str | None) -> BehaveRunner:
    project_key = _project_key(project)
    if project_key not in _runner_cache:
        paths = _automation_paths(project_key)
        _runner_cache[project_key] = BehaveRunner(
            str(paths["automation_root"]),
            paths["features_root"],
            paths["artifacts_root"],
            project_key=project_key,
        )
    return _runner_cache[project_key]


_CASE_METADATA_CACHE: dict[str, tuple[tuple[tuple[str, int, int], ...], dict[str, dict]]] = {}
_FEATURE_LOCATION_CACHE: dict[str, tuple[tuple[tuple[str, int, int], ...], dict[str, list[dict]]]] = {}
_FULL_CASE_ID_RE = re.compile(r"\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b", re.IGNORECASE)


def _case_id_from_scenario_fields(name: str | None, tags: str | None) -> str | None:
    """Extract Test Case ID; scenario-name prefix is canonical, tags are legacy."""
    for source in (name or "", tags or ""):
        match = _FULL_CASE_ID_RE.search(source)
        if match:
            return match.group(1).upper()
    return None


def _normalise_xlsx_header(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _case_metadata_fingerprint(project_key: str) -> tuple[tuple[str, int, int], ...]:
    root = _project_workspace_root(project_key) / "01-requirements"
    if not root.exists():
        return tuple()

    candidates: list[Path] = []
    candidates.extend(root.rglob("test-cases-*.xlsx"))
    candidates.extend(root.rglob("automation-assessment*.xlsx"))

    fp = []
    for path in candidates:
        rel_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in {"_archive", ".backup"} for part in rel_parts):
            continue
        if path.name.startswith("~$"):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        fp.append((str(path), int(stat.st_mtime), int(stat.st_size)))
    return tuple(sorted(fp))


def _read_case_metadata_workbook(path: Path) -> dict[str, dict]:
    """Read case metadata keyed by Test Case ID from one workbook.

    Dashboard rows should use the signed workbook's business description, not
    the shorter Behave scenario name used by automation scripts.
    """
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True, read_only=True)
    except Exception:
        return {}

    sheet = wb["Test Cases"] if "Test Cases" in wb.sheetnames else wb.active
    headers: dict[str, int] = {}
    for col_idx in range(1, sheet.max_column + 1):
        key = _normalise_xlsx_header(sheet.cell(row=1, column=col_idx).value)
        if key:
            headers[key] = col_idx

    case_col = headers.get("test case id")
    if not case_col:
        return {}

    def col(*names: str) -> int | None:
        for name in names:
            idx = headers.get(_normalise_xlsx_header(name))
            if idx:
                return idx
        return None

    scenario_col = col("Test Scenario")
    desc_col = col("Test Case Description")
    module_col = col("Module/Feature")
    steps_col = col("Test Steps")
    expected_col = col("Expected Result")
    automation_status_col = col("Automation Status")
    automation_type_col = col("Automation Type")

    out: dict[str, dict] = {}
    for row_idx in range(2, sheet.max_row + 1):
        case_id = str(sheet.cell(row=row_idx, column=case_col).value or "").strip().upper()
        if not _FULL_CASE_ID_RE.fullmatch(case_id):
            continue

        def value(idx: int | None):
            if not idx:
                return None
            raw = sheet.cell(row=row_idx, column=idx).value
            return str(raw).strip() if raw is not None else None

        out[case_id] = {
            "case_id": case_id,
            "test_case_scenario": value(scenario_col),
            "test_case_description": value(desc_col),
            "module_feature": value(module_col),
            "test_steps": value(steps_col),
            "expected_result": value(expected_col),
            "automation_status": value(automation_status_col),
            "automation_type": value(automation_type_col),
            "case_metadata_source": str(path).replace("\\", "/"),
        }
    return out


def _case_metadata_for_project(project: str | None) -> dict[str, dict]:
    project_key = _project_key(project)
    fingerprint = _case_metadata_fingerprint(project_key)
    cached = _CASE_METADATA_CACHE.get(project_key)
    if cached and cached[0] == fingerprint:
        return cached[1]

    metadata: dict[str, dict] = {}
    for path_str, _mtime, _size in fingerprint:
        path = Path(path_str)
        rows = _read_case_metadata_workbook(path)
        is_assessment = "automation-assessment" in path.name.lower()
        for case_id, row in rows.items():
            current = metadata.get(case_id)
            if not current:
                metadata[case_id] = row
                continue
            # Keep signed test-case workbook wording as display authority; use
            # automation assessment rows only to fill automation fields.
            if is_assessment:
                for key in ("automation_status", "automation_type"):
                    if row.get(key):
                        current[key] = row[key]
                current.setdefault("automation_metadata_source", row["case_metadata_source"])
            else:
                for key, row_value in row.items():
                    if row_value:
                        current[key] = row_value

    _CASE_METADATA_CACHE[project_key] = (fingerprint, metadata)
    return metadata


def _automation_type_from_tags(tags: str | None) -> str | None:
    normalized = {
        tag.strip().lstrip("@").lower()
        for tag in (tags or "").split(",")
        if tag.strip()
    }
    if {"mixed", "api_ui_mixed", "api_first_ui"} & normalized:
        return "Mixed"
    if "api" in normalized and "ui" in normalized:
        return "Mixed"
    if "api" in normalized:
        return "API"
    if "ui" in normalized:
        return "UI"
    if "smoke" in normalized:
        return "Smoke"
    return None


def _automation_type_for_scenario(s: TestScenario, run: Optional[TestRun] = None) -> str:
    project_key = (run.project_key if run else None) or "west-kowloon"
    case_id = _case_id_from_scenario_fields(s.name, s.tags)
    case_meta = _case_metadata_for_project(project_key).get(case_id, {}) if case_id else {}
    return case_meta.get("automation_type") or _automation_type_from_tags(s.tags) or "N/A"


def _feature_location_fingerprint(project_key: str) -> tuple[tuple[str, int, int], ...]:
    features_root = _automation_paths(project_key)["features_root"]
    if not features_root.exists():
        return tuple()
    fp = []
    for path in sorted(features_root.rglob("*.feature")):
        if "deprecated" in path.parts:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        fp.append((str(path), int(stat.st_mtime), int(stat.st_size)))
    return tuple(fp)


def _read_text_lossy(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="gbk", errors="replace")


def _feature_locations_for_project(project: str | None) -> dict[str, list[dict]]:
    """Index current Behave feature scenarios by full test-case ID.

    The dashboard stores scenario name + tags in `test_scenarios`, but not the
    source file line. This index lets result rows point back to the exact
    automation file and scenario without changing the DB schema.
    """
    project_key = _project_key(project)
    fingerprint = _feature_location_fingerprint(project_key)
    cached = _FEATURE_LOCATION_CACHE.get(project_key)
    if cached and cached[0] == fingerprint:
        return cached[1]

    paths = _automation_paths(project_key)
    features_root = paths["features_root"]
    automation_root = paths["automation_root"]
    locations: dict[str, list[dict]] = {}

    for path_str, _mtime, _size in fingerprint:
        fpath = Path(path_str)
        text = _read_text_lossy(fpath)
        feature_name = ""
        pending_tags: list[str] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("Feature:"):
                feature_name = stripped[len("Feature:"):].strip()
                continue
            if stripped.startswith("@"):
                pending_tags = re.findall(r"@[\w-]+", stripped)
                continue
            if not stripped.startswith("Scenario"):
                continue

            scenario_name = re.sub(r"^Scenario(?: Outline)?:\s*", "", stripped)
            source = " ".join([scenario_name, *pending_tags])
            ids = sorted({m.group(1).upper() for m in _FULL_CASE_ID_RE.finditer(source)})
            rel_file = str(fpath.relative_to(automation_root)).replace("\\", "/")
            item = {
                "file": rel_file,
                "absolute_file": str(fpath).replace("\\", "/"),
                "line": line_no,
                "feature": feature_name,
                "scenario": scenario_name,
                "test_kind": "Behave Scenario",
                "test_name": scenario_name,
                "tags": pending_tags,
            }
            for case_id in ids:
                locations.setdefault(case_id, []).append(item)
            pending_tags = []

    _FEATURE_LOCATION_CACHE[project_key] = (fingerprint, locations)
    return locations


def _automation_location_for_scenario(s: TestScenario, project: str | None = None) -> dict | None:
    project_key = _project_key(project)
    case_id = _case_id_from_scenario_fields(s.name, s.tags)
    if not case_id:
        return None
    candidates = _feature_locations_for_project(project_key).get(case_id, [])
    if not candidates:
        return None
    for item in candidates:
        if item.get("scenario") == s.name:
            return item
    return candidates[0]


# --- ZenTao bug-status cache (per bug_id, TTL-based) ----------------------
# Run-detail pages can refresh several times a minute. We cache the bug
# status for ~30s so dev workflow updates (active -> resolved -> closed)
# surface within a refresh or two, but we don't slam ZenTao on every poll.
import time as _time
_BUG_STATUS_CACHE: dict[int, tuple[float, str]] = {}
_BUG_STATUS_TTL = 30.0


def _fetch_bug_status(bug_id: int, token: str) -> str:
    """Return current ZenTao bug status — 'active' | 'resolved' | 'closed' |
    'unknown' (network / auth / parsing errors all map to 'unknown' so the
    UI keeps rendering instead of breaking)."""
    now = _time.time()
    hit = _BUG_STATUS_CACHE.get(bug_id)
    if hit and (now - hit[0]) < _BUG_STATUS_TTL:
        return hit[1]
    try:
        data = _zt_get(f"/bugs/{bug_id}", token)
        if not data:
            status = "unknown"
        else:
            payload = data.get("bug") or data.get("data") or data
            status = payload.get("status") or "unknown"
    except Exception:                                         # noqa: BLE001
        status = "unknown"
    _BUG_STATUS_CACHE[bug_id] = (now, status)
    return status


def _enrich_bug_statuses(scenario_dicts: list[dict]) -> list[dict]:
    """For each scenario's `bugs[]` list, add a `status` field per bug from
    ZenTao (active | resolved | closed | unknown). Sequential fetch but each
    bug is cached for 30s so reloads are cheap."""
    # Most runs have no linked ZenTao bugs. Avoid token refresh/network work in
    # that common path so loading functional scenarios never waits on ZenTao.
    if not any(s.get("bugs") for s in scenario_dicts):
        return scenario_dicts
    token = _zentao_token()
    if not token:
        return scenario_dicts
    for s in scenario_dicts:
        for b in (s.get("bugs") or []):
            b["status"] = _fetch_bug_status(int(b["id"]), token)
    return scenario_dicts


_ZT_DYNAMIC_TOKEN: Optional[str] = None
_ZT_TOKEN_SOURCE: str = "unset"
_ZT_TOKEN_REFRESHED_AT: Optional[str] = None
_ZT_LAST_REFRESH_ERROR: Optional[str] = None


def _windows_user_env(name: str) -> Optional[str]:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, name)
            return str(val) if val else None
    except Exception:                                     # noqa: BLE001
        return None


def _env_or_user_env(name: str) -> Optional[str]:
    return os.environ.get(name) or _windows_user_env(name)


def _zentao_refresh_configured() -> bool:
    return bool(_env_or_user_env("ZENTAO_ACCOUNT") and _env_or_user_env("ZENTAO_PASSWORD"))


def _static_zentao_token() -> Optional[str]:
    return _env_or_user_env("ZENTAO_API_V2_TOKEN")


def _refresh_zentao_token() -> Optional[str]:
    """Refresh a short-lived ZenTao token from dashboard-owned credentials."""
    global _ZT_DYNAMIC_TOKEN, _ZT_TOKEN_SOURCE, _ZT_TOKEN_REFRESHED_AT, _ZT_LAST_REFRESH_ERROR
    account = _env_or_user_env("ZENTAO_ACCOUNT")
    password = _env_or_user_env("ZENTAO_PASSWORD")
    if not account or not password:
        _ZT_LAST_REFRESH_ERROR = "ZENTAO_ACCOUNT/ZENTAO_PASSWORD not configured"
        return None

    headers = {"Content-Type": "application/json"}
    sid = _env_or_user_env("ZENTAO_SESSION_COOKIE")
    if sid:
        headers["Cookie"] = f"device=desktop; lang=zh-cn; theme=default; zentaosid={sid}"

    try:
        resp = _zt_session().post(
            f"{ZENTAO_BASE}/api.php/v1/tokens?user=null",
            headers=headers,
            json={"account": account, "password": password},
            timeout=15,
        )
        if resp.status_code not in (200, 201):
            _ZT_LAST_REFRESH_ERROR = f"ZenTao token refresh HTTP {resp.status_code}: {resp.text[:200]}"
            return None
        data = resp.json() or {}
        token = data.get("token") or (data.get("data") or {}).get("token")
        if token:
            _ZT_DYNAMIC_TOKEN = str(token)
            _ZT_TOKEN_SOURCE = "auto-refresh"
            _ZT_TOKEN_REFRESHED_AT = datetime.utcnow().isoformat()
            _ZT_LAST_REFRESH_ERROR = None
            os.environ["ZENTAO_API_V2_TOKEN"] = _ZT_DYNAMIC_TOKEN
            _ZT_DASHBOARD_CACHE.clear()
            return _ZT_DYNAMIC_TOKEN
    except Exception as exc:                                               # noqa: BLE001
        _ZT_LAST_REFRESH_ERROR = f"{type(exc).__name__}: {exc}"
        return None
    return None


def _zentao_token(force_refresh: bool = False) -> Optional[str]:
    """Return the dashboard-owned ZenTao token.

    If account/password are configured, the backend owns the token lifecycle
    and refreshes into process memory. A manually supplied API token remains
    a compatibility fallback, not the preferred operating mode.
    """
    global _ZT_TOKEN_SOURCE
    if force_refresh:
        return _refresh_zentao_token()
    if _ZT_DYNAMIC_TOKEN:
        return _ZT_DYNAMIC_TOKEN
    if _zentao_refresh_configured():
        refreshed = _refresh_zentao_token()
        if refreshed:
            return refreshed
    tok = _static_zentao_token()
    if tok:
        _ZT_TOKEN_SOURCE = "static-env"
    return tok


class OpenBugRequest(BaseModel):
    """Body for POST /api/scenarios/{id}/open-bug. All fields optional — the
    backend fills sane defaults from the scenario when omitted."""
    title: Optional[str] = None
    steps: Optional[str] = None
    severity: int = 3                # 1 (highest) .. 4 (lowest); 3 = medium
    pri: int = 3                     # 1 .. 4 mirrors the priority used in tasks
    type: str = "codeerror"          # codeerror | config | security | performance | designdefect | others
    product_id: int = ZENTAO_DEFAULT_PRODUCT_ID
    assigned_to: str = "wangyifan"   # per Evan 2026-05-23: all auto-bugs go to him


# --- Bug-template helpers (2026-05-23 overhaul) ---------------------------

import base64 as _b64                                       # noqa: E402

_MODULE_FROM_FEATURE = {
    # rough mapping from the feature human-readable name to a 1-2 word
    # 模块名称 to put in the bug title. Falls back to "Auto Test" when
    # nothing matches.
    "registration": "注册",
    "register":     "注册",
    "login":        "登录",
    "forgot":       "忘记密码",
    "guest":        "游客",
    "session":      "会话",
    "auth":         "登录",
}


def _module_from_feature(feature: str) -> str:
    """Extract a short module name from a feature header string. The DB
    `feature` field looks like 'Website 注册 / Native registration (SIT-TC-
    WEB-AUTH-001-006...)'. We strip the case-id parens and look for a
    keyword we recognise; otherwise return the trimmed prefix."""
    if not feature:
        return "Auto Test"
    head = feature.split("(", 1)[0].strip()
    low = head.lower()
    for key, label in _MODULE_FROM_FEATURE.items():
        if key in low:
            return label
    return head[:30] or "Auto Test"


def _short_scenario_label(name: str) -> str:
    """Strip the full SIT-TC-...-XXX prefix from a scenario name so the
    bug title doesn't restate the whole test id."""
    return re.sub(r"^\s*SIT-TC-[A-Z0-9-]+-\d{3,}\s*", "",
                  name or "", flags=re.I).strip()


def _gherkin_steps_for_scenario(
    scenario_name: str,
    project_key: str | None = None,
) -> list[str]:
    """Read the project's .feature files and return the Given/When/Then
    step lines for the named scenario. Used to populate the bug body's
    'Steps to Reproduce' section verbatim."""
    feats_dir = _automation_paths(project_key or DEFAULT_PROJECT_KEY)["features_root"]
    if not feats_dir.exists():
        return []
    target = scenario_name.strip()
    for fpath in feats_dir.rglob("*.feature"):
        try:
            lines = fpath.read_text(encoding="utf-8").splitlines()
        except Exception:                                    # noqa: BLE001
            continue
        for i, line in enumerate(lines):
            m = re.match(r"\s*Scenario(?:\s+Outline)?:\s*(.*?)\s*$", line)
            if not m or m.group(1).strip() != target:
                continue
            steps: list[str] = []
            for s in lines[i + 1:]:
                stripped = s.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if re.match(r"^(Scenario|Feature|Background|Examples)",
                            stripped):
                    break
                if re.match(r"^(Given|When|Then|And|But|\*)\s", stripped):
                    steps.append(stripped)
                else:
                    break
            return steps
    return []


_LEGACY_CASE_SHORT_RE = re.compile(r"\bSIT-TC-[A-Z0-9-]+-(\d{3,})\b", re.I)


def _runtime_manifest_paths(artifacts_root: Path, run_id: int | None) -> list[Path]:
    """Return runtime screenshot manifests, preferring the current run."""
    seen: set[Path] = set()
    paths: list[Path] = []
    if run_id is not None:
        for path in artifacts_root.rglob(f"case-screenshot-manifest-run-{run_id}.json"):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                paths.append(path)
    for path in sorted(
        artifacts_root.rglob("case-screenshot-manifest-run-*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    ):
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            paths.append(path)
    return paths


def _latest_runtime_screenshots_for_case(
    case_full: str,
    project_key: str | None = None,
    run_id: int | None = None,
    limit: int = 4,
) -> list[Path]:
    """Find screenshots from per-run, per-case runtime manifests."""
    project_keys = [project_key] if project_key else [cfg["key"] for cfg in PROJECT_CATALOG]
    seen_projects: set[str] = set()
    for key in project_keys:
        if not key or key in seen_projects:
            continue
        seen_projects.add(key)
        artifacts_root = _automation_paths(key)["artifacts_root"]
        if not artifacts_root.exists():
            continue
        for manifest_path in _runtime_manifest_paths(artifacts_root, run_id):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:                                  # noqa: BLE001
                continue
            case = (manifest.get("cases") or {}).get(case_full)
            if not isinstance(case, dict):
                continue
            screenshots = case.get("screenshots") or []
            if not isinstance(screenshots, list):
                screenshots = []
            shots: list[Path] = []
            for shot in screenshots:
                if not isinstance(shot, dict) or not shot.get("path"):
                    continue
                path = Path(str(shot["path"]))
                if path.is_file():
                    shots.append(path)
            if shots:
                return shots[:limit]
    return []


def _latest_legacy_screenshots_for_case(
    case_short: str,
    project_key: str | None = None,
    limit: int = 4,
) -> list[Path]:
    """Find the most-recent legacy evidence_* dir for a short case id,
    return up to `limit` PNG paths sorted by filename."""
    base = (
        _automation_paths(project_key or DEFAULT_PROJECT_KEY)["artifacts_root"]
        / "screenshots"
    )
    if not base.exists():
        return []
    runs = sorted([d for d in base.glob("evidence_*") if d.is_dir()],
                  key=lambda d: d.name, reverse=True)
    for run_dir in runs:
        case_dir = run_dir / f"tc{case_short}"
        if case_dir.is_dir():
            shots = sorted(case_dir.glob("*.png"))[:limit]
            if shots:
                return shots
    return []


# Where bug viewers will fetch screenshots from. Override with env if the
# dashboard is on a shared host so devs can actually open the links.
DASHBOARD_PUBLIC_URL = os.environ.get("DASHBOARD_PUBLIC_URL",
                                     "http://127.0.0.1:8002")


def _img_as_http_html(path: Path) -> Optional[str]:
    """Build an <img> tag that points back at the dashboard's static mount,
    so ZenTao can show the screenshot inline. (Data URLs get stripped by
    ZenTao's HTML sanitizer; HTTP URLs survive — verified 2026-05-23.)"""
    url = None
    for project in PROJECT_CATALOG:
        shots_root = _automation_paths(project["key"])["artifacts_root"] / "screenshots"
        try:
            rel = path.resolve().relative_to(shots_root.resolve()).as_posix()
        except ValueError:
            continue
        encoded_project = quote(project["key"], safe="")
        encoded_rel = "/".join(quote(part, safe="") for part in rel.split("/"))
        url = (
            f"{DASHBOARD_PUBLIC_URL.rstrip('/')}/project-screenshots/"
            f"{encoded_project}/{encoded_rel}"
        )
        break
    if not url:
        return None
    return (f'<p><a href="{url}" target="_blank"><img alt="{path.name}" '
            f'src="{url}" style="max-width:680px;border:1px solid #ccc;'
            f'margin:6px 0;display:block;" /></a></p>'
            f'<p style="font-size:11px;color:#888;">'
            f'本地路径: <code>{path}</code></p>')


def _bug_defaults_from_scenario(s: TestScenario,
                                run: Optional[TestRun] = None) -> tuple[str, str]:
    """Build a structured-template bug title + HTML body for a scenario.
    Modeled on IEEE 829 / Jira-style QA bug reports — summary, environment,
    steps, expected, actual, evidence."""
    module = _module_from_feature(s.feature)
    short = _short_scenario_label(s.name)
    # Title: '[模块] 简要场景 — 期望未满足 (status)'
    if s.status == "failed":
        title = f"[{module}] {short} — 用例未通过 / Failed"
    else:
        title = f"[{module}] {short} — 待跟进 / Watch ({s.status})"

    # Per-case Gherkin steps (the test's own Given/When/Then — the most
    # accurate 'steps to reproduce')
    gherkin = _gherkin_steps_for_scenario(
        s.name,
        getattr(run, "project_key", None) if run else None,
    )
    if gherkin:
        steps_html_list = "<ol>" + "".join(
            f"<li><code>{line.replace('&','&amp;').replace('<','&lt;')}</code></li>"
            for line in gherkin
        ) + "</ol>"
    else:
        steps_html_list = ("<p><i>(automation Gherkin steps not found "
                           "in features/*.feature; please add manually)</i></p>")

    # Environment block
    env_name = (run.env if run else "sit").upper()
    started = (run.started_at.strftime("%Y-%m-%d %H:%M:%S")
               if run and run.started_at else "(unknown)")
    automation_type = _automation_type_for_scenario(s, run)

    # Error blob (escape for safe HTML)
    err = (s.error_msg or "(no error captured — scenario was not failing this run)") \
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Screenshots: prefer cross-project runtime manifests keyed by full
    # SIT-TC-... ID; fall back to the older WestK evidence_*/tcXXX layout.
    case_full = _case_id_from_scenario_fields(s.name, s.tags)
    case_short = None
    if case_full:
        short_match = _LEGACY_CASE_SHORT_RE.search(case_full)
        if short_match:
            case_short = short_match.group(1)
    screenshots_html = "<p><i>(no screenshots found for this case)</i></p>"
    if case_full or case_short:
        shots = (
            _latest_runtime_screenshots_for_case(
                case_full,
                getattr(run, "project_key", None) if run else None,
                getattr(run, "id", None) if run else None,
            )
            if case_full else []
        )
        if not shots and case_short:
            shots = _latest_legacy_screenshots_for_case(
                case_short,
                getattr(run, "project_key", None) if run else None,
            )
        if shots:
            parts = []
            for sh in shots:
                inline = _img_as_http_html(sh)
                if inline:
                    parts.append(inline)
                else:
                    parts.append(f"<p><b>{sh.name}</b> (path: "
                                 f"<code>{sh}</code>)</p>")
            screenshots_html = ("".join(parts) +
                                "<p style='font-size:11px;color:#888;'>"
                                "(图片由 QA Dashboard 提供;若图加载不出,"
                                "确保你能访问 "
                                f"<code>{DASHBOARD_PUBLIC_URL}</code>;"
                                "同款图也在 xlsx 工作簿里嵌入。)</p>")

    # Expected vs Actual — derived heuristically; user is encouraged to edit
    expected = ("用例步骤执行后断言通过 (Given/When/Then 全部满足)。"
                if gherkin else "见上面 Gherkin 步骤的预期断言。")
    actual_raw = "用例失败，错误信息见下" if s.status == "failed" \
                 else f"当前 status={s.status}（预先跟踪用）"

    steps = (
        f"<h3>🐞 缺陷概述 / Defect Summary</h3>"
        f"<p><b>模块 Module:</b> {module}  ·  "
        f"<b>用例 Test case:</b> <code>{s.name}</code></p>"
        f"<p><b>期望 Expected:</b> {expected}</p>"
        f"<p><b>实际 Actual:</b> {actual_raw}</p>"

        f"<h3>🌐 测试环境 / Environment</h3>"
        f"<table cellpadding='6' cellspacing='0' "
        f"style='border-collapse:collapse;border:1px solid #ddd;'>"
        f"<tr><td><b>环境</b></td><td>{env_name}</td></tr>"
        f"<tr><td><b>测试开始时间</b></td><td>{started}</td></tr>"
        f"<tr><td><b>用例耗时</b></td><td>{s.duration_s:.2f}s</td></tr>"
        f"<tr><td><b>Feature 文件</b></td><td>{s.feature}</td></tr>"
        f"<tr><td><b>Automation Type</b></td><td>{automation_type}</td></tr>"
        f"<tr><td><b>Dashboard 引用</b></td><td>run #{s.run_id} / "
        f"scenario #{s.id}</td></tr>"
        f"</table>"

        f"<h3>🔁 重现步骤 / Steps to Reproduce</h3>"
        f"{steps_html_list}"

        f"<h3>❌ 错误信息 / Error Output</h3>"
        f"<pre style='background:#fff2f0;color:#a8071a;padding:8px;"
        f"border:1px solid #ffccc7;white-space:pre-wrap;'>{err}</pre>"

        f"<h3>📡 API 错误 / API Errors</h3>"
        f"<p><i>(API call capture not wired up yet — add Playwright "
        f"route-handler logging if needed)</i></p>"

        f"<h3>📸 截图 / Screenshots</h3>"
        f"{screenshots_html}"

        f"<hr>"
        f"<p style='color:#888;font-size:11px;'>"
        f"自动生成自 QA Dashboard · 模板基于 IEEE 829 / Jira best-practice · "
        f"请按需修改各段内容后再提交。"
        f"</p>"
    )
    return title, steps


@app.post("/api/scenarios/{scenario_id}/open-bug")
def open_bug_for_scenario(scenario_id: int, req: OpenBugRequest):
    """Open a ZenTao bug for one scenario. Multi-bug per scenario IS
    supported — dedup is by EXACT title within the scenario, so re-clicking
    'Open Bug' with the default title returns the existing bug, but editing
    the title creates a new one."""
    token = _zentao_token()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="ZENTAO_API_V2_TOKEN not set on the host.",
        )

    db = get_db()
    try:
        s = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
        if not s:
            return {"error": f"scenario {scenario_id} not found"}
        # Run is needed by the defaults so the template can show env + start time
        run = db.query(TestRun).filter(TestRun.id == s.run_id).first()

        default_title, default_steps = _bug_defaults_from_scenario(s, run)
        title = (req.title or default_title).strip()

        # Dedup by exact title within this scenario.
        existing = (
            db.query(ScenarioBug)
            .filter(ScenarioBug.scenario_id == s.id,
                    ScenarioBug.title == title)
            .first()
        )
        if existing:
            return {
                "already_opened": True,
                "bug_id": existing.zentao_bug_id,
                "bug_url": existing.zentao_bug_url,
                "title": existing.title,
            }

        body = {
            "title": title,
            "steps": req.steps or default_steps,
            "severity": req.severity,
            "pri": req.pri,
            "type": req.type,
            "openedBuild": "trunk",
            "assignedTo": req.assigned_to,    # all auto-bugs to wangyifan
        }

        status_code, data, text = _zt_post_json(
            f"/products/{req.product_id}/bugs",
            body,
            token=token,
            timeout=30,
        )
        if status_code not in (200, 201):
            return {
                "error": "ZenTao rejected the bug create",
                "status": status_code,
                "body": text[:500],
            }

        if not data:
            return {"error": f"non-JSON response from ZenTao: {text[:300]}"}

        bug_id = data.get("id") or (data.get("data") or {}).get("id")
        if not bug_id:
            return {
                "error": "ZenTao responded OK but did not return a bug id",
                "body": data,
            }

        bug_url = f"{ZENTAO_BASE}/bug-view-{bug_id}.html"
        # Persist to scenario_bugs (multi-bug) AND keep the legacy single
        # columns in sync with the MOST RECENT bug, so older callers that
        # still read those fields don't see NULL.
        new_bug = ScenarioBug(
            scenario_id=s.id,
            zentao_bug_id=int(bug_id),
            zentao_bug_url=bug_url,
            title=title,
        )
        db.add(new_bug)
        s.zentao_bug_id = int(bug_id)
        s.zentao_bug_url = bug_url
        db.commit()

        return {
            "bug_id": int(bug_id),
            "bug_url": bug_url,
            "title": title,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# WebSocket — live log streaming
# ---------------------------------------------------------------------------

@app.websocket("/ws/runs/{run_id}")
async def ws_logs(websocket: WebSocket, run_id: int):
    """Stream live log lines from a running behave process.

    Protocol:
      - Server sends plain text lines (behave stdout) as they appear
      - Server sends JSON {"type": "done"} when the run finishes
      - Server sends JSON {"type": "ping"} as a keep-alive every 60s
    """
    await websocket.accept()
    db = get_db()
    try:
        run = db.query(TestRun).filter(TestRun.id == run_id).first()
        project_key = (run.project_key if run else None) or "west-kowloon"
    finally:
        db.close()
    project_runner = _runner_for_project(project_key)

    # Send all log lines accumulated so far (in case client connected late)
    for line in project_runner.logs.get(run_id, []):
        await websocket.send_text(line)

    if run and run.status != "running":
        await websocket.send_json({"type": "done"})
        return

    # Subscribe to new lines via an asyncio.Queue
    queue: asyncio.Queue = asyncio.Queue()
    project_runner.subscribe(run_id, queue)

    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=60)
                if msg is None:
                    # None is the sentinel: run finished
                    await websocket.send_json({"type": "done"})
                    break
                await websocket.send_text(msg)
            except asyncio.TimeoutError:
                # Keep the connection alive
                await websocket.send_json({"type": "ping"})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        project_runner.unsubscribe(run_id, queue)


# ---------------------------------------------------------------------------
# Feature / tag discovery — scan .feature files for module selection UI
# ---------------------------------------------------------------------------

def _package_case_ids(package_id: str | None) -> set[str]:
    if not package_id:
        return set()
    pkg = _resolve_safe(package_id)
    if pkg is None or not pkg.is_dir():
        return set()
    case_ids: set[str] = set()
    test_design = pkg / "03-test-design"
    if test_design.is_dir():
        for xlsx in test_design.rglob("test-cases-*.xlsx"):
            case_ids.update(_extract_case_ids(xlsx))
    return case_ids


@app.get("/api/features")
def list_features(project: str = "west-kowloon", package_id: str | None = None):
    """Scan all .feature files and return features with their tags."""
    project_key = _project_key(project)
    paths = _automation_paths(project_key)
    features_dir = paths["features_root"]
    results = []
    all_tags = set()
    package_case_ids = _package_case_ids(package_id)
    package_filtered = bool(package_id)

    if not features_dir.exists():
        return {
            "project": project_key,
            "automationRoot": str(paths["automation_root"]).replace("\\", "/"),
            "featuresRoot": str(features_dir).replace("\\", "/"),
            "packageId": package_id,
            "packageFiltered": package_filtered,
            "packageCaseCount": len(package_case_ids),
            "packageCaseIds": sorted(package_case_ids),
            "features": [],
            "tags": [],
            "_note": f"No feature directory found for project {project_key}",
        }

    for fpath in sorted(features_dir.glob("**/*.feature")):
        if "deprecated" in fpath.parts:
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception:
            text = fpath.read_text(encoding="gbk", errors="replace")

        feature_name = ""
        scenarios = []
        feature_tags = []

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("Feature:"):
                feature_name = stripped[len("Feature:"):].strip()
            elif stripped.startswith("@"):
                tags = re.findall(r"@[\w-]+", stripped)
                feature_tags = tags
                all_tags.update(tags)
            elif stripped.startswith("Scenario"):
                sc_name = re.sub(r"^Scenario(?: Outline)?:\s*", "", stripped)
                case_id = _case_id_from_scenario_fields(sc_name, ",".join(feature_tags))
                if package_filtered and case_id not in package_case_ids:
                    feature_tags = []
                    continue
                scenarios.append({
                    "name": sc_name,
                    "tags": feature_tags,
                    "case_id": case_id,
                })
                feature_tags = []

        if scenarios or not package_filtered:
            results.append({
                "file": str(fpath.relative_to(paths["automation_root"])).replace("\\", "/"),
                "feature": feature_name,
                "scenarios": scenarios,
            })

    return {
        "project": project_key,
        "automationRoot": str(paths["automation_root"]).replace("\\", "/"),
        "featuresRoot": str(features_dir).replace("\\", "/"),
        "packageId": package_id,
        "packageFiltered": package_filtered,
        "packageCaseCount": len(package_case_ids),
        "packageCaseIds": sorted(package_case_ids),
        "features": results,
        "tags": sorted(all_tags),
    }


# ---------------------------------------------------------------------------
# Stats & Analytics — trends, error analysis, flaky tests
# ---------------------------------------------------------------------------

@app.get("/api/stats/trends")
def get_trends(limit: int = 30, project: str = "west-kowloon"):
    """Pass rate trends, duration trends, and error category breakdown."""
    project_key = _project_key(project)
    db = get_db()
    try:
        runs = (
            db.query(TestRun)
            .filter(
                TestRun.status != "running",
                TestRun.project_key == project_key,
                TestRun.run_kind == "full",
            )
            .order_by(TestRun.id.desc())
            .limit(limit)
            .all()
        )
        runs.reverse()  # chronological order

        run_trends = []
        for r in runs:
            errored = r.errored or 0
            executed = (r.passed or 0) + (r.failed or 0) + errored
            collected = r.total or 0
            skipped = r.skipped or 0
            pass_rate = round(((r.passed or 0) / executed) * 100, 1) if executed > 0 else 0

            # Average duration for this run's scenarios
            scenarios = db.query(TestScenario).filter(TestScenario.run_id == r.id).all()
            durations = [s.duration_s for s in scenarios if s.duration_s]
            avg_dur = round(sum(durations) / len(durations), 2) if durations else 0
            total_dur = round(sum(durations), 1) if durations else 0

            run_trends.append({
                "id": r.id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "env": r.env,
                "run_kind": r.run_kind or "full",
                "is_rerun": (r.run_kind or "full").startswith("rerun"),
                "total": collected,
                "collected": collected,
                "executed": executed,
                "passed": r.passed,
                "failed": r.failed,
                "errored": errored,
                "skipped": skipped,
                "pass_rate": pass_rate,
                "avg_duration": avg_dur,
                "total_duration": total_dur,
                "status": r.status,
            })

        # Error category breakdown across all runs
        all_failed = (
            db.query(TestScenario)
            .filter(
                TestScenario.run_id.in_([r.id for r in runs]),
                TestScenario.status == "failed",
                TestScenario.error_msg.isnot(None),
            )
            .all()
        )

        from error_analyzer import categorize_error
        from collections import Counter

        cat_counts = Counter()
        for s in all_failed:
            cat = categorize_error(s.error_msg)
            cat_counts[cat["label"]] += 1

        error_categories = [
            {"category": cat, "count": cnt}
            for cat, cnt in cat_counts.most_common()
        ]

        # Overall summary
        all_runs = (
            db.query(TestRun)
            .filter(
                TestRun.status != "running",
                TestRun.project_key == project_key,
                TestRun.run_kind == "full",
            )
            .all()
        )
        total_passed = sum((r.passed or 0) for r in all_runs)
        total_failed = sum((r.failed or 0) for r in all_runs)
        total_errored = sum((r.errored or 0) for r in all_runs)
        total_skipped = sum((r.skipped or 0) for r in all_runs)
        total_collected = sum((r.total or 0) for r in all_runs)
        total_executed = total_passed + total_failed + total_errored
        overall_pass_rate = round((total_passed / total_executed) * 100, 1) if total_executed > 0 else 0
        avg_executed = round(total_executed / len(all_runs), 1) if all_runs else 0
        avg_collected = round(total_collected / len(all_runs), 1) if all_runs else 0

        return {
            "project": project_key,
            "runs": run_trends,
            "error_categories": error_categories,
            "summary": {
                "total_runs": len(all_runs),
                "overall_pass_rate": overall_pass_rate,
                "avg_scenarios_per_run": avg_executed,
                "avg_executed_per_run": avg_executed,
                "avg_collected_per_run": avg_collected,
                "total_scenarios_executed": total_executed,
                "total_scenarios_collected": total_collected,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_errored": total_errored,
                "total_skipped": total_skipped,
            },
        }
    finally:
        db.close()


@app.get("/api/stats/errors/{run_id}")
def get_error_analysis(run_id: int):
    """Smart error analysis for a specific run."""
    db = get_db()
    try:
        scenarios = (
            db.query(TestScenario)
            .filter(TestScenario.run_id == run_id)
            .all()
        )
        scenario_dicts = [_scenario_dict(s) for s in scenarios]
        return analyze_run_errors(scenario_dicts)
    finally:
        db.close()


@app.get("/api/stats/flaky")
def get_flaky_tests(limit: int = 15, project: str = "west-kowloon"):
    """Detect flaky tests by analyzing status flips across recent runs."""
    project_key = _project_key(project)
    db = get_db()
    try:
        runs = (
            db.query(TestRun)
            .filter(
                TestRun.status != "running",
                TestRun.status != "error",
                TestRun.project_key == project_key,
                TestRun.run_kind == "full",
            )
            .order_by(TestRun.id.desc())
            .limit(limit)
            .all()
        )
        runs.reverse()

        run_history = []
        for r in runs:
            scenarios = db.query(TestScenario).filter(TestScenario.run_id == r.id).all()
            run_history.append({
                "run_id": r.id,
                "scenarios": [
                    {"feature": s.feature, "name": s.name, "status": s.status}
                    for s in scenarios
                ],
            })

        flaky = detect_flaky_tests(run_history)
        return {"project": project_key, "flaky_tests": flaky, "runs_analyzed": len(runs)}
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Background task: execute behave and save results to DB
# ---------------------------------------------------------------------------

async def _execute_run(
    run_id: int,
    tags: Optional[str],
    env: str,
    names: Optional[list[str]] = None,
    features: Optional[list[str]] = None,
    project: str = "west-kowloon",
):
    """Run behave, parse results, and update the database."""
    project_runner = _runner_for_project(project)
    exit_code, scenarios = await project_runner.run_behave(
        run_id, tags=tags, env=env, names=names, features=features,
    )

    db = get_db()
    try:
        run = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not run:
            return

        run.finished_at = datetime.utcnow()
        run.total = len(scenarios)
        run.passed = sum(1 for s in scenarios if s["status"] == "passed")
        run.failed = sum(1 for s in scenarios if s["status"] == "failed")
        run.errored = sum(1 for s in scenarios if s["status"] in ("error", "undefined", "untested"))
        run.skipped = sum(1 for s in scenarios if s["status"] == "skipped")
        executed = run.passed + run.failed + run.errored

        if run.total == 0:
            run.status = "error"
        elif executed == 0:
            run.status = "error"
        elif run.failed > 0 or run.errored > 0:
            run.status = "failed"
        else:
            run.status = "passed"

        # Save individual scenario results
        for s in scenarios:
            db.add(TestScenario(
                run_id=run_id,
                feature=s["feature"],
                name=s["name"],
                status=s["status"],
                duration_s=s["duration_s"],
                error_msg=s["error_msg"],
                tags=s["tags"],
            ))

        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_dict(r: TestRun) -> dict:
    errored = r.errored or 0
    executed = (r.passed or 0) + (r.failed or 0) + errored
    collected = r.total or 0
    run_kind = r.run_kind or "full"
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "status": r.status,
        "env": r.env,
        "project": r.project_key or "west-kowloon",
        "tags": r.tags,
        "run_kind": run_kind,
        "parent_run_id": r.parent_run_id,
        "rerun_scope": r.rerun_scope,
        "source_scenario_id": r.source_scenario_id,
        "is_rerun": run_kind.startswith("rerun"),
        "total": collected,
        "collected": collected,
        "executed": executed,
        "passed": r.passed,
        "failed": r.failed,
        "errored": errored,
        "skipped": r.skipped,
    }


def _run_event_timestamp(r: TestRun) -> datetime | None:
    return r.finished_at or r.started_at


def _scenario_latest_attempts(
    db,
    scenarios: list[TestScenario],
    project: str | None,
) -> dict[str, dict]:
    """Latest per-case attempt metadata across full runs and reruns."""
    from sqlalchemy import or_

    project_key = _project_key(project)
    case_ids = sorted({
        cid for cid in (
            _case_id_from_scenario_fields(s.name, s.tags) for s in scenarios
        )
        if cid
    })
    if not case_ids:
        return {}

    conditions = []
    for case_id in case_ids:
        conditions.append(TestScenario.name.like(f"%{case_id}%"))
        conditions.append(TestScenario.tags.like(f"%{case_id}%"))

    rows = (
        db.query(TestScenario, TestRun)
        .join(TestRun, TestScenario.run_id == TestRun.id)
        .filter(TestRun.project_key == project_key, or_(*conditions))
        .all()
    )

    grouped: dict[str, list[tuple[TestScenario, TestRun]]] = {
        case_id: [] for case_id in case_ids
    }
    for scenario, run in rows:
        case_id = _case_id_from_scenario_fields(scenario.name, scenario.tags)
        if case_id in grouped:
            grouped[case_id].append((scenario, run))

    out: dict[str, dict] = {}
    for case_id, attempts in grouped.items():
        if not attempts:
            continue
        attempts.sort(
            key=lambda item: (
                _run_event_timestamp(item[1]) or datetime.min,
                item[1].id or 0,
                item[0].id or 0,
            ),
            reverse=True,
        )
        latest_s, latest_r = attempts[0]
        meaningful = next(
            (
                (scenario, run)
                for scenario, run in attempts
                if _execution_result_from_technical_status(scenario.status)
            ),
            None,
        )
        payload = {
            "last_run_id": latest_r.id,
            "last_run_kind": latest_r.run_kind or "full",
            "last_run_status": latest_s.status,
            "last_run_at": (
                _run_event_timestamp(latest_r).isoformat()
                if _run_event_timestamp(latest_r) else None
            ),
            "last_run_env": latest_r.env,
            "last_run_duration_s": latest_s.duration_s,
            "last_run_scenario_id": latest_s.id,
            "last_run_parent_run_id": latest_r.parent_run_id,
            "last_run_rerun_scope": latest_r.rerun_scope,
            "attempt_count": len(attempts),
            "rerun_count": sum(
                1 for _, run in attempts if (run.run_kind or "full") != "full"
            ),
        }
        if meaningful:
            meaningful_s, meaningful_r = meaningful
            payload.update({
                "last_meaningful_run_id": meaningful_r.id,
                "last_meaningful_run_kind": meaningful_r.run_kind or "full",
                "last_meaningful_status": meaningful_s.status,
                "last_meaningful_at": (
                    _run_event_timestamp(meaningful_r).isoformat()
                    if _run_event_timestamp(meaningful_r) else None
                ),
                "last_meaningful_execution_result": (
                    _execution_result_from_technical_status(meaningful_s.status)
                ),
            })
        out[case_id] = payload
    return out


def _scenario_dict(
    s: TestScenario,
    project: str | None = None,
    run: TestRun | None = None,
    latest_attempt: dict | None = None,
) -> dict:
    """Serialize a scenario row, including ALL of its ZenTao bugs (the
    multi-bug rewrite of 2026-05-23). Each bug entry's `status` is filled
    later by _enrich_bug_statuses from the live ZenTao API."""
    bugs = [{
        "id": b.zentao_bug_id,
        "url": b.zentao_bug_url,
        "title": b.title,
        "opened_at": b.opened_at.isoformat() if b.opened_at else None,
    } for b in (s.bugs or [])]
    case_id = _case_id_from_scenario_fields(s.name, s.tags)
    case_meta = _case_metadata_for_project(project).get(case_id, {}) if case_id and project else {}
    run_kind = (run.run_kind if run else None) or "full"
    payload = {
        "id": s.id,
        "run_id": s.run_id,
        "run_kind": run_kind,
        "run_started_at": run.started_at.isoformat() if run and run.started_at else None,
        "run_finished_at": run.finished_at.isoformat() if run and run.finished_at else None,
        "parent_run_id": run.parent_run_id if run else None,
        "rerun_scope": run.rerun_scope if run else None,
        "source_scenario_id": run.source_scenario_id if run else None,
        "feature": s.feature,
        "name": s.name,
        "case_id": case_id,
        "test_case_scenario": case_meta.get("test_case_scenario"),
        "test_case_description": case_meta.get("test_case_description"),
        "module_feature": case_meta.get("module_feature"),
        "test_steps": case_meta.get("test_steps"),
        "expected_result": case_meta.get("expected_result"),
        "automation_status": case_meta.get("automation_status"),
        "automation_type": case_meta.get("automation_type"),
        "automation_location": _automation_location_for_scenario(s, project) if project else None,
        "case_metadata_source": case_meta.get("case_metadata_source"),
        "automation_metadata_source": case_meta.get("automation_metadata_source"),
        "status": s.status,
        "duration_s": s.duration_s,
        "error_msg": s.error_msg,
        "tags": s.tags,
        "bugs": bugs,
    }
    if latest_attempt:
        payload.update(latest_attempt)
    return payload


def _as_float(value) -> float:
    if value in (None, "", "N/A"):
        return 0.0
    try:
        return float(str(value).replace("%", "").strip())
    except Exception:
        return 0.0


def _as_int(value) -> int:
    return int(round(_as_float(value)))


# Domain routers are configured here so shared runtime dependencies remain
# explicit and router modules never import the application module.
from routers import api_monitor, observability, package_health, performance, zentao  # noqa: E402


def _zentao_token_status() -> dict:
    return {
        "tokenSource": _ZT_TOKEN_SOURCE,
        "lastRefreshAt": _ZT_TOKEN_REFRESHED_AT,
        "lastRefreshError": _ZT_LAST_REFRESH_ERROR,
    }


app.include_router(performance.configure_router(
    project_key=_project_key,
    automation_paths=_automation_paths,
    workspace_root=_workspace_root,
    metrics_client_instance=metrics_client,
    metrics_config_instance=metrics_config,
    perf_artifact_prefix=PERF_ARTIFACT_PREFIX,
    perf_log_limit=PERF_LOG_LIMIT,
    perf_state_ref=perf_state,
    as_float=_as_float,
    as_int=_as_int,
))
app.include_router(observability.configure_router(
    metrics_client_instance=metrics_client,
    metrics_config_instance=metrics_config,
))
app.include_router(api_monitor.configure_router(
    project_key=_project_key,
    project_match_values=_project_match_values,
    automation_paths=_automation_paths,
))
app.include_router(zentao.configure_router(
    zt_session=_zt_session,
    zentao_token=_zentao_token,
    zentao_refresh_configured=_zentao_refresh_configured,
    token_status_provider=_zentao_token_status,
    project_config=_project_config,
    project_key=_project_key,
    as_float=_as_float,
))
app.include_router(package_health.configure_router(
    package_scanner_module=package_scanner,
    workspace_root=_workspace_root,
    repo_root=_repo_root,
    project_key=_project_key,
    project_workspace_root=_project_workspace_root,
    case_id_from_scenario_fields=_case_id_from_scenario_fields,
))

# Existing run-detail and bug-opening helpers share the same configured
# ZenTao client and cache as the ZenTao router.
_zt_get = zentao.zt_get
_zt_post_json = zentao.zt_post_json
_ZT_DASHBOARD_CACHE = zentao.dashboard_cache()


# Production/local single-process mode: after `npm run build`, FastAPI serves
# the Vite bundle while development can continue to use the Vite HMR server.
from frontend_hosting import install_frontend_routes  # noqa: E402

install_frontend_routes(app, _dashboard_root / "02-frontend" / "dist")
