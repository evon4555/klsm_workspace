"""package_scanner.py — read west-kowloon (or any project) requirement packages
from the filesystem and report per-stage health for the dashboard's Package
Health page.

The scanner is filesystem-driven, with gate-aware checks for stages that have
formal readiness rules. For example, `03-test-design` respects the requirement
sign-off gate and `04-test-case-review` respects the Test Manager review
sign-off gate.

Usable two ways:

1. Imported by the dashboard backend:

    from package_scanner import scan_workspace, scan_package
    summary = scan_workspace(workspace_root, project="west-kowloon")
    detail  = scan_package(package_dir)

2. CLI for offline inspection / smoke:

    python 01-system/03-tools/package_scanner.py
    python 01-system/03-tools/package_scanner.py --project west-kowloon --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

# Force UTF-8 stdout so PowerShell on gbk doesn't choke on Chinese paths.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))
from _paths import repo_root  # noqa: E402
from check_testcase_review_gate import evaluate_packages  # noqa: E402

REPO = repo_root()
WORKSPACE = REPO.parent

# The 7 numbered stages every date package may have.
STAGE_DEFS = [
    {"id": "01-input",            "label": "Input"},
    {"id": "02-analysis",         "label": "Analysis"},
    {"id": "03-test-design",      "label": "Test Design"},
    {"id": "04-test-case-review", "label": "Case Review"},
    {"id": "05-execution",        "label": "Execution"},
    {"id": "06-execution-review", "label": "Execution Review"},
    {"id": "07-release-feedback", "label": "Release Feedback"},
]

CONSOLIDATION_PREFIX = "requirement-consolidation-"
TESTCASE_PREFIX = "test-cases-"

# Package paths look like:
# <workspace>/<project>/01-requirements/02-subprojects/<subproject>/02-modules/<module>/<yyyy-mm-dd>[-suffix]
PACKAGE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(-.*)?$")

# Status parsing — accept both plain-line form and markdown-table-row form,
# in English or Chinese labels. Mirror of check_signoff_gate.py — kept in
# sync intentionally so both surfaces (dashboard + CLI gate) agree.
SIGNED_OFF_VALUES = {"signed off", "signedoff", "已确认", "已签字", "已签字确认", "确认"}
_STATUS_LABEL = r"(?:Status|状态|当前状态|签字状态)"
STATUS_LINE_RE = re.compile(
    rf"^\s*{_STATUS_LABEL}\s*[:：]\s*\**\s*(?:[⚠✅⛔️]\s*)?(?P<value>[^*\n]+?)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
STATUS_TABLE_RE = re.compile(
    rf"^\s*\|\s*{_STATUS_LABEL}\s*\|\s*\**\s*(?:[⚠✅⛔️]\s*)?(?P<value>[^|*\n]+?)\s*\**\s*\|",
    re.IGNORECASE | re.MULTILINE,
)


def _is_signed_off(raw: str) -> bool:
    if not raw:
        return False
    norm = raw.strip().lower().replace("　", " ").replace(" ", "")
    return any(norm == v.lower().replace(" ", "") for v in SIGNED_OFF_VALUES)


_REVISION_HEADERS = ("修订历史", "修改历史", "Revision History")


def _parse_revision_history_latest_status(text: str) -> str:
    """See check_signoff_gate.py for the rationale. Kept in sync."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("##"):
            heading = stripped.lstrip("#").strip()
            if any(h in heading for h in _REVISION_HEADERS):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("|"):
                    i += 1
                i += 2  # skip header + separator
                last_cells = None
                while i < len(lines):
                    row = lines[i].strip()
                    if not (row.startswith("|") and row.endswith("|")):
                        break
                    cells = [c.strip().strip("*").strip() for c in row.strip("|").split("|")]
                    if any(cells):
                        last_cells = cells
                    i += 1
                return last_cells[-1] if last_cells else ""
        i += 1
    return ""


