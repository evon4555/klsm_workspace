"""Enforce the test-case review sign-off gate before execution.

This validator checks the human/Test Manager review form under
04-test-case-review/ for each live test-case scope in 03-test-design/.

It is intentionally separate from check_signoff_gate.py:
- check_signoff_gate.py protects requirement consolidation -> test design.
- this script protects test-case review -> execution readiness.

Exit:
  0  PASS
  1  FAIL
  2  usage/setup error
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

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

TESTCASE_PREFIX = "test-cases-"
REVIEW_PREFIX = "test-case-review-"
PLACEHOLDER_FILES = {".gitkeep", "README.md"}


@dataclass
class ReviewData:
    final_status: str = ""
    signoff_date: str = ""
    signature: str = ""
    open_comments: str = ""
    open_comments_present: bool = False
    last_trail_status: str = ""
    docx_has_comments: bool = False
    review_md: Path | None = None
    review_docx: Path | None = None


@dataclass
class ScopeReviewResult:
    package: Path
    scope: str
    testcase_files: list[Path] = field(default_factory=list)
    review_md: Path | None = None
    state: str = "missing"  # signed | pending | missing | invalid
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def scope_from_testcase(path: Path) -> str:
    return path.stem.removeprefix(TESTCASE_PREFIX)


def is_audit_path(base: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(base)
    except ValueError:
        return False
    return any(part.startswith(".") or part.startswith("_") for part in rel.parts[:-1])


def find_packages(roots: Iterable[Path]) -> list[Path]:
    packages: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for td in root.glob("01-requirements/**/03-test-design"):
            if td.is_dir():
                packages.add(td.parent)
    return sorted(packages)


def package_from_testcase(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.name == "03-test-design":
            return parent.parent
    return None


def expand_xlsx_patterns(patterns: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if not matches and Path(pattern).is_file():
            matches = [pattern]
        for match in matches:
            p = Path(match).resolve()
            if p.suffix.lower() != ".xlsx" or p in seen:
                continue
            seen.add(p)
            files.append(p)
    return files


def gather_live_testcases(package: Path) -> dict[str, list[Path]]:
    td = package / "03-test-design"
    tests: dict[str, list[Path]] = {}
    if not td.is_dir():
        return tests
    for ext in ("md", "xlsx"):
        for path in td.rglob(TESTCASE_PREFIX + "*." + ext):
            if is_audit_path(td, path):
                continue
            tests.setdefault(scope_from_testcase(path), []).append(path)
    return {scope: sorted(files) for scope, files in sorted(tests.items())}


def has_execution_artifacts(package: Path) -> bool:
    execution = package / "05-execution"
    if not execution.is_dir():
        return False
    for path in execution.rglob("*"):
        if path.is_file() and path.name not in PLACEHOLDER_FILES:
            return True
    return False


def split_table_row(line: str) -> list[str]:
    return [normalize_cell(cell) for cell in line.strip().strip("|").split("|")]


def normalize_cell(value: str) -> str:
    value = value.strip()
    value = value.replace("`", "")
    value = re.sub(r"\s+", " ", value)
    return value


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells)


def parse_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = split_table_row(line)
            if not is_separator_row(cells):
                current.append(cells)
            continue
        if current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def is_placeholder(value: str) -> bool:
    raw = value.strip()
    low = raw.lower()
    return not raw or "<" in raw or ">" in raw or "yyyy" in low


def is_signed_off(value: str) -> bool:
    low = value.strip().lower().replace(" ", "")
    return low in {"signedoff", "approved"}


def is_noneish(value: str) -> bool:
    low = value.strip().lower()
    low = low.strip(". ")
    if low in {"", "-", "na", "n/a", "none", "nil", "no", "not applicable"}:
        return True
    if "no" in low and "comment" in low:
        return True
    return False


def is_open_status(value: str) -> bool:
    low = value.lower()
    return any(token in low for token in (
        "needs revision",
        "awaiting",
        "pending",
        "open blocker",
        "blocked",
        "revise",
    ))


def docx_has_word_comments(docx_path: Path) -> bool:
    if not docx_path.is_file():
        return False
    try:
        with ZipFile(docx_path) as zf:
            return any("comments" in name.lower() for name in zf.namelist())
    except Exception:
        return False


def parse_review(review_md: Path) -> ReviewData:
    text = review_md.read_text(encoding="utf-8", errors="replace")
    tables = parse_tables(text)
    data = ReviewData(review_md=review_md, review_docx=review_md.with_suffix(".docx"))

    fields: dict[str, str] = {}
    for table in tables:
        if not table:
            continue
        header = [norm_key(c) for c in table[0]]
        for row in table[1:]:
            if len(row) >= 2:
                fields.setdefault(norm_key(row[0]), row[1])
            if len(row) >= 3 and "additional test manager comments" in norm_key(" ".join(row[:2])):
                data.open_comments = row[-1]
                data.open_comments_present = True

        if "round version" in header and "status" in header:
            status_idx = header.index("status")
            for row in table[1:]:
                if len(row) > status_idx:
                    data.last_trail_status = row[status_idx]

    data.final_status = fields.get("final status", "")
    data.signoff_date = fields.get("sign off date", "")
    data.signature = fields.get("signature confirmation", "")
    if "open review comments" in fields:
        data.open_comments = fields["open review comments"]
        data.open_comments_present = True
    data.docx_has_comments = docx_has_word_comments(data.review_docx)
    return data


def find_review_md(package: Path, scope: str) -> Path | None:
    review = package / "04-test-case-review" / f"{REVIEW_PREFIX}{scope}.md"
    return review if review.is_file() else None


def evaluate_scope(package: Path, scope: str, testcase_files: list[Path],
                   strict: bool = False) -> ScopeReviewResult:
    result = ScopeReviewResult(
        package=package,
        scope=scope,
        testcase_files=testcase_files,
        review_md=find_review_md(package, scope),
    )
    execution_started = has_execution_artifacts(package)

    if result.review_md is None:
        result.state = "missing"
        msg = "missing matching 04-test-case-review/test-case-review-<scope>.md"
        if strict or execution_started:
            result.failures.append(msg)
        else:
            result.warnings.append(msg)
        return result

    data = parse_review(result.review_md)
    signed = is_signed_off(data.final_status) or is_signed_off(data.last_trail_status)

    if not signed:
        result.state = "pending"
        msg = f"review is not Signed Off (Final Status={data.final_status or '<missing>'})"
        if strict or execution_started:
            result.failures.append(msg)
        else:
            result.warnings.append(msg)
        return result

    result.state = "signed"
    if is_placeholder(data.signoff_date):
        result.failures.append("Signed Off review has no valid Sign-off Date")
    if is_placeholder(data.signature):
        result.failures.append("Signed Off review has no valid Signature / Confirmation")
    if not data.open_comments_present:
        result.failures.append("Signed Off review is missing Open Review Comments")
    elif not is_noneish(data.open_comments):
        result.failures.append(f"Signed Off review still has open comments: {data.open_comments}")
    if data.docx_has_comments:
        result.failures.append("paired DOCX still contains Word comments")
    if is_open_status(data.last_trail_status):
        result.failures.append(
            f"Review Trail last status is still open: {data.last_trail_status}"
        )
    if result.failures:
        result.state = "invalid"
    return result


def evaluate_packages(packages: Iterable[Path], strict: bool = False,
                      scope_filter: dict[Path, set[str]] | None = None
                      ) -> list[ScopeReviewResult]:
    results: list[ScopeReviewResult] = []
    for package in sorted({p.resolve() for p in packages}):
        tests = gather_live_testcases(package)
        if scope_filter is not None:
            wanted = scope_filter.get(package.resolve(), set())
            tests = {scope: files for scope, files in tests.items() if scope in wanted}
        for scope, files in tests.items():
            results.append(evaluate_scope(package, scope, files, strict=strict))
    return results


def build_scope_filter_from_xlsx(xlsx_files: list[Path]) -> tuple[list[Path], dict[Path, set[str]]]:
    packages: set[Path] = set()
    scope_filter: dict[Path, set[str]] = {}
    for xlsx in xlsx_files:
        package = package_from_testcase(xlsx)
        if package is None:
            continue
        package = package.resolve()
        packages.add(package)
        scope_filter.setdefault(package, set()).add(scope_from_testcase(xlsx))
    return sorted(packages), scope_filter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enforce Test Manager test-case review sign-off before execution."
    )
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--xlsx", nargs="+", default=[],
                        help="optional xlsx file(s) or glob(s) to scope the check")
    parser.add_argument("--strict", action="store_true",
                        help="fail missing/pending reviews even if execution has not started")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = args.workspace.resolve()

    scope_filter = None
    if args.xlsx:
        xlsx_files = expand_xlsx_patterns(args.xlsx)
        packages, scope_filter = build_scope_filter_from_xlsx(xlsx_files)
    else:
        roots = [workspace / name for name in args.project] if args.project else [
            p for p in workspace.iterdir() if p.is_dir()
        ]
        packages = find_packages(roots)

    print(f"[testcase-review-gate] scanning {len(packages)} package(s)")
    results = evaluate_packages(packages, strict=args.strict, scope_filter=scope_filter)
    if not results:
        print("[testcase-review-gate] no live test-case scopes found.")
        print("RESULT: PASS")
        return 0

    failures: list[str] = []
    warnings: list[str] = []
    for item in results:
        review = relpath(item.review_md) if item.review_md else "<missing>"
        print(
            f"  [{item.state.upper():7s}] {relpath(item.package)} "
            f"scope={item.scope!r} review={review}"
        )
        for msg in item.warnings:
            warnings.append(f"{relpath(item.package)} scope={item.scope!r}: {msg}")
        for msg in item.failures:
            failures.append(f"{relpath(item.package)} scope={item.scope!r}: {msg}")

    print()
    if warnings:
        print(f"[testcase-review-gate] {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  WARN  {warning}")
        print()

    if failures:
        print(f"[testcase-review-gate] {len(failures)} failure(s):")
        for failure in failures:
            print(f"  FAIL  {failure}")
        print()
        print("RESULT: FAIL - test-case review sign-off gate is not satisfied.")
        return 1

    print("RESULT: PASS - signed test-case reviews have no open comments.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(2)
