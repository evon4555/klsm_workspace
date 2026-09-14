"""check_signoff_gate.py — enforce the Step 3.5 sign-off gate.

Rule (see `01-system/02-qa-workflow.md` § 3.5 and `08-our-pipeline.md` § 1.5):

  A requirement-consolidation document gates `03-test-design/` for the
  same package and scope. Test cases for a scope MUST NOT exist while
  that scope's consolidation document is in any status other than
  "Signed Off".

What this script does:

  1. Walks every project's `01-requirements/` looking for date packages.
  2. In each package, finds:
       <package>/02-analysis/requirement-consolidation-<scope>.md
       <package>/03-test-design/**/test-cases-<scope>.{md,xlsx}
  3. Parses the consolidation doc's Status line.
  4. FAILs if test cases exist for a scope whose consolidation is not
     Signed Off.
  5. WARNs on test-case files in the same package whose scope does not
     match any consolidation (informational, doesn't FAIL).

Scope is the filename slug:

  requirement-consolidation-bank-card-priority-purchase.md
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  pairs with
  test-cases-bank-card-priority-purchase.{md,xlsx}

Exit:
  0  PASS (no gate violations)
  1  FAIL (one or more unsigned scopes with test cases)
  2  usage error / setup problem
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# Force UTF-8 stdout — see md_docx.py for why.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))
from _paths import repo_root  # noqa: E402

REPO = repo_root()
WORKSPACE = REPO.parent

CONSOLIDATION_PREFIX = "requirement-consolidation-"
TESTCASE_PREFIX = "test-cases-"
# Values that mean "this consolidation has been signed off" (case-insensitive,
# whitespace-trimmed). Both English and Chinese are accepted because docs
# may be authored in either language.
SIGNED_OFF_VALUES = {"signed off", "signedoff", "已确认", "已签字", "已签字确认", "确认"}

_STATUS_LABEL = r"(?:Status|状态|当前状态|签字状态|Final Status)"
# Plain line form:  Status: **xxx**  or  当前状态: xxx
STATUS_LINE_RE = re.compile(
    rf"^\s*{_STATUS_LABEL}\s*[:：]\s*\**\s*(?:[⚠✅⛔️]\s*)?(?P<value>[^*\n]+?)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Markdown-table-row form:  | 当前状态 | **⚠ 待确认** |
STATUS_TABLE_RE = re.compile(
    rf"^\s*\|\s*{_STATUS_LABEL}\s*\|\s*\**\s*(?:[⚠✅⛔️]\s*)?(?P<value>[^|*\n]+?)\s*\**\s*\|",
    re.IGNORECASE | re.MULTILINE,
)


def _is_signed_off(raw: str) -> bool:
    """Normalize a status value and decide whether it counts as Signed Off."""
    if not raw:
        return False
    norm = (
        raw.strip()
        .lower()
        .replace("　", " ")
        .replace(" ", "")
        .replace("*", "")
        .replace("✅", "")
        .replace("⚠", "")
        .replace("⛔", "")
        .replace("️", "")
    )
    # Accept exact signed-off values and explanatory status values that start
    # with a signed-off marker, e.g. "已确认 — Q-1..Q-10 已全部答复".
    return any(
        norm == v.lower().replace(" ", "") or norm.startswith(v.lower().replace(" ", ""))
        for v in SIGNED_OFF_VALUES
    )


def _strip_status_cell(value: str) -> str:
    return (
        value.strip()
        .strip("*")
        .strip()
        .lstrip("✅⚠⛔️ ")
        .strip()
    )


_REVISION_HEADERS = ("修订历史", "修改历史", "Revision History")


def _parse_revision_history_latest_status(text: str) -> str:
    """Return the last data row's last-column value from the 修订历史 /
    Revision History markdown table. The latest row's '完成后状态' column
    represents the doc's post-revision state — this is the most natural
    place for the Test Manager to record signoff.
    Returns empty string if section / table not found.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("##"):
            heading = stripped.lstrip("#").strip()
            if any(h in heading for h in _REVISION_HEADERS):
                # Found the section. Skip to first table row.
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("|"):
                    i += 1
                # Skip header row + separator
                i += 2
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


def find_packages(roots: Iterable[Path]) -> list[Path]:
    """Find date packages: any dir under a project's 01-requirements/
    that has an `02-analysis/` child with at least one consolidation md.
    """
    packages: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for cons in root.glob(
            "01-requirements/**/02-analysis/" + CONSOLIDATION_PREFIX + "*.md"
        ):
            packages.add(cons.parent.parent)
    return sorted(packages)