@dataclass
class StageResult:
    id: str
    label: str
    status: str  # "pass" | "partial" | "empty" | "blocked"
    summary: str
    files: list[str] = field(default_factory=list)
    # Optional honest disclosure that the signoff gate doesn't fully cover
    # this stage — e.g. legacy filenames the gate can't pair. Frontend shows
    # a small warning icon when present. Status stays accurate (pass /
    # partial / blocked); this is an at-a-glance "but..." annotation.
    gate_note: str | None = None


@dataclass
class PackageResult:
    id: str               # relative path id used by the API
    project: str
    subproject: str
    module: str
    date_slug: str
    title: str            # short human label
    stages: list[StageResult] = field(default_factory=list)
    verdict: str = "in-progress"  # "not-started" | "in-progress" | "complete"
    next_action: str = ""
    qa_readiness: str = "in-progress"  # "not-started" | "in-progress" | "blocked" | "ready"
    qa_next_action: str = ""
    release_feedback_status: str = "empty"
    release_feedback_summary: str = ""


def _list_files(dir_path: Path, recursive: bool = True) -> list[Path]:
    if not dir_path.is_dir():
        return []
    it = dir_path.rglob("*") if recursive else dir_path.iterdir()
    files: list[Path] = []
    for p in it:
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(dir_path)
            if any(part.startswith(".") for part in rel.parts[:-1]):
                continue
        except ValueError:
            pass
        if p.name.startswith("~$") or p.name.startswith("._"):
            continue
        files.append(p)
    return files


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(WORKSPACE)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def find_packages(project_root: Path) -> list[Path]:
    """A package is any folder whose name matches the date pattern AND that
    sits at depth 6 below 01-requirements (subproject/module/date)."""
    base = project_root / "01-requirements"
    if not base.exists():
        return []
    packages: list[Path] = []
    for module_dir in base.glob("02-subprojects/*/02-modules/*"):
        if not module_dir.is_dir():
            continue
        for child in module_dir.iterdir():
            if child.is_dir() and PACKAGE_DATE_RE.match(child.name):
                packages.append(child)
    return sorted(packages)


def _parse_consolidation_status(md: Path) -> str:
    """Returns the effective status. Signed-off wins between top metadata
    and the 修订历史 table's latest row. See check_signoff_gate.parse_status."""
    text = md.read_text(encoding="utf-8", errors="replace")
    candidates: list[str] = []
    for pattern in (STATUS_LINE_RE, STATUS_TABLE_RE):
        m = pattern.search(text)
        if m:
            candidates.append(m.group("value").strip())
            break
    rev_status = _parse_revision_history_latest_status(text)
    if rev_status:
        candidates.append(rev_status)
    for c in candidates:
        if _is_signed_off(c):
            return c
    return candidates[0] if candidates else ""


def _check_input(pkg: Path) -> StageResult:
    sd = pkg / "01-input"
    if not sd.exists():
        return StageResult("01-input", "Input", "empty", "no 01-input/ folder")
    files = _list_files(sd)
    if not files:
        return StageResult("01-input", "Input", "empty", "01-input/ is empty")
    has_index = (sd / "input-index.md").exists()
    summary = f"{len(files)} file(s)"
    if not has_index:
        summary += " · no input-index.md"
        status = "partial"
    else:
        status = "pass"
    return StageResult(
        "01-input", "Input", status, summary,
        files=[_rel(f) for f in files[:10]],
    )


