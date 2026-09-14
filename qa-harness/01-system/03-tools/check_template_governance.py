"""check_template_governance.py — enforce template authority rules.

This checker protects the workspace rule that good historical artifacts must be
distilled into canonical templates and guards. Active instructions must not
tell agents to use a dated package document as the template source.

It complements:
  - check_workflow_coverage.py: every template is wired to workflow
  - check_requirement_review_interface.py: requirement consolidation has a
    stricter user-facing Q/U interface guard

Exit:
  0  pass
  1  violations found
  2  usage error / missing path
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import repo_root  # noqa: E402

REPO = repo_root()
WORKSPACE = REPO.parent
QA_SYSTEM = REPO / "01-system"
TEMPLATES_DIR = QA_SYSTEM / "02-templates"
WORKFLOW = QA_SYSTEM / "02-qa-workflow.md"
GATE = QA_SYSTEM / "03-tools" / "gate.py"
DEFAULT_OUT = REPO / "06-artifacts" / "template_governance_report.md"

ACTIVE_INSTRUCTION_ROOTS = [
    QA_SYSTEM,
    WORKSPACE / "AGENTS.md",
    WORKSPACE / "CODEX.md",
    WORKSPACE / "CLAUDE.md",
    WORKSPACE / "README.md",
    WORKSPACE / "west-kowloon" / "01-requirements" / "00-project-overview",
    WORKSPACE / "standard product" / "01-requirements" / "00-project-overview",
    WORKSPACE / "jockey club" / "01-requirements" / "00-project-overview",
]

DATE_RE = r"\b20\d{2}-\d{2}-\d{2}\b"
TEMPLATE_WORD_RE = r"(template|模板|样式|style reference|formatting template)"
ACTION_RE = r"(use|follow|walk|run|按|照|作为|当作|走|引用|套用)"
HISTORICAL_TEMPLATE_PATTERNS = [
    re.compile(ACTION_RE + r".{0,80}" + DATE_RE + r".{0,80}" + TEMPLATE_WORD_RE, re.I),
    re.compile(ACTION_RE + r".{0,80}" + TEMPLATE_WORD_RE + r".{0,80}" + DATE_RE, re.I),
    re.compile(DATE_RE + r".{0,80}" + ACTION_RE + r".{0,80}" + TEMPLATE_WORD_RE, re.I),
    re.compile(TEMPLATE_WORD_RE + r".{0,80}" + ACTION_RE + r".{0,80}" + DATE_RE, re.I),
]

NEGATION_RE = re.compile(
    r"(do not|don't|not\s+(?:a\s+)?template|not as a template|"
    r"not template sources?|不是模板|不能.*模板|不要.*模板|"
    r"唯一模板入口|template authority|only template authority|"
    r"business reference|impact reference|业务.*参考|影响.*参考)",
    re.I,
)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def iter_markdown_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() == ".md" else []
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def template_names() -> list[str]:
    if not TEMPLATES_DIR.is_dir():
        raise FileNotFoundError(f"templates dir missing: {TEMPLATES_DIR}")
    return sorted(
        p.stem for p in TEMPLATES_DIR.glob("*.md")
        if p.name not in {"README.md", "TODO.md"}
    )


def check_workflow_references() -> list[str]:
    if not WORKFLOW.exists():
        return [f"workflow missing: {display_path(WORKFLOW)}"]
    workflow_text = WORKFLOW.read_text(encoding="utf-8-sig")
    missing = [name for name in template_names() if name not in workflow_text]
    return [f"template not referenced from workflow: {name}" for name in missing]


def check_gate_wiring() -> list[str]:
    if not GATE.exists():
        return [f"gate missing: {display_path(GATE)}"]
    text = GATE.read_text(encoding="utf-8-sig")
    required = [
        "check_template_governance.py",
        "check_requirement_review_interface.py",
        "check_workflow_coverage.py",
    ]
    return [f"gate missing checker: {name}" for name in required if name not in text]


def scan_historical_template_references() -> list[str]:
    issues: list[str] = []
    for root in ACTIVE_INSTRUCTION_ROOTS:
        for path in iter_markdown_files(root):
            try:
                lines = path.read_text(encoding="utf-8-sig").splitlines()
            except Exception as exc:
                issues.append(f"{display_path(path)}: cannot read ({exc})")
                continue
            for lineno, line in enumerate(lines, start=1):
                if not any(pattern.search(line) for pattern in HISTORICAL_TEMPLATE_PATTERNS):
                    continue
                if NEGATION_RE.search(line):
                    continue
                issues.append(
                    f"{display_path(path)}:{lineno}: historical artifact appears to be used as template source: {line.strip()}"
                )
    return issues


def render_report(issues: list[str]) -> str:
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Template Governance Report",
        "",
        f"- Generated: {now}",
        "",
    ]
    if not issues:
        lines += [
            "## Result",
            "",
            "PASS — templates are workflow-wired, gate-wired, and no active instruction treats a dated historical artifact as a template source.",
            "",
        ]
        return "\n".join(lines)

    lines += ["## Result", "", f"FAIL — {len(issues)} issue(s) found.", ""]
    for issue in issues:
        lines.append(f"- {issue}")
    lines += [
        "",
        "## Rule",
        "",
        "- Canonical templates live under `qa-harness/01-system/02-templates`.",
        "- Historical artifacts can be business references or examples for extracting improvements, but must not be runtime template sources.",
        "- If a historical artifact has a good pattern, update the canonical template and add or update a guard.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []
    try:
        issues.extend(check_workflow_references())
    except Exception as exc:
        issues.append(str(exc))
    issues.extend(check_gate_wiring())
    issues.extend(scan_historical_template_references())

    report = render_report(issues)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"[template-governance] wrote {args.out}")
    if issues:
        print(f"[template-governance] FAIL: {len(issues)} issue(s)")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("[template-governance] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
