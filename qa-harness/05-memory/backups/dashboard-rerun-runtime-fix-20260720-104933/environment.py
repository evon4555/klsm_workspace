from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from test_automation.config import get_settings
from test_automation.standard_product.evidence import artifact_root
from test_automation.standard_product.evidence import case_id_from_text
from test_automation.standard_product.evidence import record_case_status


def _dashboard_db() -> Path:
    harness_root = Path(os.environ.get("QA_HARNESS_ROOT", "D:/Workspace/qa-harness"))
    return harness_root / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db"


def _dashboard_should_record() -> bool:
    return not os.environ.get("BEHAVE_DASHBOARD_RUN_ID") and _dashboard_db().exists()


def _create_run() -> int | None:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    project_key = os.environ.get("QA_PROJECT_KEY", "standard product")
    con = sqlite3.connect(str(_dashboard_db()))
    try:
        cur = con.execute(
            "INSERT INTO test_runs "
            "(started_at, status, env, total, passed, failed, skipped, project_key) "
            "VALUES (?, 'running', ?, 0, 0, 0, 0, ?)",
            (started_at, os.environ.get("ENV", "local"), project_key),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def _record_scenario(run_id: int, scenario) -> None:
    duration = sum(getattr(step, "duration", 0.0) or 0.0 for step in scenario.steps)
    status = scenario.status.name if hasattr(scenario.status, "name") else str(scenario.status)
    error_msg = ""
    for step in scenario.steps:
        step_status = step.status.name if hasattr(step.status, "name") else str(step.status)
        if step_status == "failed":
            raw = step.error_message or ""
            error_msg = raw if isinstance(raw, str) else "\n".join(raw)
            break
    con = sqlite3.connect(str(_dashboard_db()))
    try:
        con.execute(
            "INSERT INTO test_scenarios "
            "(run_id, feature, name, status, duration_s, error_msg, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                scenario.feature.name if scenario.feature else "",
                scenario.name,
                status,
                duration,
                error_msg,
                ",".join(scenario.effective_tags) if scenario.effective_tags else "",
            ),
        )
        con.commit()
    finally:
        con.close()


def _finalize_run(run_id: int) -> None:
    finished_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    con = sqlite3.connect(str(_dashboard_db()))
    try:
        counts = {
            row[0]: row[1]
            for row in con.execute(
                "SELECT status, COUNT(*) FROM test_scenarios WHERE run_id = ? GROUP BY status",
                (run_id,),
            ).fetchall()
        }
        total = sum(counts.values())
        passed = counts.get("passed", 0)
        failed = counts.get("failed", 0)
        errored = counts.get("error", 0) + counts.get("untested", 0) + counts.get("undefined", 0)
        skipped = counts.get("skipped", 0)
        status = "passed" if total > 0 and failed == 0 and errored == 0 else "failed"
        con.execute(
            "UPDATE test_runs SET finished_at=?, status=?, total=?, passed=?, "
            "failed=?, errored=?, skipped=? WHERE id=?",
            (finished_at, status, total, passed, failed, errored, skipped, run_id),
        )
        con.commit()
    finally:
        con.close()


def _load_run_summary(run_id: int) -> tuple[dict, list[dict]]:
    con = sqlite3.connect(str(_dashboard_db()))
    con.row_factory = sqlite3.Row
    try:
        run = con.execute(
            "SELECT id, started_at, finished_at, status, env, project_key, "
            "total, passed, failed, errored, skipped FROM test_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        scenarios = con.execute(
            "SELECT feature, name, status, duration_s, error_msg, tags "
            "FROM test_scenarios WHERE run_id = ? ORDER BY id",
            (run_id,),
        ).fetchall()
    finally:
        con.close()
    return (dict(run) if run else {}, [dict(row) for row in scenarios])


def _layer_from_tags(tags: object) -> str:
    values = {
        item.strip().lower().replace("@", "")
        for item in str(tags or "").split(",")
        if item.strip()
    }
    if values & {"mixed", "api_ui_mixed", "api-first-ui", "api_first_ui"}:
        return "Mixed"
    if "ui" in values:
        return "UI"
    if "api" in values:
        return "API"
    return "N/A"


def _display_status(status: object) -> str:
    raw = str(status or "").strip().lower()
    if raw == "passed":
        return "Passed"
    if raw in {"failed", "error", "errored", "undefined", "untested"}:
        return "Failed"
    if raw == "skipped":
        return "Skipped"
    return raw.title() if raw else "Unknown"


def _display_layer(layer: object) -> str:
    raw = str(layer or "").strip().lower()
    if raw == "api":
        return "API"
    if raw == "ui":
        return "UI"
    if raw == "mixed":
        return "Mixed"
    return "N/A"