def _check_analysis(pkg: Path) -> StageResult:
    sd = pkg / "02-analysis"
    if not sd.exists():
        return StageResult("02-analysis", "Analysis", "empty", "no 02-analysis/ folder")
    cons_files = sorted(sd.glob(CONSOLIDATION_PREFIX + "*.md"))
    if not cons_files:
        other = _list_files(sd, recursive=False)
        if not other:
            return StageResult("02-analysis", "Analysis", "empty", "no consolidation doc")
        return StageResult(
            "02-analysis", "Analysis", "partial",
            f"{len(other)} file(s), no consolidation doc",
            files=[_rel(f) for f in other],
        )
    statuses = [(c.name, _parse_consolidation_status(c)) for c in cons_files]
    signed = [(n, s) for n, s in statuses if _is_signed_off(s)]
    pending = [(n, s) for n, s in statuses if not _is_signed_off(s)]
    if pending and not signed:
        status = "partial"
        summary = f"{len(pending)} consolidation doc(s) awaiting sign-off"
    elif pending and signed:
        status = "partial"
        summary = f"{len(signed)} signed off, {len(pending)} awaiting"
    else:
        status = "pass"
        summary = f"{len(signed)} signed off"
    return StageResult(
        "02-analysis", "Analysis", status, summary,
        files=[_rel(c) for c in cons_files],
    )


def _check_test_design(pkg: Path) -> StageResult:
    sd = pkg / "03-test-design"
    # Consolidation gate: if any consolidation is unsigned and test cases for
    # that scope exist, this is "blocked" rather than "pass".
    cons_files = sorted((pkg / "02-analysis").glob(CONSOLIDATION_PREFIX + "*.md"))
    cons_scopes: set[str] = set()
    unsigned_scopes: set[str] = set()
    for c in cons_files:
        scope = c.stem.removeprefix(CONSOLIDATION_PREFIX)
        cons_scopes.add(scope)
        if not _is_signed_off(_parse_consolidation_status(c)):
            unsigned_scopes.add(scope)

    # Helper: dot-prefixed directories (`.iterations/`, `.archive/`, etc.) are
    # audit-trail / version-history folders. They contain real test-case files
    # for previous rounds, but those should NOT be counted as live test
    # artifacts by the gate. Skip any path with a dot-prefixed component.
    def _is_audit_path(f: Path) -> bool:
        try:
            rel = f.relative_to(sd)
        except ValueError:
            return False
        return any(p.startswith(".") for p in rel.parts[:-1])

    # Detect files the gate's scope-matching can't pair (legacy + orphan).
    # Only meaningful when this package has at least one consolidation —
    # otherwise the gate isn't trying to enforce anything here.
    legacy_files: list[Path] = []
    orphan_files: list[Path] = []
    if sd.exists() and cons_files:
        for ext in ("md", "xlsx"):
            for f in sd.rglob(f"*test-cases*.{ext}"):
                if _is_audit_path(f):
                    continue
                if f.name.startswith(TESTCASE_PREFIX):
                    scope = f.stem.removeprefix(TESTCASE_PREFIX)
                    if scope not in cons_scopes:
                        orphan_files.append(f)
                else:
                    legacy_files.append(f)

    def _gate_note() -> str | None:
        n = len(legacy_files) + len(orphan_files)
        if n == 0:
            return None
        parts = []
        if legacy_files:
            parts.append(f"legacy={len(legacy_files)}")
        if orphan_files:
            parts.append(f"orphan={len(orphan_files)}")
        return (
            f"闸门未覆盖 {n} 个文件：" + " / ".join(parts)
            + "（命名不匹配 test-cases-<consolidation-scope>.{md,xlsx} 约定）"
        )

    if not sd.exists():
        if unsigned_scopes:
            return StageResult(
                "03-test-design", "Test Design", "blocked",
                f"{len(unsigned_scopes)} scope(s) blocked by unsigned consolidation",
            )
        return StageResult("03-test-design", "Test Design", "empty", "no 03-test-design/ folder")

    tc_files = []
    for ext in ("md", "xlsx"):
        tc_files.extend(
            f for f in sd.rglob(TESTCASE_PREFIX + "*." + ext)
            if not _is_audit_path(f)
        )
    tc_files = sorted(tc_files)

    # Detect gate violations: tc file exists for an unsigned scope.
    violating: list[Path] = []
    for tc in tc_files:
        scope = tc.stem.removeprefix(TESTCASE_PREFIX)
        if scope in unsigned_scopes:
            violating.append(tc)

    if violating:
        return StageResult(
            "03-test-design", "Test Design", "blocked",
            f"{len(violating)} test-case file(s) violate sign-off gate",
            files=[_rel(f) for f in violating],
            gate_note=_gate_note(),
        )

    if not tc_files:
        if unsigned_scopes:
            return StageResult(
                "03-test-design", "Test Design", "blocked",
                "consolidation not Signed Off (gate)",
                gate_note=_gate_note(),
            )
        return StageResult(
            "03-test-design", "Test Design", "empty", "no test cases yet",
            gate_note=_gate_note(),
        )

    return StageResult(
        "03-test-design", "Test Design", "pass",
        f"{len(tc_files)} test-case file(s)",
        files=[_rel(f) for f in tc_files[:10]],
        gate_note=_gate_note(),
    )