def parse_status(md_path: Path) -> str:
    """Return the consolidation doc's effective status value (lowercased).
    Considers TWO sources, with signed-off winning:
      1. Top metadata `Status:` field (line or table row form)
      2. Latest row's last-column value from `## 修订历史` table

    The user signs off naturally by adding a new revision-history row
    (per the documented rule). Many users won't also remember to update
    the top status field. So we treat either as authoritative and let
    signed-off win the merge.
    """
    text = md_path.read_text(encoding="utf-8", errors="replace")
    candidates: list[str] = []

    # Robust table parser for rows like:
    # | 当前状态 | ✅ **已确认** — Q-1..Q-10 已全部答复 |
    # | Final Status | Signed Off |
    labels_re = re.compile(rf"^{_STATUS_LABEL}$", re.IGNORECASE)
    for line in text.splitlines():
        row = line.strip()
        if not (row.startswith("|") and row.endswith("|")):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) >= 2 and labels_re.match(cells[0]):
            candidates.append(_strip_status_cell(cells[1]))
            break

    for pattern in (STATUS_LINE_RE, STATUS_TABLE_RE):
        m = pattern.search(text)
        if m:
            candidates.append(_strip_status_cell(m.group("value")))
            break
    rev_status = _parse_revision_history_latest_status(text)
    if rev_status:
        candidates.append(rev_status)

    for c in candidates:
        if _is_signed_off(c):
            return c.lower()
    return candidates[0].lower() if candidates else ""


def scope_from_consolidation(p: Path) -> str:
    return p.stem.removeprefix(CONSOLIDATION_PREFIX)


def scope_from_testcase(p: Path) -> str:
    return p.stem.removeprefix(TESTCASE_PREFIX)


def gather(package: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    """Return ({scope: consolidation_md}, {scope: [test_case_files]})."""
    cons: dict[str, Path] = {}
    for md in (package / "02-analysis").glob(CONSOLIDATION_PREFIX + "*.md"):
        cons[scope_from_consolidation(md)] = md

    tests: dict[str, list[Path]] = {}
    td = package / "03-test-design"
    if td.is_dir():
        for ext in ("md", "xlsx"):
            for f in td.rglob(TESTCASE_PREFIX + "*." + ext):
                # Skip audit-trail / version-history dirs (e.g. .iterations/v1/)
                rel = f.relative_to(td)
                if any(p.startswith(".") for p in rel.parts[:-1]):
                    continue
                scope = scope_from_testcase(f)
                tests.setdefault(scope, []).append(f)
    return cons, tests


def relpath(p: Path) -> str:
    try:
        return str(p.relative_to(WORKSPACE))
    except ValueError:
        return str(p)


def check_packages(packages: list[Path]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    for pkg in packages:
        cons, tests = gather(pkg)
        cons_scopes = set(cons.keys())

        # Per-scope enforcement
        for scope, cons_md in sorted(cons.items()):
            status = parse_status(cons_md)
            signed = _is_signed_off(status)
            tc_files = tests.get(scope, [])
            badge = "OK " if signed or not tc_files else "FAIL"
            label = "Signed Off" if signed else (status or "<no status line>")
            print(
                f"  [{badge}] {relpath(pkg)}  scope={scope!r}  "
                f"status='{label}'  tc-files={len(tc_files)}"
            )
            if not signed and tc_files:
                failures.append(
                    f"{relpath(pkg)} : scope={scope!r} consolidation status="
                    f"'{label}' but {len(tc_files)} test-case file(s) exist: "
                    + ", ".join(relpath(f) for f in tc_files)
                )

        # Orphan test case files: scope doesn't match any consolidation in
        # this package. Only warn — they might be legacy.
        for scope, tc_files in sorted(tests.items()):
            if scope not in cons_scopes:
                warnings.append(
                    f"{relpath(pkg)} : test-case scope={scope!r} has no "
                    f"matching consolidation doc ({len(tc_files)} file(s))."
                )

    return failures, warnings


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Enforce Step 3.5 sign-off gate (consolidation -> test design)."
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=WORKSPACE,
        help="Workspace root containing project dirs (default: parent of qa-harness).",
    )
    p.add_argument(
        "--project",
        action="append",
        default=[],
        help=(
            "Limit to specific project dir name(s) under workspace "
            "(e.g. west-kowloon). May be repeated. Default: all projects."
        ),
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    workspace: Path = args.workspace.resolve()

    if args.project:
        roots = [workspace / name for name in args.project]
    else:
        roots = [p for p in workspace.iterdir() if p.is_dir()]

    packages = find_packages(roots)
    print(f"[signoff-gate] scanning {len(packages)} package(s) with consolidation docs")
    if not packages:
        print("[signoff-gate] no consolidation docs found anywhere — nothing to enforce.")
        print("RESULT: PASS")
        return 0

    failures, warnings = check_packages(packages)

    print()
    if warnings:
        print(f"[signoff-gate] {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN  {w}")
        print()

    if failures:
        print(f"[signoff-gate] {len(failures)} failure(s):")
        for f in failures:
            print(f"  FAIL  {f}")
        print()
        print("RESULT: FAIL — unsigned consolidations have test cases in 03-test-design/.")
        print("Fix: either (a) Test Manager signs off the consolidation doc, or")
        print("           (b) remove the premature test-case files.")
        return 1

    print("RESULT: PASS — all consolidations are Signed Off or have no test cases yet.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(2)