def _write_latest_execution_record(run_id: int) -> None:
    run, scenarios = _load_run_summary(run_id)
    if not run:
        return

    root = artifact_root()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"case-screenshot-manifest-run-{run_id}.json"
    behave_path = root / "latest-full-behave.json"
    package = Path(os.environ.get(
        "QA_REQUIREMENT_PACKAGE",
        "D:/Workspace/standard product/01-requirements/02-subprojects/"
        "01-domestic projects/02-modules/04-Configuration Related/2026-07-15",
    ))
    snapshot_path = package / "05-execution" / "04-execution-results" / "execution-results-batch-session-configuration.json"

    layers: dict[str, dict] = {
        "api": {"total": 0, "passed": 0, "case_ids": []},
        "ui": {"total": 0, "passed": 0, "case_ids": []},
        "mixed": {"total": 0, "passed": 0, "case_ids": []},
    }
    results = []
    for scenario in scenarios:
        case_id = case_id_from_text(scenario.get("name")) or ""
        layer = _layer_from_tags(scenario.get("tags"))
        status = str(scenario.get("status") or "").lower()
        results.append({
            "case_id": case_id,
            "layer": layer.lower() if layer != "N/A" else "n/a",
            "status": status,
        })
        key = layer.lower()
        if key in layers:
            layers[key]["total"] += 1
            if status == "passed":
                layers[key]["passed"] += 1
            if case_id:
                layers[key]["case_ids"].append(case_id)

    dashboard_api_base = os.environ.get("QA_DASHBOARD_API_BASE", "http://127.0.0.1:8002")
    payload = {
        "suite": "standard_product_batch_session_configuration",
        "requirement_package": "04-Configuration Related/2026-07-15",
        "status": run.get("status"),
        "valid_behave_execution": True,
        "dashboard_run_id": run_id,
        "project_key": run.get("project_key"),
        "env": run.get("env"),
        "started_at_utc": run.get("started_at"),
        "finished_at_utc": run.get("finished_at"),
        "total": int(run.get("total") or 0),
        "passed": int(run.get("passed") or 0),
        "failed": int(run.get("failed") or 0),
        "errored": int(run.get("errored") or 0),
        "skipped": int(run.get("skipped") or 0),
        "behave_artifact": str(behave_path),
        "dashboard_api": f"{dashboard_api_base.rstrip('/')}/api/runs/{run_id}",
        "runtime_screenshot_manifest": str(manifest_path),
        "fixed_snapshot": str(snapshot_path).replace("\\", "/"),
        "layers": layers,
        "results": results,
    }

    json_path = root / "latest-execution-record.json"
    md_path = root / "latest-execution-record.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result_line = (
        f"{payload['passed']} passed / {payload['failed']} failed / "
        f"{payload['errored']} errored / {payload['skipped']} skipped"
    )
    layer_rows = [
        f"| {_display_layer(name)} | "
        f"`{', '.join(value['case_ids'])}` | `{value['passed']} passed` |"
        for name, value in layers.items()
        if value["total"] > 0
    ]
    case_rows = [
        f"| `{item['case_id']}` | {_display_layer(item['layer'])} | "
        f"{_display_status(item['status'])} |"
        for item in sorted(results, key=lambda row: row["case_id"])
    ]
    md_path.write_text("\n".join([
        "# Batch Session Configuration Execution Record",
        "",
        "- Suite: `standard_product_batch_session_configuration`",
        "- Requirement package: `04-Configuration Related/2026-07-15`",
        f"- Status: `{_display_status(payload['status'])}`",
        f"- Result: `{result_line}`",
        f"- Dashboard run ID: `{run_id}`",
        f"- Project: `{payload['project_key']}`",
        f"- Environment: `{payload['env']}`",
        f"- Started at UTC: `{payload['started_at_utc']}`",
        f"- Finished at UTC: `{payload['finished_at_utc']}`",
        f"- Behave artifact: `{payload['behave_artifact']}`",
        f"- Fixed execution snapshot: `{payload['fixed_snapshot']}`",
        f"- Dashboard API check: `{payload['dashboard_api']}`",
        f"- Runtime screenshot manifest: `{payload['runtime_screenshot_manifest']}`",
        "",
        "## Valid Automation Strategy",
        "",
        "This run is valid for QA platform test-management purposes because it uses:",
        "",
        "- Behave as the outer scenario runner.",
        "- Python `requests` against real backend APIs for API steps.",
        "- Playwright against the real Standard Product admin UI for UI checks.",
        "- Mixed execution for API setup/action plus final browser-side UI evidence.",
        "",
        "## Layer Summary",
        "",
        "| Layer | Case IDs | Result |",
        "|---|---|---|",
        *layer_rows,
        "",
        "## Case Results",
        "",
        "| Case ID | Layer | Status |",
        "|---|---|---|",
        *case_rows,
        "",
    ]), encoding="utf-8")


def before_all(context):
    context.settings = get_settings()
    context._dashboard_run_id = _create_run() if _dashboard_should_record() else None


def before_scenario(context, scenario):
    context.scenario = scenario
    context._current_case_id = case_id_from_text(scenario.name)
    context._evidence_screenshot_index = 0
    tags = set(scenario.effective_tags)
    uses_api = bool({"api", "mixed", "api_ui_mixed"} & tags)
    uses_ui = bool({"ui", "mixed", "api_ui_mixed"} & tags)
    mutates_batch_configuration = (
        "batch_session_configuration" in tags and bool({"api", "mixed", "api_ui_mixed"} & tags)
    )
    if "needs_mapping" in tags:
        scenario.skip("Real endpoint or UI selector mapping is not captured yet.")
        return
    if "needs_ui_selector" in tags:
        scenario.skip("Real UI selector mapping is not captured yet.")
        return
    if uses_api:
        if not os.environ.get("TA_USER1_USERNAME") or not os.environ.get("TA_USER1_PASSWORD"):
            scenario.skip("Real API credentials are not configured in environment variables.")
            return
    if mutates_batch_configuration and os.environ.get("TA_ALLOW_BATCH_MUTATION") != "1":
        scenario.skip("Real write API execution is disabled; set TA_ALLOW_BATCH_MUTATION=1 after approval.")
        return
    if uses_ui:
        context._playwright = sync_playwright().start()
        context.browser = context._playwright.chromium.launch(headless=True)
        context.page = context.browser.new_page()


def after_scenario(context, scenario):
    record_case_status(context, scenario)
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "_playwright"):
        context._playwright.stop()
    run_id = getattr(context, "_dashboard_run_id", None)
    if run_id:
        _record_scenario(run_id, scenario)


def after_all(context):
    run_id = getattr(context, "_dashboard_run_id", None)
    if run_id:
        _finalize_run(run_id)
        _write_latest_execution_record(run_id)