def _check_simple_folder(pkg: Path, stage_id: str, label: str) -> StageResult:
    sd = pkg / stage_id
    if not sd.exists():
        return StageResult(stage_id, label, "empty", f"no {stage_id}/ folder")
    files = _list_files(sd)
    # Filter out placeholder files that shouldn't count as real content
    real = [f for f in files if f.name not in (".gitkeep", "README.md")]
    if not real:
        if files:
            return StageResult(stage_id, label, "empty", "only placeholders / README")
        return StageResult(stage_id, label, "empty", f"{stage_id}/ is empty")
    return StageResult(
        stage_id, label, "pass", f"{len(real)} file(s)",
        files=[_rel(f) for f in real[:10]],
    )


def _check_execution(pkg: Path) -> StageResult:
    sd = pkg / "05-execution"
    if not sd.exists():
        return StageResult("05-execution", "Execution", "empty", "no 05-execution/ folder")
    files = _list_files(sd)
    real = [f for f in files if f.name not in (".gitkeep", "README.md")]
    if not real:
        if files:
            return StageResult("05-execution", "Execution", "empty", "only placeholders / README")
        return StageResult("05-execution", "Execution", "empty", "05-execution/ is empty")

    evidence_keywords = ("execution", "evidence", "result", "run", "report")
    planning_keywords = ("automation-assessment", "automation-plan", "planning", "plan")
    def stage_rel(f: Path) -> str:
        try:
            return str(f.relative_to(sd)).replace("\\", "/").lower()
        except ValueError:
            return f.name.lower()

    evidence_files = [
        f for f in real
        if any(k in stage_rel(f) for k in evidence_keywords)
    ]
    planning_files = [
        f for f in real
        if any(k in stage_rel(f) for k in planning_keywords)
    ]
    if evidence_files:
        shown = evidence_files + [f for f in real if f not in evidence_files]
        return StageResult(
            "05-execution",
            "Execution",
            "pass",
            f"{len(evidence_files)} execution evidence/report file(s)",
            files=[_rel(f) for f in shown[:10]],
        )
    if planning_files:
        shown = planning_files + [f for f in real if f not in planning_files]
        return StageResult(
            "05-execution",
            "Execution",
            "partial",
            f"{len(planning_files)} planning/automation assessment file(s); no execution evidence yet",
            files=[_rel(f) for f in shown[:10]],
        )
    return StageResult(
        "05-execution",
        "Execution",
        "partial",
        f"{len(real)} file(s); execution evidence not identified",
        files=[_rel(f) for f in real[:10]],
    )


