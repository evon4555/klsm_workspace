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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

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
    ApiMonitorEndpointResult, ApiMonitorRun,
    ScenarioBug, TestRun, TestScenario, get_db, init_db,
)
from error_analyzer import analyze_run_errors, detect_flaky_tests
from metrics_client import (
    MetricsClient, MetricsConfig, generate_mock_perf_report,
    generate_mock_flamegraph, generate_mock_logs,
)
from runner import DEFAULT_DASHBOARD_TAGS, BehaveRunner
from story_case_generator import (
    STORY_RULES,
    generate_login_registration_core_workbook,
    generate_story_workbook,
    generated_file_path,
)

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

app = FastAPI(title="Test Automation Dashboard API")

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

runner = BehaveRunner(PROJECT_ROOT, FEATURES_ROOT, ARTIFACTS_ROOT)
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


@app.on_event("startup")
def on_startup():
    """Create database tables on first launch (idempotent)."""
    init_db()


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
        "defaultProject": "west-kowloon",
        "workspaceRoot": str(_workspace_root).replace("\\", "/"),
        "projects": projects,
    }


# Serve evidence screenshots over HTTP so they can be embedded as <img> in
# ZenTao bugs. ZenTao SaaS strips data: URLs (verified 2026-05-23) but keeps
# <img src="http://..."> intact, so this is how screenshots reach a bug page.
_SHOTS_DIR = ARTIFACTS_ROOT / "screenshots"
if _SHOTS_DIR.exists():
    app.mount("/screenshots",
              StaticFiles(directory=str(_SHOTS_DIR)),
              name="screenshots")


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
def list_runs(project: str = "west-kowloon"):
    """List the 20 most recent test runs (newest first)."""
    project_key = _project_key(project)
    db = get_db()
    try:
        runs = (
            db.query(TestRun)
            .filter(TestRun.project_key == project_key)
            .order_by(TestRun.id.desc())
            .limit(20)
            .all()
        )
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
        scenario_dicts = _enrich_bug_statuses(
            [_scenario_dict(s, run.project_key) for s in scenarios]
        )
        return {
            **_run_dict(run),
            "scenarios": scenario_dicts,
        }
    finally:
        db.close()


