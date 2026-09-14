"""Promote selected automation runtime artifacts into durable evidence.

Runtime output stays in 02-automation/07-artifacts. This tool copies one
review-worthy run into 03-evidence/automation/... and writes a manifest that
the QA dashboard can use as an evidence-backed Quality Gate input.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "wk-evidence-manifest/v1"
DEFAULT_DELIVERABLES = ["p5-d1", "p5-d2", "p5-d4", "p6-d3", "p6-d4"]
CASE_ID_RE = re.compile(r"\b[A-Z]{2,5}-TC-[A-Z]+-[A-Z]+-\d{3}\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return slug or "unknown"


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_scenarios(behave_json: list[dict[str, Any]]):
    for feature in behave_json:
        for element in feature.get("elements") or []:
            if element.get("type") == "scenario":
                yield feature, element


def summarize_behave(behave_json: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"passed": 0, "failed": 0, "errored": 0, "skipped": 0, "undefined": 0}
    case_ids: set[str] = set()
    features = len(behave_json)
    scenarios = []

    for feature, scenario in iter_scenarios(behave_json):
        status = (scenario.get("status") or "unknown").lower()
        if status in counts:
            counts[status] += 1
        elif status in {"error", "hook_error"}:
            counts["errored"] += 1
        else:
            counts.setdefault(status, 0)
            counts[status] += 1

        text = " ".join([
            str(feature.get("name") or ""),
            str(feature.get("location") or ""),
            str(scenario.get("name") or ""),
            " ".join(str(t) for t in scenario.get("tags") or []),
        ])
        case_ids.update(CASE_ID_RE.findall(text))
        scenarios.append({
            "feature": feature.get("name"),
            "name": scenario.get("name"),
            "status": status,
            "location": scenario.get("location"),
            "tags": scenario.get("tags") or [],
        })

    total = sum(counts.values())
    passed = counts.get("passed", 0)
    executed = total - counts.get("skipped", 0)
    return {
        "featureCount": features,
        "scenarioCount": total,
        "executed": executed,
        "passed": passed,
        "failed": counts.get("failed", 0),
        "errored": counts.get("errored", 0) + counts.get("undefined", 0),
        "skipped": counts.get("skipped", 0),
        "passRate": round((passed / executed) * 100, 1) if executed else 0,
        "statusCounts": counts,
        "testCaseIds": sorted(case_ids),
        "scenarios": scenarios,
    }


def copy_file(src: Path, dst: Path, evidence_root: Path, kind: str) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "kind": kind,
        "path": relpath(dst, evidence_root),
        "sourcePath": str(src.resolve()).replace("\\", "/"),
        "sha256": sha256_file(dst),
        "sizeBytes": dst.stat().st_size,
    }


def files_within_window(root: Path, center: datetime, minutes: int, suffixes: set[str]) -> list[Path]:
    if not root.exists():
        return []
    lower = center.timestamp() - minutes * 60
    upper = center.timestamp() + minutes * 60
    hits = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        mtime = path.stat().st_mtime
        if lower <= mtime <= upper:
            hits.append(path)
    return sorted(hits)


def gate_for_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    summary = manifest["summary"]
    artifacts = manifest["artifacts"]

    if not manifest.get("environment"):
        issues.append("environment is required")
    if not manifest.get("build"):
        issues.append("build/version is required")
    if summary["scenarioCount"] == 0:
        issues.append("run has no scenario-level execution records")
    if summary["failed"] or summary["errored"]:
        if not manifest.get("defects") and not manifest.get("knownRisks"):
            issues.append("failed/errored run requires defects or knownRisks")
    if not any(a["kind"] == "run-json" for a in artifacts):
        issues.append("run JSON artifact is required")
    if not any(a["kind"] in {"screenshot", "log", "api-evidence", "report"} for a in artifacts):
        issues.append("at least one human-reviewable evidence artifact is required")
    if not manifest.get("qualityDeliverables"):
        issues.append("qualityDeliverables mapping is required")
    if not summary["testCaseIds"]:
        warnings.append("no test case IDs were parsed from the Behave result")
    if not any(a["kind"] == "log" for a in artifacts):
        warnings.append("no log file was promoted")

    passed = not issues
    return {
        "status": "PASS" if passed else "FAIL",
        "trusted": passed,
        "blockingIssues": issues,
        "warnings": warnings,
        "checkedAt": utc_now(),
    }


def write_report(package_dir: Path, manifest: dict[str, Any]) -> Path:
    summary = manifest["summary"]
    gate = manifest["gate"]
    lines = [
        f"# Evidence Package {manifest['packageId']}",
        "",
        f"- Project: {manifest['project']}",
        f"- Module: {manifest['module']}",
        f"- Run ID: {manifest['source']['dashboardRunId']}",
        f"- Environment: {manifest.get('environment') or 'MISSING'}",
        f"- Build: {manifest.get('build') or 'MISSING'}",
        f"- Status: {manifest['status']}",
        f"- Gate: {gate['status']} ({'trusted' if gate['trusted'] else 'not trusted'})",
        "",
        "## Summary",
        "",
        f"- Scenarios: {summary['scenarioCount']}",
        f"- Executed: {summary['executed']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Errored: {summary['errored']}",
        f"- Skipped: {summary['skipped']}",
        f"- Pass rate: {summary['passRate']}%",
        "",
        "## Quality Deliverables",
        "",
        *(f"- {d}" for d in manifest["qualityDeliverables"]),
        "",
        "## Gate Findings",
        "",
    ]
    if gate["blockingIssues"]:
        lines.extend(f"- BLOCKER: {issue}" for issue in gate["blockingIssues"])
    else:
        lines.append("- No blocking issues.")
    if gate["warnings"]:
        lines.extend(f"- WARNING: {warning}" for warning in gate["warnings"])
    lines.extend([
        "",
        "## Artifacts",
        "",
        *(f"- {a['kind']}: `{a['path']}`" for a in manifest["artifacts"]),
        "",
    ])
    report = package_dir / "evidence-report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=int, required=True, help="Dashboard/Behave run id, e.g. 160")
    parser.add_argument("--module", default="website/login-registration", help="Evidence module path")
    parser.add_argument("--subproject", default="website")
    parser.add_argument("--evidence-type", default="automation-regression")
    parser.add_argument("--status", default="selected-for-review",
                        choices=["selected-for-review", "delivery-approved", "rejected", "draft"])
    parser.add_argument("--env", dest="environment", default=os.environ.get("ENV", "sit").upper())
    parser.add_argument("--build", default=os.environ.get("BUILD_ID", ""))
    parser.add_argument("--owner", default=os.environ.get("USERNAME") or getpass.getuser())
    parser.add_argument("--requirement", action="append", default=[])
    parser.add_argument("--defect", action="append", default=[])
    parser.add_argument("--known-risk", action="append", default=[])
    parser.add_argument("--deliverable", action="append", default=[],
                        help="Quality System deliverable id. Defaults cover evidence + automation phases.")
    parser.add_argument("--window-minutes", type=int, default=30,
                        help="Copy logs/screenshots modified around run JSON mtime.")
    parser.add_argument("--source-artifacts", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    westk_root = Path(__file__).resolve().parents[2]
    source_artifacts = (args.source_artifacts or westk_root / "02-automation" / "07-artifacts").resolve()
    evidence_root = (args.evidence_root or westk_root / "03-evidence").resolve()
    run_file = source_artifacts / f"run_{args.run_id}.json"
    if not run_file.exists():
        raise SystemExit(f"Run file not found: {run_file}")

    behave_json = load_json(run_file)
    if not isinstance(behave_json, list):
        raise SystemExit(f"Unsupported run JSON shape: {run_file}")

    promoted_at = utc_now()
    package_id = f"run-{args.run_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    module_path = Path(*[safe_slug(p) for p in args.module.split("/") if p.strip()])
    package_dir = evidence_root / "automation" / module_path / package_id
    if package_dir.exists() and not args.overwrite:
        raise SystemExit(f"Evidence package already exists: {package_dir}")

    raw_dir = package_dir / "raw"
    screenshots_dir = package_dir / "screenshots"
    logs_dir = package_dir / "logs"

    artifacts: list[dict[str, Any]] = []
    artifacts.append(copy_file(run_file, raw_dir / run_file.name, evidence_root, "run-json"))

    run_mtime = datetime.fromtimestamp(run_file.stat().st_mtime)
    for log in files_within_window(source_artifacts, run_mtime, args.window_minutes, {".log"}):
        artifacts.append(copy_file(log, logs_dir / log.name, evidence_root, "log"))

    screenshots_root = source_artifacts / "screenshots"
    for shot in files_within_window(screenshots_root, run_mtime, args.window_minutes, {".png", ".jpg", ".jpeg", ".webp"}):
        rel = shot.relative_to(screenshots_root)
        artifacts.append(copy_file(shot, screenshots_dir / rel, evidence_root, "screenshot"))

    summary = summarize_behave(behave_json)
    deliverables = args.deliverable or DEFAULT_DELIVERABLES
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "packageId": package_id,
        "project": "west-kowloon",
        "subproject": args.subproject,
        "module": args.module,
        "evidenceType": args.evidence_type,
        "status": args.status,
        "promotedAt": promoted_at,
        "promotedBy": args.owner,
        "environment": args.environment,
        "build": args.build,
        "source": {
            "dashboardRunId": args.run_id,
            "automationArtifacts": str(source_artifacts).replace("\\", "/"),
            "runFile": str(run_file).replace("\\", "/"),
        },
        "summary": summary,
        "qualityDeliverables": deliverables,
        "traceability": {
            "requirements": args.requirement,
            "testCaseIds": summary["testCaseIds"],
        },
        "defects": args.defect,
        "knownRisks": args.known_risk,
        "artifacts": artifacts,
    }
    manifest["gate"] = gate_for_manifest(manifest)

    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = write_report(package_dir, manifest)
    (package_dir / "gate-result.json").write_text(
        json.dumps(manifest["gate"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "packageDir": str(package_dir),
        "manifest": str(package_dir / "manifest.json"),
        "report": str(report),
        "gate": manifest["gate"],
    }, ensure_ascii=False, indent=2))
    return 0 if manifest["gate"]["trusted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