def _check_execution_review(pkg: Path) -> StageResult:
    sd = pkg / "06-execution-review"
    if not sd.exists():
        return StageResult("06-execution-review", "Execution Review", "empty", "no 06-execution-review/ folder")

    files = _list_files(sd)
    real = [f for f in files if f.name not in (".gitkeep", "README.md")]
    if not real:
        if files:
            return StageResult("06-execution-review", "Execution Review", "empty", "only placeholders / README")
        return StageResult("06-execution-review", "Execution Review", "empty", "06-execution-review/ is empty")

    review_keywords = (
        "execution-review",
        "readiness",
        "ready-for-release",
        "sign-off",
        "signoff",
        "test-report",
        "test-summary",
        "summary",
        "accepted-risk",
        "risk",
    )

    def stage_rel(f: Path) -> str:
        try:
            return str(f.relative_to(sd)).replace("\\", "/").lower()
        except ValueError:
            return f.name.lower()

    review_files = [
        f for f in real
        if any(k in stage_rel(f) for k in review_keywords)
    ]
    if review_files:
        return StageResult(
            "06-execution-review",
            "Execution Review",
            "pass",
            f"{len(review_files)} readiness review/report file(s)",
            files=[_rel(f) for f in real[:10]],
        )

    return StageResult(
        "06-execution-review",
        "Execution Review",
        "partial",
        f"{len(real)} file(s); readiness review not identified",
        files=[_rel(f) for f in real[:10]],
    )


def _check_release_feedback(pkg: Path) -> StageResult:
    sd = pkg / "07-release-feedback"
    if not sd.exists():
        return StageResult("07-release-feedback", "Release Feedback", "empty", "no 07-release-feedback/ folder")

    files = _list_files(sd)
    real = [f for f in files if f.name not in (".gitkeep", "README.md")]
    if not real:
        if files:
            return StageResult("07-release-feedback", "Release Feedback", "empty", "only placeholders / README")
        return StageResult("07-release-feedback", "Release Feedback", "empty", "07-release-feedback/ is empty")

    feedback_keywords = (
        "release-feedback",
        "post-release",
        "production",
        "prod",
        "incident",
        "hotfix",
        "rollback",
        "monitoring",
        "retrospective",
        "feedback",
    )

    def stage_rel(f: Path) -> str:
        try:
            return str(f.relative_to(sd)).replace("\\", "/").lower()
        except ValueError:
            return f.name.lower()

    feedback_files = [
        f for f in real
        if any(k in stage_rel(f) for k in feedback_keywords)
    ]
    if feedback_files:
        return StageResult(
            "07-release-feedback",
            "Release Feedback",
            "pass",
            f"{len(feedback_files)} release feedback file(s)",
            files=[_rel(f) for f in real[:10]],
        )

    return StageResult(
        "07-release-feedback",
        "Release Feedback",
        "partial",
        f"{len(real)} file(s); release feedback not identified",
        files=[_rel(f) for f in real[:10]],
    )


def _check_case_review(pkg: Path) -> StageResult:
    results = evaluate_packages([pkg], strict=False)
    if not results:
        return _check_simple_folder(pkg, "04-test-case-review", "Case Review")

    signed = [r for r in results if r.state == "signed"]
    pending = [r for r in results if r.state in ("pending", "missing")]
    invalid = [r for r in results if r.state == "invalid" or r.failures]

    files = [_rel(r.review_md) for r in results if r.review_md is not None]
    notes = []
    for r in results:
        for msg in r.warnings + r.failures:
            notes.append(f"{r.scope}: {msg}")

    if invalid:
        return StageResult(
            "04-test-case-review",
            "Case Review",
            "blocked",
            f"{len(invalid)} review scope(s) violate sign-off gate",
            files=files[:10],
            gate_note="; ".join(notes[:3]) if notes else None,
        )

    if pending:
        return StageResult(
            "04-test-case-review",
            "Case Review",
            "partial",
            f"{len(signed)} signed, {len(pending)} awaiting review/sign-off",
            files=files[:10],
            gate_note="; ".join(notes[:3]) if notes else None,
        )

    return StageResult(
        "04-test-case-review",
        "Case Review",
        "pass",
        f"{len(signed)} signed review scope(s); no open comments",
        files=files[:10],
    )


