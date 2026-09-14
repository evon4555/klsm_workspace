"""check_requirement_review_interface.py — enforce the human-facing
requirement consolidation working interface.

This guard exists because memory notes and prose rules were not enough to
prevent old formal/internal templates from leaking into user-facing
requirement reviews. New requirement-consolidation working docs must use the
decision-only Chinese Q/U interface.

Default scope:
  - requirement-consolidation-*.md under dated packages on/after 2026-07-15
  - the shared requirement-consolidation template, which is the only template
    authority for this working interface
  - the consolidate-requirement skill and workflow docs that drive execution

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
DEFAULT_SINCE = dt.date(2026, 7, 15)
DEFAULT_OUT = REPO / "06-artifacts" / "requirement_review_interface_guard.md"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_DOC_MARKERS = [
    "## 1. 有没有问题？",
    "## 2. 问题分类",
    "## 3. 测试范围",
    "## 4. 差异项",
    "## 5. 来源",
    "## 6. 问题清单",
    "## 7. 下一步",
    "| # | 决策点 | 选项 | 默认 | 答复 |",
    "| # | 模糊点 | AI 暂定假设 | 确认 / 修正 |",
]

TEMPLATE_AUTHORITY_MARKER = "本文件是需求整理工作界面的唯一模板入口"

FORBIDDEN_DOC_PATTERNS = [
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s*\[SECTION\]\b"), "visible [SECTION] heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bIntegrated Breakdown\b"), "Integrated Breakdown heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bHand-Off Statement\b"), "Hand-Off Statement heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bSource Inventory\b"), "Source Inventory heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bTest Scope This Round\b"), "Test Scope This Round heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bUnclear Items\b"), "Unclear Items heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bItems Requiring User Confirmation\b"), "Items Requiring User Confirmation heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bRequirement Analysis Detail\b"), "Requirement Analysis Detail heading"),
    (re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\bReview Findings\b"), "Review Findings heading"),
    (re.compile(r"\bOpen Review Comments\b"), "Open Review Comments field"),
    (re.compile(r"\bResolution / Status\b"), "Resolution / Status field"),
]

FORBIDDEN_INSTRUCTION_PATTERNS = [
    (re.compile(r"legacy consolidation section order may be used", re.I), "legacy consolidation section order"),
    (re.compile(r"formal template wins", re.I), "formal template wins instruction"),
    (re.compile(r"must use the v2\.1 `Requirement Review Template`", re.I), "v2.1 formal template mandate"),
    (re.compile(r"For West Kowloon formal requirement review", re.I), "West Kowloon formal review mandate"),
    (re.compile(r"For West Kowloon packages, the human-facing requirement review/sign-off", re.I), "West Kowloon formal package mandate"),
    (re.compile(r"§ Integrated Breakdown", re.I), "legacy Integrated Breakdown section list"),
    (re.compile(r"§ Hand-Off Statement", re.I), "legacy Hand-Off Statement section list"),
]

INSTRUCTION_FILES = [
    REPO / "01-system" / "01-skills" / "consolidate-requirement" / "SKILL.md",
    REPO / "01-system" / "02-qa-workflow.md",
    REPO / "01-system" / "08-our-pipeline.md",
]

TEMPLATE_FILE = REPO / "01-system" / "02-templates" / "requirement-consolidation-template.md"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def date_from_path(path: Path) -> dt.date | None:
    for part in path.parts:
        if not DATE_RE.match(part):
            continue
        try:
            return dt.date.fromisoformat(part)
        except ValueError:
            continue
    return None


def collect_requirement_docs(workspace: Path, since: dt.date, include_legacy: bool) -> list[Path]:
    docs: list[Path] = []
    for project in sorted(p for p in workspace.iterdir() if p.is_dir()):
        req = project / "01-requirements"
        if not req.is_dir():
            continue
        for path in sorted(req.rglob("requirement-consolidation-*.md")):
            if "02-analysis" not in path.parts:
                continue
            package_date = date_from_path(path)
            if package_date is None:
                continue
            if include_legacy or package_date >= since:
                docs.append(path)
    return docs


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def validate_decision_doc(path: Path) -> list[str]:
    text = read_text(path)
    issues: list[str] = []

    for pattern, label in FORBIDDEN_DOC_PATTERNS:
        if pattern.search(text):
            issues.append(f"forbidden {label}")

    for marker in REQUIRED_DOC_MARKERS:
        if marker not in text:
            issues.append(f"missing required marker: {marker}")

    return issues


def validate_template(path: Path) -> list[str]:
    text = read_text(path)
    issues: list[str] = []
    for pattern, label in FORBIDDEN_DOC_PATTERNS[:9]:
        if pattern.search(text):
            issues.append(f"template contains forbidden positive heading: {label}")
    for marker in REQUIRED_DOC_MARKERS:
        if marker not in text:
            issues.append(f"template missing required marker: {marker}")
    if TEMPLATE_AUTHORITY_MARKER not in text:
        issues.append("template missing explicit template-authority marker")
    if "用户-facing 的需求整理文档不得出现 `[SECTION]` 标记" not in text:
        issues.append("template missing explicit [SECTION] ban")
    return issues


def validate_instruction(path: Path) -> list[str]:
    text = read_text(path)
    issues: list[str] = []
    for pattern, label in FORBIDDEN_INSTRUCTION_PATTERNS:
        if pattern.search(text):
            issues.append(f"instruction still contains {label}")
    return issues


def render_report(results: list[tuple[Path, list[str]]], scanned: int) -> str:
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Requirement Review Interface Guard",
        "",
        f"- Generated: {now}",
        f"- Scanned files: {scanned}",
        "",
    ]

    failures = [(path, issues) for path, issues in results if issues]
    if not failures:
        lines += [
            "## Result",
            "",
            "PASS — no legacy formal/internal requirement-review interface leaked into the checked scope.",
            "",
        ]
        return "\n".join(lines)

    lines += ["## Result", "", f"FAIL — {len(failures)} file(s) need cleanup.", ""]
    for path, issues in failures:
        lines.append(f"### `{display_path(path)}`")
        lines.append("")
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")

    lines += [
        "## Required Working Interface",
        "",
        "- Chinese decision-only structure: conclusion, issue classification, test scope, differences, sources, Q/U tables, next step.",
        "- Test Manager fills only `答复` and `确认 / 修正` columns.",
        "- No `[SECTION]`, `Integrated Breakdown`, `Hand-Off Statement`, `Review Findings`, `Open Review Comments`, or `Resolution / Status` in user-facing requirement consolidation docs.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--since", type=dt.date.fromisoformat, default=DEFAULT_SINCE)
    parser.add_argument("--include-legacy", action="store_true",
                        help="also scan dated packages before --since")
    parser.add_argument("--path", type=Path, action="append", default=[],
                        help="extra markdown path to validate as a decision-only consolidation doc")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.workspace.is_dir():
        print(f"ERROR: workspace not found: {args.workspace}", file=sys.stderr)
        return 2

    files: list[tuple[Path, str]] = []
    if not TEMPLATE_FILE.exists():
        print(f"ERROR: template missing: {TEMPLATE_FILE}", file=sys.stderr)
        return 2
    files.append((TEMPLATE_FILE, "template"))

    for path in INSTRUCTION_FILES:
        if not path.exists():
            print(f"ERROR: instruction file missing: {path}", file=sys.stderr)
            return 2
        files.append((path, "instruction"))

    for path in collect_requirement_docs(args.workspace, args.since, args.include_legacy):
        files.append((path, "doc"))

    for path in args.path:
        if not path.exists():
            print(f"ERROR: path not found: {path}", file=sys.stderr)
            return 2
        files.append((path, "doc"))

    seen: set[Path] = set()
    unique_files: list[tuple[Path, str]] = []
    for path, kind in files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_files.append((resolved, kind))

    results: list[tuple[Path, list[str]]] = []
    for path, kind in unique_files:
        if kind == "template":
            issues = validate_template(path)
        elif kind == "instruction":
            issues = validate_instruction(path)
        else:
            issues = validate_decision_doc(path)
        results.append((path, issues))

    report = render_report(results, len(unique_files))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")

    failures = [(path, issues) for path, issues in results if issues]
    print(f"[requirement-review-interface] wrote {args.out}")
    if failures:
        print(f"[requirement-review-interface] FAIL: {len(failures)} file(s)")
        for path, issues in failures:
            print(f"  {display_path(path)}")
            for issue in issues:
                print(f"    - {issue}")
        return 1

    print(f"[requirement-review-interface] PASS: {len(unique_files)} files checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