@app.post("/api/runs/{run_id}/rerun")
async def rerun_failed(run_id: int):
    """Rerun only the failed scenarios from a previous run.
    Creates a new run with the same env/tags but filtered to failed scenario names."""
    db = get_db()
    try:
        original = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not original:
            return {"error": "Run not found"}

        failed = (
            db.query(TestScenario)
            .filter(TestScenario.run_id == run_id, TestScenario.status == "failed")
            .all()
        )
        if not failed:
            return {"error": "No failed scenarios to rerun"}

        failed_names = [s.name for s in failed]

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

        new_run = TestRun(
            started_at=datetime.utcnow(),
            status="running",
            env=orig_env,
            project_key=orig_project,
            tags=orig_tags,
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)
        new_id = new_run.id
    finally:
        db.close()

    asyncio.create_task(
        _execute_run(new_id, orig_tags, orig_env, names=failed_names,
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
        name = s.name

        new_run = TestRun(
            started_at=datetime.utcnow(),
            status="running",
            env=env,
            project_key=project_key,
            tags=tags,
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
        artifacts_root.rglob("case-screenshot-manifest-latest.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    if not candidates:
        return
    manifest_path = candidates[0]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:                                      # noqa: BLE001
        return
    cases = manifest.get("cases") or {}
    if not isinstance(cases, dict):
        return

    payload["updated_at"] = payload.get("updated_at") or manifest.get("updated_at")
    payload["runtime_screenshot_manifest"] = str(manifest_path).replace("\\", "/")
    payload["runtime_run_id"] = manifest.get("run_id")
    evidence_cases = payload.setdefault("cases", {})
    for raw_case_id, raw_case in cases.items():
        case_id = _case_id_key(raw_case_id)
        if not case_id or not isinstance(raw_case, dict):
            continue
        screenshots = raw_case.get("screenshots") or []
        if not isinstance(screenshots, list):
            screenshots = []
        short = case_id.rsplit("-", 1)[-1]
        rec = dict(evidence_cases.get(case_id) or evidence_cases.get(short) or {})
        rec.update({
            "case_id": case_id,
            "has_screenshot": len(screenshots) > 0,
            "shots": len(screenshots),
            "screenshot_count": len(screenshots),
            "screenshots": screenshots,
            "runtime_run_id": manifest.get("run_id"),
            "runtime_status": raw_case.get("status"),
            "runtime_scenario": raw_case.get("scenario"),
            "runtime_manifest": str(manifest_path).replace("\\", "/"),
        })
        rec.setdefault("synced", False)
        rec.setdefault("status", "Runtime screenshots" if screenshots else "No screenshot")
        evidence_cases[case_id] = rec
        evidence_cases[short] = rec


# ---------------------------------------------------------------------------
# Quality evidence packages — durable manifests promoted into 03-evidence.
# The dashboard uses this as the evidence-backed layer for Quality System
# deliverables and gates. Runtime artifacts remain under 02-automation.
# ---------------------------------------------------------------------------

QUALITY_REQUIRED_DELIVERABLES = ["p5-d1", "p5-d2", "p5-d4", "p6-d3", "p6-d4"]


def _rel_to_evidence(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_EVIDENCE_ROOT.resolve())).replace("\\", "/")
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
        out.append({
            "type": "behave",
            "timestamp": (r.started_at.isoformat() if r.started_at else None),
            "run_id": r.id,
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
ZENTAO_DEFAULT_PRODUCT_ID = 146     # West Kowloon


PROJECT_CATALOG = [
    {
        "key": "west-kowloon",
        "name": "West Kowloon",
        "kind": "customer",
        "workspace": "west-kowloon",
        "zentaoProductId": ZENTAO_DEFAULT_PRODUCT_ID,
        "zentaoExecutionId": 614,
    },
    {
        "key": "standard product",
        "name": "Standard Product",
        "kind": "baseline",
        "workspace": "standard product",
        "zentaoProductId": 22,
        "zentaoExecutionId": 640,
    },
    {
        "key": "jockey club",
        "name": "Jockey Club",
        "kind": "customer",
        "workspace": "jockey club",
        "zentaoProductId": None,
        "zentaoExecutionId": None,
    },
]


def _project_config(project: str | None) -> dict:
    requested = (project or "west-kowloon").strip()
    for item in PROJECT_CATALOG:
        aliases = {
            item["key"],
            item["workspace"],
            item["name"],
            str(item["key"]).lower(),
            str(item["workspace"]).lower(),
            str(item["name"]).lower(),
        }
        if requested in aliases or requested.lower() in aliases:
            return item
    raise HTTPException(status_code=400, detail=f"unknown project: {requested}")


def _project_key(project: str | None) -> str:
    return _project_config(project)["key"]


def _project_match_values(project: str | None) -> set[str]:
    cfg = _project_config(project)
    values = {cfg["key"], cfg["workspace"], cfg["name"]}
    # Older API smoke artifacts may store a localized display name.
    if cfg["key"] == "west-kowloon":
        values.update({"西九", "瑗夸節"})
    return {v for v in values if v}


def _project_workspace_root(project: str | None) -> Path:
    cfg = _project_config(project)
    return (_workspace_root / cfg["workspace"]).resolve()


def _automation_root_for_project(project: str | None) -> Path:
    project_root = _project_workspace_root(project)
    automation_root = project_root / "02-automation"
    if automation_root.exists():
        return automation_root
    if _project_key(project) == "west-kowloon":
        return _repo_root / "02-platform" / "01-automation"
    return automation_root


def _automation_paths(project: str | None) -> dict[str, Path]:
    automation_root = _automation_root_for_project(project)
    return {
        "project_key": _project_key(project),
        "workspace_root": _project_workspace_root(project),
        "automation_root": automation_root,
        "features_root": automation_root / "01-features",
        "tests_root": automation_root / "02-tests",
        "tools_root": automation_root / "04-tools",
        "artifacts_root": automation_root / "07-artifacts",
        "evidence_root": _project_workspace_root(project) / "03-evidence",
    }


def _runner_for_project(project: str | None) -> BehaveRunner:
    project_key = _project_key(project)
    if project_key not in _runner_cache:
        paths = _automation_paths(project_key)
        _runner_cache[project_key] = BehaveRunner(
            str(paths["automation_root"]),
            paths["features_root"],
            paths["artifacts_root"],
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


def _gherkin_steps_for_scenario(scenario_name: str) -> list[str]:
    """Read the project's .feature files and return the Given/When/Then
    step lines for the named scenario. Used to populate the bug body's
    'Steps to Reproduce' section verbatim."""
    feats_dir = FEATURES_ROOT
    if not feats_dir.exists():
        return []
    target = scenario_name.strip()
    for fpath in feats_dir.glob("*.feature"):
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


def _latest_legacy_screenshots_for_case(case_short: str, limit: int = 4) -> list[Path]:
    """Find the most-recent legacy evidence_* dir for a short case id,
    return up to `limit` PNG paths sorted by filename."""
    base = ARTIFACTS_ROOT / "screenshots"
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
    try:
        rel = path.resolve().relative_to(_SHOTS_DIR.resolve()).as_posix()
    except Exception:                                        # noqa: BLE001
        return None
    url = f"{DASHBOARD_PUBLIC_URL.rstrip('/')}/screenshots/{rel}"
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
    gherkin = _gherkin_steps_for_scenario(s.name)
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
            shots = _latest_legacy_screenshots_for_case(case_short)
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
        return {"error": "ZENTAO_API_V2_TOKEN not set on the host."}, 500

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

@app.get("/api/features")
def list_features(project: str = "west-kowloon"):
    """Scan all .feature files and return features with their tags."""
    project_key = _project_key(project)
    paths = _automation_paths(project_key)
    features_dir = paths["features_root"]
    results = []
    all_tags = set()

    if not features_dir.exists():
        return {
            "project": project_key,
            "automationRoot": str(paths["automation_root"]).replace("\\", "/"),
            "featuresRoot": str(features_dir).replace("\\", "/"),
            "features": [],
            "tags": [],
            "_note": f"No feature directory found for project {project_key}",
        }

    for fpath in sorted(features_dir.glob("**/*.feature")):
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
                scenarios.append({
                    "name": sc_name,
                    "tags": feature_tags,
                })
                feature_tags = []

        results.append({
            "file": str(fpath.relative_to(paths["automation_root"])).replace("\\", "/"),
            "feature": feature_name,
            "scenarios": scenarios,
        })

    return {
        "project": project_key,
        "automationRoot": str(paths["automation_root"]).replace("\\", "/"),
        "featuresRoot": str(features_dir).replace("\\", "/"),
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
            .filter(TestRun.status != "running", TestRun.project_key == project_key)
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
                "env": r.env,
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
            .filter(TestRun.status != "running", TestRun.project_key == project_key)
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
# Performance Testing — Locust integration + metrics services status
# ---------------------------------------------------------------------------

PERF_MODE_TO_USER_CLASS = {
    "mixed": "MixedUser",
    "login": "LoginUser",
    "business": "BusinessUser",
    "order_create": "OrderCreateUser",
    "order_cancel": "OrderCancelUser",
}
PERF_MODE_ORDER = list(PERF_MODE_TO_USER_CLASS.keys())
PERF_LOCUSTFILE_MODE_MAP = {
    "tests/performance/locustfile.py": PERF_MODE_ORDER,
    "tests/performance/business_create_order.py": ["order_create"],
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
    locustfile: str = "tests/performance/locustfile.py"


def _perf_artifact_prefix(project: str | None) -> Path:
    return _automation_paths(project)["evidence_root"] / "performance" / "latest" / "perf_latest"


@app.get("/api/perf/status")
async def perf_status(project: str = "west-kowloon"):
    """Return the latest Locust run status and metadata."""
    project_key = _project_key(project)
    state = _perf_state_dict()
    if state.get("project") in (None, project_key):
        return state
    return {
        **state,
        "status": "idle",
        "project": project_key,
        "pid": None,
        "logs": [],
        "message": "No performance run is active for this project.",
    }


@app.get("/api/perf/services")
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


@app.get("/api/perf/grafana/panels")
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


@app.get("/api/perf/metrics")
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


@app.get("/api/perf/report")
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


@app.get("/api/perf/locustfiles")
def list_perf_locustfiles(project: str = "west-kowloon"):
    """List top-level Locust entry files available to the dashboard."""
    project_key = _project_key(project)
    tests_root = _automation_paths(project_key)["tests_root"]
    perf_dir = tests_root / "performance"
    if not perf_dir.exists():
        return {"project": project_key, "files": [], "modes": {}}

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
    return {"project": project_key, "files": files, "modes": modes}


@app.post("/api/perf/stop")
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


@app.post("/api/perf/run")
async def start_perf_test(req: PerfTestRequest):
    """Trigger a Locust performance test.
    Returns immediately; the test runs in the background."""
    if perf_state["status"] == "running":
        return {"error": "A performance test is already running", "status": "running"}

    project_key = _project_key(req.project)
    paths = _automation_paths(project_key)
    locustfile = paths["automation_root"] / req.locustfile
    if not locustfile.exists() and req.locustfile.startswith("tests/"):
        locustfile = paths["tests_root"] / req.locustfile.removeprefix("tests/")
    if not locustfile.exists():
        return {"error": f"Locust file not found: {req.locustfile}"}

    mode = (req.mode or "mixed").strip().lower()
    allowed_modes = _allowed_perf_modes(req.locustfile)
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
            "pid": process.pid,
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "exit_code": None,
            "config": {
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
        asyncio.create_task(_monitor_perf_process(process))
        return {
            "status": "started",
            "pid": process.pid,
            "config": {
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
        perf_state.update({
            "status": "error",
            "pid": None,
            "finished_at": datetime.utcnow().isoformat(),
            "exit_code": None,
            "error": str(exc),
        })
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Observability — Pyroscope (flame graph) + Loki (logs) + Toxiproxy (chaos)
# ---------------------------------------------------------------------------

@app.get("/api/observability/status")
async def observability_status():
    """Check connectivity to Pyroscope, Loki, and Toxiproxy."""
    pyro, loki, toxi = await asyncio.gather(
        metrics_client.check_pyroscope(),
        metrics_client.check_loki(),
        metrics_client.check_toxiproxy(),
    )
    return {
        "pyroscope": {"connected": pyro, "url": metrics_config.pyroscope_url},
        "loki": {"connected": loki, "url": metrics_config.loki_url},
        "toxiproxy": {"connected": toxi, "url": metrics_config.toxiproxy_url},
    }


@app.get("/api/observability/flamegraph")
async def get_flamegraph(query: str = "process_cpu", from_ts: str = "now-1h", until_ts: str = "now"):
    """Get flame graph data from Pyroscope (or mock data for demo)."""
    return await metrics_client.get_flame_graph(query, from_ts, until_ts)


@app.get("/api/observability/logs")
async def get_logs(query: str = '{job="fastapi-app"}', limit: int = 100):
    """Query logs from Loki (or mock data for demo)."""
    return await metrics_client.query_loki(query, limit)


@app.get("/api/observability/toxiproxy/proxies")
async def list_toxi_proxies():
    """List all Toxiproxy proxies."""
    return await metrics_client.list_proxies()


@app.post("/api/observability/toxiproxy/toxic")
async def add_toxi_toxic(proxy_name: str, toxic_type: str, latency: int = 500, jitter: int = 100):
    """Add a toxic to a proxy. For demo: returns mock confirmation when Toxiproxy is not running."""
    connected = await metrics_client.check_toxiproxy()
    if not connected:
        return {
            "status": "demo",
            "message": f"[Demo Mode] Would inject {toxic_type} toxic on proxy '{proxy_name}' with latency={latency}ms jitter={jitter}ms",
            "toxic": {
                "name": f"{proxy_name}-{toxic_type}",
                "type": toxic_type,
                "proxy": proxy_name,
                "attributes": {"latency": latency, "jitter": jitter},
            },
        }

    attrs = {"latency": latency, "jitter": jitter} if toxic_type == "latency" else {"rate": latency}
    return await metrics_client.add_toxic(proxy_name, toxic_type, attrs)


@app.post("/api/observability/toxiproxy/reset")
async def reset_toxi():
    """Reset all toxics."""
    connected = await metrics_client.check_toxiproxy()
    if not connected:
        return {"status": "demo", "message": "[Demo Mode] Would reset all toxics"}
    await metrics_client.reset_toxiproxy()
    return {"status": "ok"}


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


@app.post("/api/api-monitor/run-smoke")
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


@app.get("/api/api-monitor/run-smoke")
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


@app.get("/api/api-monitor/endpoints")
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


@app.get("/api/api-monitor/trends")
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


@app.get("/api/api-monitor/layers")
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

        if run.total == 0:
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
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "status": r.status,
        "env": r.env,
        "project": r.project_key or "west-kowloon",
        "tags": r.tags,
        "total": collected,
        "collected": collected,
        "executed": executed,
        "passed": r.passed,
        "failed": r.failed,
        "errored": errored,
        "skipped": r.skipped,
    }


def _scenario_dict(s: TestScenario, project: str | None = None) -> dict:
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
    return {
        "id": s.id,
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


async def _monitor_perf_process(process):
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
        prefix = _current_perf_artifact_prefix()
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

        error_rate = round((total_failures / total_requests) * 100, 2) if total_requests else 0
        perf_state.update({
            "status": final_status,
            "finished_at": datetime.utcnow().isoformat(),
            "exit_code": exit_code,
            "pid": None,
            "error": final_error,
            "stop_requested": False,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "error_rate": error_rate,
        })
    except Exception as exc:
        perf_state.update({
            "status": "error",
            "finished_at": datetime.utcnow().isoformat(),
            "exit_code": None,
            "pid": None,
            "error": str(exc),
        })


def _perf_state_dict() -> dict:
    return {
        "status": perf_state["status"],
        "project": perf_state.get("project"),
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
        fail_ps = _as_float(_row_value(row, "Total Failure Count/s", "Total Failure Count", "total_failure_count", "Failures/s"))

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


def _as_float(value) -> float:
    if value in (None, "", "N/A"):
        return 0.0
    try:
        return float(str(value).replace("%", "").strip())
    except Exception:
        return 0.0


def _as_int(value) -> int:
    return int(round(_as_float(value)))


# ===========================================================================
# ZenTao Integration dashboard — aggregate endpoint
#
# Single endpoint that returns everything the ZenTaoDashboardPage needs:
# iterations, requirements, modules, QA throughput, bug heatmap, automation
# trend. Cached 5 min to avoid hammering the SaaS.
#
# Token: read from ZENTAO_API_V2_TOKEN (Windows user env or process env)
# Base:  https://lengliwh.chandao.net/api.php/v1
# Default product: 146 (西九 / West Kowloon)
# ===========================================================================

_ZT_DASHBOARD_CACHE: dict[str, tuple[float, dict]] = {}
_ZT_DASHBOARD_TTL = 300.0  # 5 minutes
_ZT_QA_TASK_MATRIX_CACHE: dict[str, tuple[float, dict]] = {}
_ZT_QA_TASK_MATRIX_TTL = 1800.0  # 30 minutes; this scans all executions.
_ZT_LAST_ERROR: Optional[str] = None


def _zt_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[dict] = None,
    critical: bool = False,
) -> Optional[dict]:
    """Wrapper for ZenTao REST GET. Returns parsed JSON or None on failure."""
    global _ZT_LAST_ERROR
    try:
        url = f"{ZENTAO_BASE}/api.php/v1{path}"
        active_token = _ZT_DYNAMIC_TOKEN or token or _zentao_token()
        if not active_token:
            if critical:
                _ZT_LAST_ERROR = "ZenTao API token unavailable and auto-refresh is not configured."
            return None
        resp = _zt_session().get(url, headers={"Token": active_token}, params=params, timeout=15)
        if resp.status_code == 401:
            refreshed = _zentao_token(force_refresh=True)
            if refreshed:
                resp = _zt_session().get(
                    url,
                    headers={"Token": refreshed},
                    params=params,
                    timeout=15,
                )
        if resp.status_code != 200:
            if critical:
                if resp.status_code == 401:
                    if _zentao_refresh_configured():
                        _ZT_LAST_ERROR = "ZenTao API token unauthorized; backend auto-refresh was attempted but did not recover."
                    else:
                        _ZT_LAST_ERROR = "ZenTao API token unauthorized and backend auto-refresh is not configured. Set ZENTAO_ACCOUNT/ZENTAO_PASSWORD."
                else:
                    _ZT_LAST_ERROR = f"ZenTao GET {path} HTTP {resp.status_code}: {resp.text[:200]}"
            return None
        return resp.json()
    except Exception as exc:                                       # noqa: BLE001
        if critical:
            _ZT_LAST_ERROR = f"ZenTao GET {path} failed: {type(exc).__name__}: {exc}"
        return None


def _zt_post_json(
    path: str,
    body: dict,
    token: Optional[str] = None,
    timeout: int = 30,
) -> tuple[int, Optional[dict], str]:
    """ZenTao POST with the same dashboard-owned token retry policy."""
    url = f"{ZENTAO_BASE}/api.php/v1{path}"
    active_token = _ZT_DYNAMIC_TOKEN or token or _zentao_token()
    if not active_token:
        return 0, None, "ZenTao API token unavailable and auto-refresh is not configured."

    headers = {"Token": active_token, "Content-Type": "application/json"}
    try:
        resp = _zt_session().post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 401:
            refreshed = _zentao_token(force_refresh=True)
            if refreshed:
                resp = _zt_session().post(
                    url,
                    headers={"Token": refreshed, "Content-Type": "application/json"},
                    json=body,
                    timeout=timeout,
                )
        text = resp.text
        try:
            data = resp.json()
        except Exception:                                     # noqa: BLE001
            data = None
        return resp.status_code, data, text
    except Exception as exc:                                  # noqa: BLE001
        return 0, None, f"{type(exc).__name__}: {exc}"


@app.get("/api/zentao/auth-status")
def zentao_auth_status():
    """Non-secret ZenTao auth diagnostics for dashboard operation."""
    token = _zentao_token()
    return {
        "base": ZENTAO_BASE,
        "autoRefreshConfigured": _zentao_refresh_configured(),
        "hasToken": bool(token),
        "tokenSource": _ZT_TOKEN_SOURCE,
        "lastRefreshAt": _ZT_TOKEN_REFRESHED_AT,
        "lastRefreshError": _ZT_LAST_REFRESH_ERROR,
    }


@app.get("/api/zentao/products")
def zentao_products(refresh: bool = False):
    """Return selectable ZenTao products for the integration page."""
    token = _zentao_token()
    if not token:
        return {"products": [], "error": "ZENTAO_API_V2_TOKEN not set"}

    global _ZT_LAST_ERROR
    _ZT_LAST_ERROR = None
    resp = _zt_get("/products", token, {"limit": 500}, critical=True)
    products = (resp or {}).get("products") or (resp or {}).get("data") or []
    if not products and _ZT_LAST_ERROR:
        products = [{"id": ZENTAO_DEFAULT_PRODUCT_ID, "name": "西九", "code": "", "status": "unknown"}]
    return {
        "products": [
            {
                "id": int(p.get("id")),
                "name": p.get("name") or f"Product {p.get('id')}",
                "code": p.get("code") or "",
                "status": p.get("status") or "",
            }
            for p in products
            if p.get("id") is not None
        ],
        "error": _ZT_LAST_ERROR,
        "cached": False,
    }


class StoryTestcaseGenerateRequest(BaseModel):
    """Body for POST /api/zentao/story/{story_id}/testcases/generate."""
    execution_id: int = 614
    include_login_registration_core: bool = False


@app.post("/api/zentao/story/{story_id}/testcases/generate")
def zentao_generate_story_testcases(
    story_id: int,
    req: StoryTestcaseGenerateRequest,
):
    """Generate a West Kowloon style xlsx test-case file for one ZenTao story.

    The current implementation uses local story mappings for the West Kowloon
    split stories 4161 and 4266. The workbook is written to the project
    story-splits folder and returned with a dashboard download URL.
    """
    try:
        result = generate_story_workbook(story_id)
        result["executionId"] = req.execution_id
        result["downloadUrl"] = f"/api/zentao/generated-testcases/{result['filename']}"
        if req.include_login_registration_core:
            core = generate_login_registration_core_workbook()
            core["downloadUrl"] = f"/api/zentao/generated-testcases/{core['filename']}"
            result["loginRegistrationCore"] = core
        return result
    except Exception as exc:                                      # noqa: BLE001
        return {"error": str(exc), "storyId": story_id}


@app.get("/api/zentao/generated-testcases/{filename}")
def zentao_download_generated_testcases(filename: str):
    """Download a generated story-split xlsx file."""
    try:
        path = generated_file_path(filename)
    except Exception as exc:                                      # noqa: BLE001
        return {"error": str(exc)}
    if not path.exists():
        return {"error": f"generated file not found: {filename}"}
    return FileResponse(
        str(path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


_STORY_STAGE_ZH = {
    "wait":      "待评审",
    "planned":   "已评审",
    "projected": "已评审",
    "developing":"进行中",
    "developed": "进行中",
    "testing":   "进行中",
    "tested":    "已完成",
    "verified":  "已完成",
    "released":  "已发布",
    "closed":    "已发布",
}


def _story_stage_zh(stage: Optional[str]) -> str:
    return _STORY_STAGE_ZH.get((stage or "").lower(), "进行中")


def _name_of(field) -> str:
    """ZenTao API sometimes returns user/module fields as a dict and sometimes
    as a plain string. Normalise to a display name."""
    if isinstance(field, dict):
        return field.get("realname") or field.get("name") or field.get("account") or ""
    if isinstance(field, str):
        return field
    return ""


def _is_auto(case: dict) -> bool:
    """Heuristic for "this test case has automation". ZenTao stores it in
    different fields across versions — accept any truthy variant."""
    v = case.get("auto") or case.get("automation") or case.get("scriptStatus")
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v != 0
    if isinstance(v, str):
        return v.lower() in ("auto", "yes", "y", "true", "1", "automated")
    return False


def _safe_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:                                              # noqa: BLE001
        return None


TASK_STATUS_META = {
    "wait":    {"label": "未开始", "color": "#8c8c8c"},
    "doing":   {"label": "进行中", "color": "#faad14"},
    "pause":   {"label": "暂停", "color": "#722ed1"},
    "done":    {"label": "已完成", "color": "#52c41a"},
    "closed":  {"label": "已关闭", "color": "#1677ff"},
    "cancel":  {"label": "已取消", "color": "#bfbfbf"},
    "changed": {"label": "已变更", "color": "#13c2c2"},
}
TASK_STATUS_ORDER = ["wait", "doing", "pause", "done", "closed", "cancel", "changed"]
EXECUTION_STATUS_SCAN = ["doing", "wait", "suspended", "closed"]
TESTTASK_STATUS_MAP = {
    "wait": "wait",
    "doing": "doing",
    "done": "closed",
    "closed": "closed",
    "suspended": "pause",
}
STATUS_TEXT_MAP = {
    "未开始": "wait",
    "进行中": "doing",
    "已完成": "done",
    "已关闭": "closed",
    "暂停": "pause",
    "已取消": "cancel",
    "已变更": "changed",
}


def _account_of(field) -> str:
    if isinstance(field, dict):
        return field.get("account") or ""
    return ""


def _qa_owner_index(qa_users: list[dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for u in qa_users:
        owner = _name_of(u.get("realname")) or str(u.get("account") or "").strip()
        if not owner:
            continue
        for candidate in (u.get("account"), u.get("realname"), owner):
            key = str(candidate or "").strip().casefold()
            if key:
                index[key] = owner
    return index


def _task_owner_candidates(task: dict) -> list[str]:
    candidates: list[str] = []
    for field_name in ("assignedTo", "owner"):
        field = task.get(field_name)
        if isinstance(field, dict):
            candidates.extend([
                field.get("account"),
                field.get("realname"),
                field.get("name"),
            ])
        elif isinstance(field, str):
            candidates.append(field)
    candidates.extend([
        task.get("assignedToRealName"),
        task.get("ownerRealName"),
    ])
    # ZenTao closes-out: closed tasks have assignedTo=null and
    # assignedToRealName="Closed"; the QA who actually did the work moves to
    # finishedBy. Without this fallback, every closed task drops off the
    # owner's count (e.g. 魏梦 was showing 32 instead of ~648).
    assigned = task.get("assignedTo")
    assigned_label = str(task.get("assignedToRealName") or "").strip().lower()
    if assigned in (None, "") or assigned_label == "closed":
        fb = task.get("finishedBy")
        if isinstance(fb, dict):
            candidates.extend([
                fb.get("account"),
                fb.get("realname"),
                fb.get("name"),
            ])
        elif isinstance(fb, str):
            candidates.append(fb)
    return [
        str(v).strip() for v in candidates
        if str(v or "").strip() and str(v).strip().lower() != "closed"
    ]


def _resolve_task_owner(task: dict, qa_index: dict[str, str]) -> str:
    for candidate in _task_owner_candidates(task):
        owner = qa_index.get(candidate.casefold())
        if owner:
            return owner
    return ""


def _is_qa_task(task: dict) -> bool:
    """Filter for tasks that count as QA work in the task-count matrix.

    ZenTao's `/executions/{id}/tasks` returns ALL task types (devel/test/ui/
    affair/study/design/...). The 任务数量分布 widget only wants test work.
    But the `type` field is mislabelled often enough — many entries with
    type='devel' are clearly tests by name (e.g. '【测试】...') — so we also
    accept tasks whose name starts with the 【测试】 marker.
    """
    if task.get("type") == "test":
        return True
    name = task.get("name") or ""
    return "【测试】" in name


def _task_status_key(task: dict, source: str) -> str:
    raw_status = str(task.get("rawStatus") or task.get("status") or "").strip().lower()
    if source == "testtask":
        raw_status = TESTTASK_STATUS_MAP.get(raw_status, raw_status)
    if raw_status in TASK_STATUS_META:
        return raw_status
    status_text = str(task.get("status") or "").strip()
    return STATUS_TEXT_MAP.get(status_text, "other")


def _build_task_matrix_from_tasks(tasks: list[dict], qa_users: list[dict], fetched_executions: int,
                                 fetched_testtasks: int = 0,
                                 testtasks: Optional[list[dict]] = None) -> dict:
    from collections import defaultdict as _dd

    qa_index = _qa_owner_index(qa_users)
    status_seen: set[str] = set()
    tasks_by_owner: dict[str, dict[str, list[dict]]] = _dd(lambda: _dd(list))
    seen_task_ids = set()

    for t in tasks:
        task_id = t.get("id")
        task_key = f"task:{task_id}" if task_id else None
        if task_key and task_key in seen_task_ids:
            continue
        if task_key:
            seen_task_ids.add(task_key)

        if not _is_qa_task(t):
            continue
        owner = _resolve_task_owner(t, qa_index)
        if not owner:
            continue
        status_key = _task_status_key(t, "task")
        status_seen.add(status_key)
        raw_status = str(t.get("rawStatus") or t.get("status") or "").strip() or "其它"
        account = _account_of(t.get("assignedTo")) or str(t.get("assignedToRealName") or "").strip()
        ex_id = t.get("execution") or t.get("executionID") or t.get("executionId")
        raw_story = t.get("story")
        if isinstance(raw_story, dict):
            raw_story = raw_story.get("id")
        try:
            story_id = int(raw_story or 0)
        except (TypeError, ValueError):
            story_id = 0
        tasks_by_owner[owner][status_key].append({
            "id": task_id,
            "name": t.get("name") or "",
            "status": status_key,
            "statusLabel": TASK_STATUS_META.get(status_key, {"label": raw_status or "其它"})["label"],
            "owner": owner,
            "account": account,
            "date": (
                t.get("realStarted") or t.get("assignedDate") or t.get("openedDate")
                or t.get("finishedDate") or t.get("closedDate") or ""
            ),
            "executionId": ex_id,
            "executionName": t.get("executionName") or "",
            "storyId": story_id or None,
            "url": f"{ZENTAO_BASE}/task-view-{task_id}.html" if task_id else "",
        })

    # Testtasks (测试单) are a separate ZenTao entity, not 任务 — they used to be
    # added to this matrix and inflated QA counts by ~80 across the team. The
    # widget's title is "QA 任务数量 · 人员 × 状态", so we restrict to /tasks
    # only. `testtasks` arg kept (callers count them for the summary banner)
    # but no longer contributes rows.

    columns = [
        {
            "key": key,
            "label": TASK_STATUS_META[key]["label"],
            "color": TASK_STATUS_META[key]["color"],
        }
        for key in TASK_STATUS_ORDER
    ]
    if "other" in status_seen:
        columns.append({"key": "other", "label": "其它", "color": "#595959"})
    if not columns:
        columns = [
            {"key": key, "label": TASK_STATUS_META[key]["label"], "color": TASK_STATUS_META[key]["color"]}
            for key in ["wait", "doing", "done", "closed"]
        ]

    def _row_total(owner: str) -> int:
        return sum(len(tasks_by_owner[owner].get(col["key"], [])) for col in columns)

    owners = sorted(
        {(_name_of(u.get("realname")) or str(u.get("realname") or u.get("account") or "")) for u in qa_users},
        key=lambda owner: (-_row_total(owner), owner),
    )
    matrix = []
    matrix_tasks = []
    for owner in owners:
        by_status = tasks_by_owner.get(owner, {})
        matrix.append([len(by_status.get(col["key"], [])) for col in columns])
        matrix_tasks.append([by_status.get(col["key"], []) for col in columns])

    by_status_totals = {
        col["key"]: sum(row[idx] for row in matrix)
        for idx, col in enumerate(columns)
    }
    return {
        "scope": "all-executions",
        "peopleType": "qa",
        "statusColumns": columns,
        "ownerRows": owners,
        "matrix": matrix,
        "matrixTasks": matrix_tasks,
        "summary": {
            "total": sum(by_status_totals.values()),
            "people": len(owners),
            "qaWithTasks": sum(1 for owner in owners if _row_total(owner) > 0),
            "byStatus": by_status_totals,
            "fetchedExecutions": fetched_executions,
            "fetchedTesttasks": fetched_testtasks,
            "sourceTaskCount": len(tasks),
        },
        "fetchedAt": datetime.utcnow().isoformat(),
    }


def _collect_testtasks() -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor

    first = _zt_get("/testtasks", _zentao_token(), {"page": 1}, critical=True) or {}
    rows = first.get("testtasks") or []
    total = int(first.get("total") or len(rows) or 0)
    limit = int(first.get("limit") or 20)
    if total <= len(rows) or limit <= 0:
        return rows

    pages = (total + limit - 1) // limit

    def _fetch_page(page: int) -> list[dict]:
        resp = _zt_get("/testtasks", _zentao_token(), {"page": page}, critical=True) or {}
        return resp.get("testtasks") or []

    with ThreadPoolExecutor(max_workers=min(4, max(1, pages - 1))) as pool:
        for page_rows in pool.map(_fetch_page, range(2, pages + 1)):
            rows.extend(page_rows)
    return rows


def _fetch_qa_task_matrix(
    refresh: bool = False,
    execution_id: int = 0,
    project: str = "west-kowloon",
) -> dict:
    global _ZT_QA_TASK_MATRIX_CACHE
    project_key = _project_key(project)
    cache_key = f"{project_key}:execution:{execution_id or 'all'}"
    now = _time.time()
    cached = _ZT_QA_TASK_MATRIX_CACHE.get(cache_key)
    if not refresh and cached and (now - cached[0]) < _ZT_QA_TASK_MATRIX_TTL:
        payload = dict(cached[1])
        payload["cached"] = True
        return payload

    token = _zentao_token()
    if not token:
        return {"error": "ZENTAO_API_V2_TOKEN not set", "cached": False}

    users_resp = _zt_get("/users", token, {"limit": 500}, critical=True) or {}
    users = users_resp.get("users") or users_resp.get("data") or []
    qa_users = [
        u for u in users
        if (u.get("role") or "").lower() == "qa" and u.get("account")
    ]

    executions_by_id: dict[int, dict] = {}
    if execution_id:
        executions_by_id[int(execution_id)] = {"id": int(execution_id), "name": f"Execution {execution_id}"}
    else:
        for status in EXECUTION_STATUS_SCAN:
            resp = _zt_get("/executions", token, {"limit": 500, "status": status}, critical=True) or {}
            for ex in (resp.get("data") or resp.get("executions") or []):
                try:
                    ex_id = int(ex.get("id") or 0)
                except Exception:                                  # noqa: BLE001
                    ex_id = 0
                if ex_id:
                    executions_by_id[ex_id] = ex

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _fetch_tasks(ex_id: int) -> tuple[int, Optional[list[dict]]]:
        # Per-call retry — ZenTao SaaS occasionally drops requests under load
        # (no HTTP error, just a None from _zt_get). Without retry we'd silently
        # under-count by ~10-30 tasks across the 688-execution scan.
        for attempt in range(3):
            resp = _zt_get(f"/executions/{ex_id}/tasks", token, {"limit": 500})
            if resp is not None:
                rows = resp.get("data") or resp.get("tasks") or []
                ex_name = executions_by_id.get(ex_id, {}).get("name") or ""
                for row in rows:
                    row.setdefault("execution", ex_id)
                    row.setdefault("executionName", ex_name)
                return ex_id, rows
            _time.sleep(0.4 * (attempt + 1))
        return ex_id, None  # persistent failure

    testtasks = _collect_testtasks()
    all_tasks: list[dict] = []
    failed_exec_ids: list[int] = []
    # 8 workers, not 32 — ZenTao SaaS rate-limits aggressive concurrency, and
    # the silent failures cost more than the wall-clock savings.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_fetch_tasks, ex_id) for ex_id in executions_by_id]
        for fut in as_completed(futures):
            try:
                ex_id, rows = fut.result()
            except Exception:                                  # noqa: BLE001
                continue
            if rows is None:
                failed_exec_ids.append(ex_id)
            else:
                all_tasks.extend(rows)

    payload = _build_task_matrix_from_tasks(
        all_tasks,
        qa_users,
        len(executions_by_id),
        fetched_testtasks=len(testtasks),
        testtasks=testtasks,
    )
    payload["project"] = project_key
    payload["scope"] = f"execution:{execution_id}" if execution_id else "all-executions"
    payload["cached"] = False
    payload["summary"]["sourceTestTaskCount"] = len(testtasks)
    payload["summary"]["failedExecCount"] = len(failed_exec_ids)
    if failed_exec_ids:
        payload["summary"]["failedExecSample"] = sorted(failed_exec_ids)[:10]
    _ZT_QA_TASK_MATRIX_CACHE[cache_key] = (now, payload)
    return payload


@app.get("/api/zentao/qa-task-matrix")
def zentao_qa_task_matrix(
    refresh: bool = False,
    project: str = "west-kowloon",
    execution_id: int = 0,
):
    """QA task count matrix scoped to the selected dashboard project."""
    cfg = _project_config(project)
    project_key = cfg["key"]
    effective_execution_id = execution_id or int(cfg.get("zentaoExecutionId") or 0)
    if not effective_execution_id:
        payload = _build_task_matrix_from_tasks([], [], 0, fetched_testtasks=0, testtasks=[])
        payload.update({
            "project": project_key,
            "scope": "unmapped-project",
            "cached": False,
            "_note": f"No ZenTao execution is mapped for project {project_key}.",
        })
        return payload
    return _fetch_qa_task_matrix(
        refresh=refresh,
        execution_id=effective_execution_id,
        project=project_key,
    )


_ZT_EXEC_DETAIL_CACHE: dict[int, tuple[float, dict]] = {}


def _build_iter_detail(ex: dict, token: str,
                       sub_responses: Optional[dict] = None) -> dict:
    """Compute one execution's full detail from its sub-resources.

    If `sub_responses` is provided (during a batched dashboard build), reuse
    them — otherwise spawn 4 parallel ZenTao calls. Returns
    `{summary, requirements}` ready to merge into the dashboard payload."""
    ex_id = ex.get("id")
    # Fetch sub-resources (stories, bugs, testcases) + testtasks
    # (testtasks is a flat list across all executions — we filter client-side)
    if sub_responses is None:
        from concurrent.futures import ThreadPoolExecutor
        def _f(resource):
            if resource == "testtasks":
                # flat /testtasks endpoint, filter by execution after
                return resource, _zt_get("/testtasks", token, {"limit": 500}) or {}
            limit = 500 if resource in ("bugs", "testcases", "tasks") else 200
            return resource, _zt_get(f"/executions/{ex_id}/{resource}", token,
                                      {"limit": limit}) or {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            sub_responses = dict(pool.map(_f, ["stories", "bugs", "testcases", "testtasks", "tasks"]))

    sr_stories = sub_responses.get("stories", {}) if isinstance(sub_responses, dict) else {}
    sr_bugs = sub_responses.get("bugs", {}) if isinstance(sub_responses, dict) else {}
    sr_cases = sub_responses.get("testcases", {}) if isinstance(sub_responses, dict) else {}
    sr_tasks = sub_responses.get("testtasks", {}) if isinstance(sub_responses, dict) else {}
    sr_devtasks = sub_responses.get("tasks", {}) if isinstance(sub_responses, dict) else {}

    stories = sr_stories.get("data") or sr_stories.get("stories") or []
    bugs = sr_bugs.get("data") or sr_bugs.get("bugs") or []
    cases = sr_cases.get("data") or sr_cases.get("cases") or []
    all_testtasks = sr_tasks.get("data") or sr_tasks.get("testtasks") or []
    dev_tasks = sr_devtasks.get("data") or sr_devtasks.get("tasks") or []

    from collections import Counter as _Counter
    from collections import defaultdict as _dd

    def _story_id(raw) -> int:
        if isinstance(raw, dict):
            raw = raw.get("id")
        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0

    def _is_test_task(t: dict) -> bool:
        name = (t.get("name") or "").lower()
        return "测试" in name or "test" in name

    def _task_owner(t: dict) -> str:
        owner = _name_of(t.get("assignedTo")).strip()
        # ZenTao may surface pseudo assignees for closed/pooled work. They
        # are not real people and should not be counted as current ownership.
        return "" if owner.lower() in {"closed", "null", "none"} else owner

    def _is_current_task(t: dict) -> bool:
        status = (t.get("status") or "").lower()
        return status not in {"done", "closed", "cancel", "cancelled"}

    def _task_date(t: dict) -> str:
        return (t.get("realStarted") or t.get("assignedDate")
                or t.get("openedDate") or t.get("finishedDate") or "")

    def _task_sort_key(t: dict):
        return _task_date(t)

    def _task_evidence(t: dict, source: str) -> dict:
        return {
            "source": source,
            "id": t.get("id"),
            "name": t.get("name") or "",
            "status": t.get("status") or "",
            "owner": _task_owner(t),
            "date": _task_date(t),
        }

    task_status_meta = {
        "wait":    {"label": "未开始", "color": "#8c8c8c"},
        "doing":   {"label": "进行中", "color": "#faad14"},
        "done":    {"label": "已完成", "color": "#52c41a"},
        "closed":  {"label": "已关闭", "color": "#1677ff"},
        "pause":   {"label": "暂停", "color": "#722ed1"},
        "cancel":  {"label": "已取消", "color": "#bfbfbf"},
        "changed": {"label": "已变更", "color": "#13c2c2"},
    }
    task_status_order = ["wait", "doing", "done", "closed", "pause", "cancel", "changed"]
    task_matrix_map: dict[str, dict[str, list[dict]]] = _dd(lambda: _dd(list))
    task_status_seen: set[str] = set()
    for t in dev_tasks:
        raw_status = (t.get("status") or "unknown").lower()
        status_key = raw_status if raw_status in task_status_meta else "other"
        task_status_seen.add(status_key)
        owner = _task_owner(t) or "Unassigned"
        task_id = t.get("id")
        sid = _story_id(t.get("story"))
        task_matrix_map[owner][status_key].append({
            "id": task_id,
            "name": t.get("name") or "",
            "status": status_key,
            "statusLabel": task_status_meta.get(status_key, {
                "label": raw_status or "其它",
            })["label"],
            "owner": owner,
            "date": _task_date(t),
            "storyId": sid or None,
            "url": f"{ZENTAO_BASE}/task-view-{task_id}.html" if task_id else "",
        })

    task_status_columns = [
        {
            "key": key,
            "label": task_status_meta.get(key, {"label": "其它"})["label"],
            "color": task_status_meta.get(key, {"color": "#595959"})["color"],
        }
        for key in task_status_order
        if key in task_status_seen
    ]
    if "other" in task_status_seen:
        task_status_columns.append({"key": "other", "label": "其它", "color": "#595959"})
    if not task_status_columns:
        task_status_columns = [
            {"key": key, "label": task_status_meta[key]["label"], "color": task_status_meta[key]["color"]}
            for key in ["wait", "doing", "done", "closed"]
        ]

    def _owner_sort(item):
        owner, by_status = item
        total = sum(len(v) for v in by_status.values())
        return (owner == "Unassigned", -total, owner)

    task_owner_rows = []
    task_matrix = []
    task_matrix_tasks = []
    for owner, by_status in sorted(task_matrix_map.items(), key=_owner_sort):
        task_owner_rows.append(owner)
        task_matrix.append([len(by_status.get(col["key"], [])) for col in task_status_columns])
        task_matrix_tasks.append([by_status.get(col["key"], []) for col in task_status_columns])

    task_status_totals = {
        col["key"]: sum(row[idx] for row in task_matrix)
        for idx, col in enumerate(task_status_columns)
    }
    task_kpi = {
        "total": sum(task_status_totals.values()),
        "people": len(task_owner_rows),
        "byStatus": task_status_totals,
    }

    # Group every test-like task by Story. We only count a person as the
    # current test owner when there is a not-closed test task currently
    # assigned to them. Historical test tasks remain evidence but do not drive
    # ownership, because they can be stale and caused false attribution
    # (for example STORY-3884).
    test_tasks_by_story: dict[int, list[dict]] = _dd(list)
    for t in dev_tasks:
        sid = _story_id(t.get("story"))
        if not sid or not _is_test_task(t):
            continue
        test_tasks_by_story[sid].append(t)

    for task_list in test_tasks_by_story.values():
        task_list.sort(key=_task_sort_key, reverse=True)

    def _resolve_story_test_owner(sid: int, story_cases: list[dict]) -> dict:
        tasks = test_tasks_by_story.get(sid, [])
        current_tasks = [
            t for t in tasks
            if _is_current_task(t) and _task_owner(t)
        ]
        if current_tasks:
            task = current_tasks[0]
            return {
                "owner": _task_owner(task),
                "source": "current_test_task",
                "confidence": "high",
                "evidence": (
                    [_task_evidence(task, "current_test_task")]
                    + [_task_evidence(t, "other_current_test_task") for t in current_tasks[1:4]]
                    + [_task_evidence(t, "historical_test_task") for t in tasks if t not in current_tasks][:3]
                ),
            }

        unassigned_current_tasks = [
            t for t in tasks
            if _is_current_task(t) and not _task_owner(t)
        ]
        evidence = (
            [_task_evidence(t, "unassigned_current_test_task") for t in unassigned_current_tasks[:3]]
            + [_task_evidence(t, "historical_test_task") for t in tasks if t not in unassigned_current_tasks][:4]
        )
        case_authors = _Counter(
            _name_of(c.get("openedBy"))
            for c in story_cases
            if _name_of(c.get("openedBy"))
        )
        for owner, count in case_authors.most_common(3):
            evidence.append({
                "source": "test_case_author",
                "owner": owner,
                "count": count,
            })

        return {
            "owner": "Unassigned",
            "source": "none" if not evidence else "evidence_only",
            "confidence": "none" if not evidence else "low",
            "evidence": evidence,
        }

    story_status = {"待评审": 0, "已评审": 0, "进行中": 0, "已完成": 0, "已发布": 0}
    for s in stories:
        story_status[_story_stage_zh(s.get("stage"))] = story_status.get(_story_stage_zh(s.get("stage")), 0) + 1

    bug_active = sum(1 for b in bugs if (b.get("status") or "").lower() == "active")
    bug_closed = sum(1 for b in bugs if (b.get("status") or "").lower() == "closed")
    bug_p0 = sum(1 for b in bugs if int(b.get("pri") or 99) == 1
                  and (b.get("status") or "").lower() == "active")
    bug_p1 = sum(1 for b in bugs if int(b.get("pri") or 99) == 2
                  and (b.get("status") or "").lower() == "active")

    # 4×3 matrix: rows = S1..S4, cols = open / verifying / closed.
    # Status bucketing (ZenTao SaaS observed values):
    #   active, delay   → open    (pending fix)
    #   resolved, confirmed → verifying  (fixed, awaiting QA verification)
    #   closed          → closed
    bug_status_col = {
        "active": 0, "delay": 0,
        "resolved": 1, "confirmed": 1,
        "closed": 2,
    }
    bug_matrix = [[0]*3 for _ in range(4)]
    bug_matrix_bugs: list = [[[] for _ in range(3)] for _ in range(4)]
    for b in bugs:
        st = (b.get("status") or "").lower()
        col = bug_status_col.get(st)
        if col is None:
            continue
        try:
            sev = int(b.get("severity") or 0)
        except Exception:                                          # noqa: BLE001
            continue
        if not (1 <= sev <= 4):
            continue
        bug_matrix[sev-1][col] += 1
        bug_matrix_bugs[sev-1][col].append({
            "id": b.get("id"),
            "title": b.get("title") or "(no title)",
            "status": st,
            "severity": sev,
            "pri": int(b.get("pri") or 0) or None,
            "assignedTo": _name_of(b.get("assignedTo")) or "",
            "url": f"{ZENTAO_BASE}/bug-view-{b.get('id')}.html",
        })
    bug_kpi = {
        "total": sum(sum(r) for r in bug_matrix),
        "open":      sum(r[0] for r in bug_matrix),
        "verifying": sum(r[1] for r in bug_matrix),
        "closed":    sum(r[2] for r in bug_matrix),
        "s1": sum(bug_matrix[0]),
        "s2": sum(bug_matrix[1]),
        "s3": sum(bug_matrix[2]),
        "s4": sum(bug_matrix[3]),
    }

    total_cases = len(cases)
    auto_cases = sum(1 for c in cases if _is_auto(c))

    qa_team_map: dict[str, dict] = {}
    for c in cases:
        qa = _name_of(c.get("openedBy"))
        if not qa:
            continue
        d = qa_team_map.setdefault(qa, {"cases": 0, "auto": 0})
        d["cases"] += 1
        if _is_auto(c):
            d["auto"] += 1

    today = datetime.now()
    start_d = _safe_date(ex.get("begin") or ex.get("openedDate"))
    end_d = _safe_date(ex.get("end") or ex.get("deadline"))
    total_days = max(1, (end_d - start_d).days) if (start_d and end_d) else 0
    days_left = max(0, (end_d - today).days) if end_d else 0

    status_lc = (ex.get("status") or "").lower()
    zh_status = {"doing": "active", "wait": "planning",
                 "suspended": "closing", "closed": "done"}.get(status_lc, "active")

    summary = {
        "id": f"iter-{ex_id}",
        "name": ex.get("name") or f"执行 {ex_id}",
        "code": f"EXEC-{ex_id}",
        "startDate": (start_d.strftime("%Y-%m-%d") if start_d else ""),
        "endDate":   (end_d.strftime("%Y-%m-%d") if end_d else ""),
        "status": zh_status,
        "daysLeft": days_left,
        "totalDays": total_days,
        "progressPct": int(_as_float(ex.get("progress"))),
        "storyTotal": len(stories),
        "storyByStatus": story_status,
        "bugActive": bug_active, "bugClosed": bug_closed,
        "bugP0": bug_p0, "bugP1": bug_p1,
        "bugMatrix": bug_matrix,
        "bugMatrixBugs": bug_matrix_bugs,
        "bugKpi": bug_kpi,
        "taskStatusColumns": task_status_columns,
        "taskOwnerRows": task_owner_rows,
        "taskMatrix": task_matrix,
        "taskMatrixTasks": task_matrix_tasks,
        "taskKpi": task_kpi,
        "testCases": total_cases, "autoTestCases": auto_cases,
        "qaTeam": [
            {"name": k, "cases": v["cases"], "auto": v["auto"]}
            for k, v in sorted(qa_team_map.items(), key=lambda x: -x[1]["cases"])
        ][:5],
        "detailLoaded": True,
    }

    # Build a {story_id -> [bug list]} map from this execution's bugs.
    # Each item is the minimal info the frontend modal needs to show + link out.
    bug_by_story: dict = _dd(list)
    for b in bugs:
        sid = b.get("story") or 0
        if not sid:
            continue
        bug_by_story[sid].append({
            "id": b.get("id"),
            "title": b.get("title") or "(no title)",
            "status": (b.get("status") or "active"),
            "severity": int(b.get("severity") or 0) or None,
            "pri": int(b.get("pri") or 0) or None,
            "assignedTo": _name_of(b.get("assignedTo")) or "",
            "url": f"{ZENTAO_BASE}/bug-view-{b.get('id')}.html",
        })

    # Per-story case stats (if cases happen to be fetched for the iter)
    cases_by_story: dict = _dd(list)
    for c in cases:
        sid = c.get("story") or 0
        if sid:
            cases_by_story[sid].append(c)

    def _case_url(case_id) -> str:
        """ZenTao case ids look like 'case_1797' — strip prefix for the URL."""
        cid = case_id
        if isinstance(cid, str) and cid.startswith("case_"):
            cid = cid[5:]
        try:
            return f"{ZENTAO_BASE}/testcase-view-{int(cid)}.html"
        except (TypeError, ValueError):
            return f"{ZENTAO_BASE}/testcase-view-{cid}.html"

    def _bucket_for(result: str, status: str) -> str:
        """Map ZenTao case state → one of pass/fail/inProgress/unexecuted."""
        r = (result or "").lower()
        if r == "pass":
            return "pass"
        if r == "fail":
            return "fail"
        if r in ("blocked", "n/a"):
            return "inProgress"
        # Empty result — case has not been run yet
        return "inProgress" if (status or "").lower() == "doing" else "unexecuted"

    requirements = []
    for idx, s in enumerate(stories[:50]):
        sid = s.get("id")
        story_bugs = bug_by_story.get(sid, [])
        story_cases = cases_by_story.get(sid, [])
        owner_info = _resolve_story_test_owner(_story_id(sid), story_cases)
        total_c = len(story_cases)

        # Build the bucketed breakdown + per-case list for the modal
        breakdown = {"pass": 0, "fail": 0, "inProgress": 0, "unexecuted": 0, "total": total_c}
        case_list = []
        for c in story_cases:
            bucket = _bucket_for(c.get("lastRunResult"), c.get("status"))
            breakdown[bucket] += 1
            case_list.append({
                "id": c.get("id"),
                "title": c.get("title") or "(no title)",
                "lastRunResult": c.get("lastRunResult") or "",
                "status": c.get("status") or "",
                "bucket": bucket,
                "lastRunner": _name_of(c.get("lastRunner")) or "",
                "url": _case_url(c.get("id")),
            })

        # Demo data injection — first row of each iteration that has no real
        # cases gets a sample breakdown (5 pass / 10 fail / 15 in-prog / 30
        # unexec = 50% executed). Lets the user see what the chips look like
        # before real case linkage is wired up.
        is_demo = (idx == 0 and total_c == 0)
        if is_demo:
            counts = [("pass", 5), ("fail", 10), ("inProgress", 15), ("unexecuted", 30)]
            breakdown = {k: n for k, n in counts}
            breakdown["total"] = sum(n for _, n in counts)
            case_list = []
            seq = 1
            label_zh = {"pass": "通过", "fail": "失败",
                         "inProgress": "进行中", "unexecuted": "未执行"}
            for bucket, n in counts:
                for _ in range(n):
                    fake_id = f"demo_{ex_id}_{seq:03d}"
                    case_list.append({
                        "id": fake_id,
                        "title": f"[DEMO] {label_zh[bucket]} 用例样例 #{seq}",
                        "lastRunResult": bucket if bucket in ("pass", "fail") else "",
                        "status": "doing" if bucket == "inProgress" else ("normal" if bucket == "unexecuted" else "done"),
                        "bucket": bucket,
                        "lastRunner": "",
                        "url": "",
                        "demo": True,
                    })
                    seq += 1

        executed_c = breakdown["pass"] + breakdown["fail"]
        exec_rate_pct = round(executed_c / breakdown["total"] * 100) if breakdown["total"] else None

        # Highest-priority bug surfaces in the row tag (P1 = most urgent)
        worst_pri = min((b.get("pri") or 99) for b in story_bugs) if story_bugs else None
        severity_tag = f"P{worst_pri}" if worst_pri and worst_pri <= 4 else "—"

        requirements.append({
            "id": f"STORY-{sid}",
            "storyId": sid,
            "storyUrl": f"{ZENTAO_BASE}/story-view-{sid}.html",
            "title": s.get("title") or s.get("name") or "—",
            "status": _story_stage_zh(s.get("stage")),
            "qa": owner_info["owner"],
            "qaSource": owner_info["source"],
            "qaConfidence": owner_info["confidence"],
            "qaEvidence": owner_info["evidence"],
            "cases": breakdown["total"],
            "executedCases": executed_c,
            "execRatePct": exec_rate_pct,
            "caseBreakdown": breakdown,
            "caseList": case_list,
            "isDemo": is_demo,
            "bugs": len(story_bugs),
            "bugList": story_bugs,
            "severity": severity_tag,
        })

    return {"summary": summary, "requirements": requirements}


def _exec_summary_minimal(e: dict) -> dict:
    """Light execution record — no sub-data fetched yet. Used in
    `moreExecutions` (the dropdown candidates)."""
    start_d = _safe_date(e.get("begin") or e.get("openedDate"))
    end_d = _safe_date(e.get("end") or e.get("deadline"))
    status_lc = (e.get("status") or "").lower()
    zh_status = {"doing": "active", "wait": "planning",
                 "suspended": "closing", "closed": "done"}.get(status_lc, "active")
    return {
        "id": f"iter-{e.get('id')}",
        "name": e.get("name") or f"执行 {e.get('id')}",
        "code": f"EXEC-{e.get('id')}",
        "startDate": (start_d.strftime("%Y-%m-%d") if start_d else ""),
        "endDate":   (end_d.strftime("%Y-%m-%d") if end_d else ""),
        "status": zh_status,
        "progressPct": int(_as_float(e.get("progress"))),
        "project": e.get("project"),
        "detailLoaded": False,
    }


@app.get("/api/zentao/execution/{exec_id}/detail")
def zentao_execution_detail(exec_id: int, refresh: bool = False):
    """Per-execution detail (stories, bugs, testcases). Cached 5 min.
    Frontend calls this lazily when user picks an execution from the dropdown."""
    now = _time.time()
    if not refresh:
        hit = _ZT_EXEC_DETAIL_CACHE.get(exec_id)
        if hit and (now - hit[0]) < _ZT_DASHBOARD_TTL:
            cached = dict(hit[1])
            cached["cached"] = True
            return cached
    token = _zentao_token()
    if not token:
        return {"error": "ZENTAO_API_V2_TOKEN not set"}

    ex = _zt_get(f"/executions/{exec_id}", token) or {}
    if not ex or not ex.get("id"):
        return {"error": f"execution {exec_id} not found"}

    detail = _build_iter_detail(ex, token)
    detail["cached"] = False
    _ZT_EXEC_DETAIL_CACHE[exec_id] = (now, detail)
    return detail


def _empty_dashboard(error_msg: str = "") -> dict:
    return {
        "iterations": [], "moreExecutions": [],
        "requirementsByIter": {}, "modules": [],
        "qaThroughput": [],
        "autoTrend": [],
        "meta": {"error": error_msg, "cached": False,
                 "fetchedAt": datetime.now().isoformat()},
    }


def _local_story_generation_requirements() -> list[dict]:
    story_ids = [4161, 4266]
    requirements = []
    for sid in story_ids:
        rule = STORY_RULES[sid]
        requirements.append({
            "id": f"STORY-{sid}",
            "storyId": sid,
            "storyUrl": f"{ZENTAO_BASE}/execution-storyView-{sid}-614.html",
            "title": rule.title,
            "status": "进行中",
            "qa": "王一凡",
            "cases": 0,
            "executedCases": 0,
            "execRatePct": None,
            "caseBreakdown": {"pass": 0, "fail": 0, "inProgress": 0, "unexecuted": 0, "total": 0},
            "caseList": [],
            "isDemo": False,
            "bugs": 0,
            "bugList": [],
            "severity": "—",
        })
    return requirements


def _local_story_generation_iteration(requirements: list[dict]) -> dict:
    iteration = {
        "id": "iter-614",
        "name": "Execution 614 - local story generation fallback",
        "code": "EXEC-614",
        "startDate": "",
        "endDate": "",
        "status": "active",
        "daysLeft": 0,
        "totalDays": 0,
        "progressPct": 0,
        "storyTotal": len(requirements),
        "storyByStatus": {"待评审": 0, "已评审": 0, "进行中": len(requirements), "已完成": 0, "已发布": 0},
        "bugActive": 0,
        "bugClosed": 0,
        "bugP0": 0,
        "bugP1": 0,
        "bugMatrix": [[0, 0, 0] for _ in range(4)],
        "bugMatrixBugs": [[[], [], []] for _ in range(4)],
        "bugKpi": {"total": 0, "open": 0, "verifying": 0, "closed": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0},
        "testCases": 0,
        "autoTestCases": 0,
        "qaTeam": [{"name": "王一凡", "cases": 0, "auto": 0}],
        "detailLoaded": True,
    }
    return iteration


def _local_story_generation_dashboard(error_msg: str = "") -> dict:
    """Offline fallback so story-scoped generation still works during token refresh."""
    requirements = _local_story_generation_requirements()
    return {
        "iterations": [_local_story_generation_iteration(requirements)],
        "moreExecutions": [],
        "requirementsByIter": {"iter-614": requirements},
        "modules": [],
        "qaThroughput": [],
        "autoTrend": [],
        "meta": {
            "error": error_msg,
            "fallback": "local-story-generation",
            "cached": False,
            "fetchedAt": datetime.now().isoformat(),
        },
    }


def _merge_local_story_generation_entries(result: dict) -> dict:
    """Expose local story-case generation even if ZenTao omits story details."""
    iter_key = "iter-614"
    requirements_by_iter = result.setdefault("requirementsByIter", {})
    requirements = requirements_by_iter.setdefault(iter_key, [])
    existing_ids = {
        int(r.get("storyId"))
        for r in requirements
        if str(r.get("storyId") or "").isdigit()
    }
    additions = [
        r for r in _local_story_generation_requirements()
        if int(r["storyId"]) not in existing_ids
    ]
    if not additions:
        return result

    requirements.extend(additions)
    iterations = result.setdefault("iterations", [])
    more_executions = result.setdefault("moreExecutions", [])
    # Look in BOTH iterations and moreExecutions — historically this only
    # checked iterations and synthesised a duplicate iter-614 with the bogus
    # name 'Execution 614 - local story generation fallback', clobbering the
    # real '国际版官网V1.0' label in the dropdown / per-iter cards.
    target = (
        next((it for it in iterations if it.get("id") == iter_key), None)
        or next((it for it in more_executions if it.get("id") == iter_key), None)
    )
    if not target:
        # Real iter-614 not in this response at all (offline / token failure).
        # Only here is fabricating a placeholder appropriate.
        iterations.append(_local_story_generation_iteration(requirements))
    else:
        target["storyTotal"] = max(int(target.get("storyTotal") or 0), len(requirements))
        story_by_status = target.setdefault(
            "storyByStatus",
            {"待评审": 0, "已评审": 0, "进行中": 0, "已完成": 0, "已发布": 0},
        )
        story_by_status["进行中"] = max(int(story_by_status.get("进行中") or 0), len(additions))

    result.setdefault("meta", {})["localStoryGeneration"] = "story-4161-4266"
    return result


@app.get("/api/zentao/dashboard")
def zentao_dashboard(
    product_id: int = 0,                # 0 = all active executions (no product filter)
    refresh: bool = False,
    max_iterations: int = 6,
    project: str = "west-kowloon",
):
    """Aggregate ZenTao data for the ZenTao Integration page.

    Returns: {iterations, moreExecutions, requirementsByIter, modules,
    qaThroughput, autoTrend, meta}. Each iteration carries its own
    bugMatrix / bugMatrixBugs / bugKpi (per-exec bug breakdown).
    Cached 5 minutes per project/product/execution — pass
    refresh=true to bypass."""
    cfg = _project_config(project)
    project_key = cfg["key"]
    mapped_product_id = int(cfg.get("zentaoProductId") or 0)
    mapped_execution_id = int(cfg.get("zentaoExecutionId") or 0)
    execution_scoped = mapped_execution_id > 0
    if not mapped_product_id and not mapped_execution_id:
        empty = _empty_dashboard(f"No ZenTao product or execution is mapped for project {project_key}.")
        empty["meta"].update({
            "project": project_key,
            "productId": None,
            "executionId": None,
            "scope": "unmapped-project",
        })
        return empty
    if mapped_product_id:
        product_id = mapped_product_id

    cache_key = (
        f"project:{project_key}:product:{product_id}:"
        f"execution:{mapped_execution_id or 'all'}:max:{max_iterations}"
    )
    now = _time.time()

    if not refresh:
        hit = _ZT_DASHBOARD_CACHE.get(cache_key)
        if hit and (now - hit[0]) < _ZT_DASHBOARD_TTL:
            cached_result = dict(hit[1])
            cached_result["meta"] = {**cached_result.get("meta", {}), "cached": True}
            return cached_result

    token = _zentao_token()
    if not token:
        if project_key == "west-kowloon":
            return _local_story_generation_dashboard("ZENTAO_API_V2_TOKEN not set")
        empty = _empty_dashboard("ZENTAO_API_V2_TOKEN not set")
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "unmapped-project",
        })
        return empty
    global _ZT_LAST_ERROR
    _ZT_LAST_ERROR = None

    # --- 1. Executions list ------------------------------------------------
    # In platform mode the selected dashboard project owns the ZenTao scope.
    # Prefer the execution explicitly mapped in PROJECT_CATALOG; otherwise fall
    # back to the historical all-active behavior for unmapped/internal views.
    from concurrent.futures import ThreadPoolExecutor
    if execution_scoped:
        mapped_exec = _zt_get(f"/executions/{mapped_execution_id}", token, critical=True) or {}
        executions = [mapped_exec] if mapped_exec.get("id") else []
    else:
        def _fetch_status(status: str):
            return _zt_get("/executions", token,
                           {"limit": 100, "status": status}, critical=True) or {}
        with ThreadPoolExecutor(max_workers=2) as _list_pool:
            doing_resp, wait_resp = _list_pool.map(_fetch_status, ["doing", "wait"])
        execs_doing = doing_resp.get("executions") or doing_resp.get("data") or []
        execs_wait  = wait_resp.get("executions")  or wait_resp.get("data")  or []
        executions = execs_doing + execs_wait
    if not executions and _ZT_LAST_ERROR:
        if project_key == "west-kowloon":
            return _local_story_generation_dashboard(_ZT_LAST_ERROR)
        empty = _empty_dashboard(_ZT_LAST_ERROR)
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "unmapped-project",
        })
        return empty
    if not executions and execution_scoped:
        empty = _empty_dashboard(f"Mapped ZenTao execution {mapped_execution_id} not found")
        empty["meta"].update({
            "project": project_key,
            "productId": product_id,
            "executionId": mapped_execution_id,
            "scope": f"execution:{mapped_execution_id}",
        })
        return empty

    today = datetime.now()
    # "最近活跃优先" — use realBegan (actually started) when present, else
    # planned begin, else openedDate. Also prefer 'doing' over 'wait'.
    def _exec_sort_key(e):
        status_rank = {"doing": 2, "suspended": 1, "wait": 0}.get(
            (e.get("status") or "").lower(), 0)
        d = (_safe_date(e.get("realBegan"))
             or _safe_date(e.get("begin"))
             or _safe_date(e.get("openedDate")))
        ts = d.timestamp() if d else 0
        return (status_rank, ts)
    if execution_scoped:
        active_execs = executions[:1]
    else:
        executions.sort(key=_exec_sort_key, reverse=True)
        active_execs = [
            e for e in executions
            if (e.get("status") or "").lower() in ("doing", "wait", "suspended")
        ][:max_iterations]

    iterations = []
    requirements_by_iter = {}

    # Parallel-fetch every (exec_id, resource) sub-call PLUS the two
    # product-level fetches in one big pool. ZenTao SaaS is ~1-2s per call
    # — 16 workers brings 26 fetches from ~52s down to ~5-8s.
    from concurrent.futures import ThreadPoolExecutor
    SUB_RESOURCES = ("stories", "bugs", "testcases", "tasks")
    iter_tasks = [(ex.get("id"), r) for ex in active_execs if ex.get("id") for r in SUB_RESOURCES]

    def _fetch_iter(args):
        ex_id, resource = args
        # Use bigger page sizes for bugs/cases/tasks (some execs have 200+ each)
        limit = 500 if resource in ("bugs", "testcases", "tasks") else 200
        return ("iter", ex_id, resource,
                _zt_get(f"/executions/{ex_id}/{resource}", token, {"limit": limit}) or {})

    def _fetch_product_cases():
        if product_id > 0 and not execution_scoped:
            return ("product", "cases",
                    _zt_get(f"/products/{product_id}/testcases", token, {"limit": 500}) or {})
        return ("product", "cases", {})

    def _fetch_product_bugs():
        if product_id > 0 and not execution_scoped:
            return ("product", "bugs",
                    _zt_get(f"/products/{product_id}/bugs", token, {"limit": 500, "status": "active"}) or {})
        return ("product", "bugs", {})

    def _fetch_testtasks():
        # Shared across all per-iter builds — one /testtasks call total
        return ("global", "testtasks",
                _zt_get("/testtasks", token, {"limit": 500}) or {})

    sub_responses: dict[tuple, dict] = {}
    product_cases_resp: dict = {}
    product_bugs_resp: dict = {}
    testtasks_resp: dict = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_fetch_iter, t) for t in iter_tasks]
        futures.append(pool.submit(_fetch_product_cases))
        futures.append(pool.submit(_fetch_product_bugs))
        futures.append(pool.submit(_fetch_testtasks))
        for fut in futures:
            res = fut.result()
            if res[0] == "iter":
                _, ex_id, resource, resp = res
                sub_responses[(ex_id, resource)] = resp
            elif res[0] == "product" and res[1] == "cases":
                product_cases_resp = res[2]
            elif res[0] == "product" and res[1] == "bugs":
                product_bugs_resp = res[2]
            elif res[0] == "global" and res[1] == "testtasks":
                testtasks_resp = res[2]

    for ex in active_execs:
        ex_id = ex.get("id")
        if not ex_id:
            continue
        # Pull the 3 pre-fetched sub-responses for this exec + the shared
        # testtasks response. Let the helper turn them into a summary +
        # requirements list (with per-story bug list, exec-wide QA owner).
        per_iter_subs = {
            "stories":   sub_responses.get((ex_id, "stories"), {}),
            "bugs":      sub_responses.get((ex_id, "bugs"), {}),
            "testcases": sub_responses.get((ex_id, "testcases"), {}),
            "tasks":     sub_responses.get((ex_id, "tasks"), {}),
            "testtasks": testtasks_resp,
        }
        built = _build_iter_detail(ex, token, sub_responses=per_iter_subs)
        iterations.append(built["summary"])
        requirements_by_iter[built["summary"]["id"]] = built["requirements"]
        # Also seed the per-exec detail cache so any later dropdown click is instant.
        _ZT_EXEC_DETAIL_CACHE[ex_id] = (now, built)

    # Light list of every other active/wait execution — frontend uses these to
    # populate the searchable dropdown without firing N sub-fetches up front.
    seen_ids = {ex.get("id") for ex in active_execs}
    more_executions = [] if execution_scoped else [
        _exec_summary_minimal(e)
        for e in executions
        if e.get("id") and e["id"] not in seen_ids
        and (e.get("status") or "").lower() in ("doing", "wait", "suspended")
    ]

    # --- 2. All testcases for the product (for modules / QA throughput / trend)
    # If no product was selected, aggregate across the iterations we already
    # have (less data but no extra ZenTao round-trips).
    all_cases: list[dict] = []
    if product_id > 0 and not execution_scoped:
        all_cases_resp = product_cases_resp
        all_cases = (all_cases_resp.get("data")
                     or all_cases_resp.get("cases")
                     or all_cases_resp.get("testcases") or [])
    else:
        # Project execution scope, or no product selected: reuse the testcases
        # already fetched per execution. Sum them up, dedupe by case id.
        seen = set()
        for ex in active_execs:
            cr = sub_responses.get((ex.get("id"), "testcases"), {})
            for c in (cr.get("data") or cr.get("cases") or cr.get("testcases") or []):
                cid = c.get("id")
                if cid and cid not in seen:
                    seen.add(cid)
                    all_cases.append(c)

    # Module rollup
    module_counts: dict[str, dict] = {}
    for c in all_cases:
        mod = _name_of(c.get("module")) or "未分类"
        d = module_counts.setdefault(mod, {"cases": 0, "auto": 0})
        d["cases"] += 1
        if _is_auto(c):
            d["auto"] += 1
    modules = [
        {"name": k, "cases": v["cases"], "auto": v["auto"]}
        for k, v in sorted(module_counts.items(), key=lambda x: -x[1]["cases"])
    ][:12]

    # --- 3. (was global S×P heatmap — superseded by per-iter bugMatrix.) -

    # --- 4. QA throughput across recent months ---------------------------
    from collections import defaultdict
    qa_iter_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in all_cases:
        opened = c.get("openedDate") or ""
        if not opened:
            continue
        month_key = opened[:7]
        qa_name = _name_of(c.get("openedBy"))
        if not qa_name:
            continue
        qa_iter_counts[qa_name][month_key] += 1

    all_months = sorted({m for q, ms in qa_iter_counts.items() for m in ms})[-4:]
    top_qas = sorted(qa_iter_counts.items(), key=lambda x: -sum(x[1].values()))[:5]
    qa_throughput = [
        {
            "qa": qa,
            "data": [{"iter": m[-2:], "cases": qa_iter_counts[qa].get(m, 0)} for m in all_months],
        }
        for qa, _ in top_qas
    ]

    # --- 5. Automation trend (cumulative auto% by month, last 6) ---------
    auto_trend = []
    today_dt = datetime.now().replace(day=1)
    for i in range(5, -1, -1):
        target_m = (today_dt - timedelta(days=i*32)).strftime("%Y-%m")
        label = target_m[-2:]
        cases_up_to_m = [c for c in all_cases if (c.get("openedDate") or "")[:7] <= target_m]
        if not cases_up_to_m:
            auto_trend.append({"month": label, "pct": 0})
            continue
        auto_n = sum(1 for c in cases_up_to_m if _is_auto(c))
        auto_trend.append({"month": label, "pct": round(auto_n / len(cases_up_to_m) * 100)})

    # Total active bugs across loaded execs — for the meta strip only.
    total_active_bugs = 0
    if product_id > 0 and not execution_scoped:
        total_active_bugs = sum(
            1 for b in (product_bugs_resp.get("data")
                        or product_bugs_resp.get("bugs") or [])
            if (b.get("status") or "").lower() == "active"
        )
    else:
        seen: set = set()
        for ex in active_execs:
            br = sub_responses.get((ex.get("id"), "bugs"), {})
            for b in (br.get("data") or br.get("bugs") or []):
                if (b.get("status") or "").lower() != "active":
                    continue
                bid = b.get("id")
                if bid and bid not in seen:
                    seen.add(bid)
                    total_active_bugs += 1

    result = {
        "iterations": iterations,
        "moreExecutions": more_executions,
        "requirementsByIter": requirements_by_iter,
        "modules": modules,
        "qaThroughput": qa_throughput,
        "autoTrend": auto_trend,
        "meta": {
            "productId": product_id,
            "project": project_key,
            "executionId": mapped_execution_id or None,
            "scope": f"execution:{mapped_execution_id}" if mapped_execution_id else "all-active-executions",
            "fetchedAt": datetime.now().isoformat(),
            "cached": False,
            "activeIterations": len(active_execs),
            "totalActive": len(active_execs) + len(more_executions),
            "totalCasesInProduct": len(all_cases),
            "totalActiveBugs": total_active_bugs,
            "error": None,
        },
    }
    if project_key == "west-kowloon":
        result = _merge_local_story_generation_entries(result)
    _ZT_DASHBOARD_CACHE[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# Quality System — Package Health (Phase 1)
#
# Reads the live filesystem state of the selected project's requirement
# packages and returns per-stage health. Filesystem IS the data source; no DB
# tables are involved.
# ---------------------------------------------------------------------------


@app.get("/api/quality-system/packages")
def list_quality_packages(project: str = "west-kowloon"):
    """Return a compact list of all packages under <project>/01-requirements
    with a per-stage summary. Recomputed on every request (manual refresh)."""
    if package_scanner is None:
        return {"error": "package_scanner not available", "packages": []}
    results = package_scanner.scan_workspace(_workspace_root, project=project)
    return {
        "project": project,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "package_count": len(results),
        "stage_defs": package_scanner.STAGE_DEFS,
        "packages": [package_scanner.to_jsonable(r) for r in results],
    }


# ---- Phase 2: file actions (open / generate docx / run validator) ---------
#
# All three endpoints share the same security model:
#   - input path is a workspace-relative path with forward slashes
#   - resolve against _workspace_root and reject anything that escapes it
#   - reject if file/dir doesn't exist
#
# These endpoints have side effects (open file in OS, write new docx, run
# subprocess), so we use POST not GET.

import os as _os
import subprocess as _subprocess

# Force child Python processes to write UTF-8 to stdout/stderr so we can
# decode their output cleanly when it contains Chinese (validator filenames,
# md_docx.py paths, etc.). Otherwise the Windows console codec (gbk by
# default) mangles non-gbk characters before we ever see them.
_CHILD_ENV = {**_os.environ, "PYTHONIOENCODING": "utf-8"}


class _PathPayload(BaseModel):
    path: str  # workspace-relative path with forward slashes


def _resolve_safe(path: str) -> Optional[Path]:
    """Resolve a workspace-relative path; return None if it escapes the
    workspace or doesn't exist."""
    target = (_workspace_root / path).resolve()
    try:
        target.relative_to(_workspace_root)
    except ValueError:
        return None
    if not target.exists():
        return None
    return target


@app.post("/api/quality-system/open-file")
def open_file(payload: _PathPayload):
    """Open a file in the OS default application (Word/WPS for .docx,
    Notepad/VS Code for .md, etc.). Windows uses os.startfile.
    """
    target = _resolve_safe(payload.path)
    if target is None:
        return {"ok": False, "error": "path not found or outside workspace"}
    if not target.is_file():
        return {"ok": False, "error": "path is not a file"}
    try:
        if hasattr(_os, "startfile"):
            _os.startfile(str(target))  # Windows native
        else:
            # Fallback for non-Windows (xdg-open / open)
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            _subprocess.Popen([opener, str(target)])
        return {"ok": True, "opened": str(target)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/quality-system/generate-docx")
def generate_docx(payload: _PathPayload):
    """Run md_docx.py to-docx on a workspace-relative .md path. Returns
    the generated .docx path on success."""
    target = _resolve_safe(payload.path)
    if target is None:
        return {"ok": False, "error": "path not found or outside workspace"}
    if target.suffix.lower() != ".md":
        return {"ok": False, "error": "path is not a .md file"}
    tool = _repo_root / "01-system" / "03-tools" / "md_docx.py"
    out_docx = target.with_suffix(".docx")
    try:
        result = _subprocess.run(
            [sys.executable, str(tool), "to-docx", str(target)],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace", env=_CHILD_ENV,
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "error": "md_docx.py failed",
                "stdout": result.stdout[-500:],
                "stderr": result.stderr[-500:],
            }
        rel = str(out_docx.relative_to(_workspace_root)).replace("\\", "/")
        return {"ok": True, "docx_path": rel, "abs_path": str(out_docx)}
    except _subprocess.TimeoutExpired:
        return {"ok": False, "error": "md_docx.py timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _extract_case_ids(xlsx_path: Path) -> set[str]:
    """Read the Test Case ID column from a test-cases-*.xlsx and return the
    set of valid case IDs. The column position is discovered from the header
    row — West Kowloon's template has a leading 'Label' column that pushes
    'Test Case ID' to column B, so a fixed column index would miss it.
    Silently returns empty set on any failure — non-fatal."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(xlsx_path, data_only=True, read_only=True)
        if "Test Cases" not in wb.sheetnames:
            return set()
        ws = wb["Test Cases"]
        header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
        case_col = None
        for i, h in enumerate(header):
            if h and isinstance(h, str) and "Test Case ID" in h:
                case_col = i  # 0-based
                break
        if case_col is None:
            return set()
        ids: set[str] = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            if case_col >= len(row):
                continue
            v = row[case_col]
            if v and isinstance(v, str):
                v = v.strip()
                # Match e.g. SIT-TC-WEB-AUTH-001 or SIT-TC-AMW-017
                if re.match(r"^[A-Z]+(-[A-Z]+)+-\d+$", v):
                    ids.add(v)
        return ids
    except Exception:
        return set()


@app.get("/api/quality-system/packages/{package_id:path}/executions")
def get_package_executions(package_id: str):
    """Pull dashboard.db test_scenarios whose name or legacy tag matches any case ID
    from the package's xlsx files. Returns the most recent runs that
    exercised this package's scope, with per-scope pass/fail counts."""
    pkg = _resolve_safe(package_id)
    if pkg is None or not pkg.is_dir():
        return {"error": "package not found"}

    case_ids: set[str] = set()
    test_design = pkg / "03-test-design"
    if test_design.is_dir():
        for x in test_design.rglob("test-cases-*.xlsx"):
            case_ids.update(_extract_case_ids(x))

    if not case_ids:
        return {
            "package_id": package_id,
            "case_ids": [],
            "case_count": 0,
            "runs": [],
            "note": "no case IDs extracted from xlsx",
        }

    from collections import defaultdict
    from sqlalchemy import or_

    db = get_db()
    try:
        # Build OR conditions: scenario tag OR name contains any of the IDs.
        # Use case-insensitive LIKE for robustness.
        conditions = []
        for cid in case_ids:
            conditions.append(TestScenario.tags.like(f"%{cid}%"))
            conditions.append(TestScenario.name.like(f"%{cid}%"))
        scenarios = db.query(TestScenario).filter(or_(*conditions)).all()

        # Group by run_id, count per-scope stats.
        per_run: dict[int, dict] = defaultdict(
            lambda: {"matched": 0, "passed": 0, "failed": 0, "skipped": 0, "errored": 0}
        )
        for s in scenarios:
            stats = per_run[s.run_id]
            stats["matched"] += 1
            key = s.status if s.status in ("passed", "failed", "skipped", "errored") else "errored"
            stats[key] += 1

        run_ids = list(per_run.keys())
        if not run_ids:
            return {
                "package_id": package_id,
                "case_ids": sorted(case_ids),
                "case_count": len(case_ids),
                "runs": [],
                "note": "no matching runs in dashboard.db",
            }

        runs = (
            db.query(TestRun)
            .filter(TestRun.id.in_(run_ids))
            .order_by(TestRun.started_at.desc())
            .limit(20)
            .all()
        )

        result_runs = []
        for r in runs:
            stats = per_run[r.id]
            result_runs.append({
                "id": r.id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "status": r.status,
                "env": r.env,
                "tags": r.tags,
                "scope_matched": stats["matched"],
                "scope_passed": stats["passed"],
                "scope_failed": stats["failed"],
                "scope_skipped": stats["skipped"],
                "scope_errored": stats["errored"],
                "total_in_run": r.total,
            })
        return {
            "package_id": package_id,
            "case_ids": sorted(case_ids),
            "case_count": len(case_ids),
            "runs": result_runs,
        }
    finally:
        db.close()


@app.post("/api/quality-system/packages/{package_id:path}/validate-xlsx")
def validate_package_xlsx(package_id: str):
    """Run validate_testcase_xlsx.py against every test-cases-*.xlsx in
    this package's 03-test-design tree. Returns one result per xlsx."""
    pkg = _resolve_safe(package_id)
    if pkg is None or not pkg.is_dir():
        return {"ok": False, "error": "package not found"}
    test_design = pkg / "03-test-design"
    xlsx_files = sorted(test_design.rglob("test-cases-*.xlsx")) if test_design.is_dir() else []
    if not xlsx_files:
        return {"ok": True, "package_id": package_id, "results": [], "summary": "no xlsx to validate"}
    tool = _repo_root / "01-system" / "03-tools" / "validate_testcase_xlsx.py"
    results = []
    for x in xlsx_files:
        try:
            r = _subprocess.run(
                [sys.executable, str(tool), str(x)],
                capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace", env=_CHILD_ENV,
            )
            results.append({
                "file": str(x.relative_to(_workspace_root)).replace("\\", "/"),
                "ok": r.returncode == 0,
                "exit_code": r.returncode,
                "output": (r.stdout + r.stderr).strip()[-1200:],
            })
        except _subprocess.TimeoutExpired:
            results.append({
                "file": str(x.relative_to(_workspace_root)).replace("\\", "/"),
                "ok": False,
                "exit_code": -1,
                "output": "timeout",
            })
    passed = sum(1 for r in results if r["ok"])
    return {
        "ok": True,
        "package_id": package_id,
        "summary": f"{passed}/{len(results)} xlsx passed",
        "results": results,
    }


# Catch-all package detail route MUST come last in the quality-system block —
# {package_id:path} would otherwise swallow `/executions` and `/validate-xlsx`
# suffixes (FastAPI matches GET routes in source order).
@app.get("/api/quality-system/packages/{package_id:path}")
def get_quality_package(package_id: str):
    """Return full detail for one package. package_id is the workspace-
    relative path with forward slashes, e.g.
    `west-kowloon/01-requirements/02-subprojects/02-website/02-modules/08-discount/2026-06-25`.
    """
    if package_scanner is None:
        return {"error": "package_scanner not available"}
    target = (_workspace_root / package_id).resolve()
    try:
        target.relative_to(_workspace_root)
    except ValueError:
        return {"error": "package_id outside workspace"}
    if not target.is_dir():
        return {"error": "package not found", "package_id": package_id}
    detail = package_scanner.scan_package(target)
    return package_scanner.to_jsonable(detail)