STAGE_CHECKS = {
    "01-input":            _check_input,
    "02-analysis":         _check_analysis,
    "03-test-design":      _check_test_design,
    "04-test-case-review": _check_case_review,
    "05-execution":        _check_execution,
    "06-execution-review": _check_execution_review,
    "07-release-feedback": _check_release_feedback,
}


def scan_package(pkg_dir: Path) -> PackageResult:
    """Build the full PackageResult for one date package."""
    pkg_dir = pkg_dir.resolve()
    parts = pkg_dir.parts
    # Walk up to derive project / subproject / module / date.
    try:
        idx = parts.index("01-requirements")
    except ValueError:
        idx = max(0, len(parts) - 6)
    project = parts[idx - 1] if idx - 1 >= 0 else "?"
    subproject_idx = parts.index("02-subprojects", idx) if "02-subprojects" in parts[idx:] else None
    subproject = parts[subproject_idx + 1] if subproject_idx is not None else "?"
    module_idx = parts.index("02-modules", subproject_idx or idx) if "02-modules" in parts else None
    module = parts[module_idx + 1] if module_idx is not None else "?"
    date_slug = pkg_dir.name

    stages: list[StageResult] = []
    for stage_def in STAGE_DEFS:
        sid = stage_def["id"]
        stages.append(STAGE_CHECKS[sid](pkg_dir))

    # QA readiness is decided by stages 01-06. Stage 07 is post-release
    # feedback and must not keep an otherwise ready package in progress.
    qa_stages = [s for s in stages if s.id != "07-release-feedback"]
    qa_statuses = [s.status for s in qa_stages]
    if all(s == "pass" for s in qa_statuses):
        qa_readiness = "ready"
        verdict = "complete"
    elif any(s == "blocked" for s in qa_statuses):
        qa_readiness = "blocked"
        verdict = "in-progress"
    elif all(s == "empty" for s in qa_statuses):
        qa_readiness = "not-started"
        verdict = "not-started"
    else:
        qa_readiness = "in-progress"
        verdict = "in-progress"

    qa_next_action = ""
    for s in qa_stages:
        if s.status in ("blocked", "partial", "empty"):
            qa_next_action = f"{s.id}: {s.summary}"
            break

    release_stage = next((s for s in stages if s.id == "07-release-feedback"), None)
    release_feedback_status = release_stage.status if release_stage else "empty"
    release_feedback_summary = release_stage.summary if release_stage else ""
    next_action = qa_next_action or "QA readiness complete; release feedback is tracked separately."

    title = f"{module} / {date_slug}"

    return PackageResult(
        id=_rel(pkg_dir),
        project=project,
        subproject=subproject,
        module=module,
        date_slug=date_slug,
        title=title,
        stages=stages,
        verdict=verdict,
        next_action=next_action,
        qa_readiness=qa_readiness,
        qa_next_action=qa_next_action,
        release_feedback_status=release_feedback_status,
        release_feedback_summary=release_feedback_summary,
    )


def scan_workspace(workspace_root: Path, project: str = "west-kowloon") -> list[PackageResult]:
    """Scan one project under the workspace and return all packages."""
    project_root = workspace_root / project
    if not project_root.exists():
        return []
    return [scan_package(p) for p in find_packages(project_root)]


def to_jsonable(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, default=WORKSPACE)
    p.add_argument("--project", default="west-kowloon")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = p.parse_args()

    results = scan_workspace(args.workspace.resolve(), args.project)
    if args.json:
        print(json.dumps([to_jsonable(r) for r in results], ensure_ascii=False, indent=2))
        return 0

    print(f"[package-scanner] project={args.project!r}  packages={len(results)}")
    for r in results:
        print(f"\n=== {r.title}  ({r.verdict})")
        print(f"    {r.id}")
        for s in r.stages:
            mark = {"pass": "OK ", "partial": "..", "blocked": "!!", "empty": "  "}[s.status]
            print(f"    [{mark}] {s.id:24s} {s.status:10s} {s.summary}")
        if r.next_action:
            print(f"    next: {r.next_action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
