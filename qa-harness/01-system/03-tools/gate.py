"""gate.py — the single harness gate that chains the harness validators.

Runs in order, with last-fail-wins exit code:
  1. validate_testcase_xlsx.py     (schema, IDs, required fields, yellow-row rule)
  2. check_traceability.py          (xlsx <-> .feature <-> dashboard.db)
  3. validate_evidence.py           (Pass/Fail rows have actual result, comments, screenshot)
  4. check_template_governance.py   (templates are workflow/gate wired and not historical artifacts)
  5. check_requirement_review_interface.py
                                      (Step 3.5 uses decision-only Q/U interface)
  6. check_workflow_coverage.py     (every skill + template is wired to a step in 02-qa-workflow.md)
  7. check_signoff_gate.py          (Step 3.5 sign-off respected: no test cases for unsigned consolidations)
  8. check_testcase_review_gate.py  (Test Manager test-case review signed before execution readiness)
  9. check_testcase_audit_trail.py  (case add/modify/remove audit visible in xlsx + review DOCX)

writeback_results.py is intentionally NOT in the gate — it is a writer, not a
validator, and should be run manually (or from CI's post-run hook) with
--dry-run first.

The gate is the contract that says "this QA harness output is consistent
enough to merge / release". It's designed to be wired into CI later
(GitHub Actions, Jenkins, etc.) — see Phase 4 of the merge plan.

Usage:
  python gate.py [--xlsx GLOB ...] [--features DIR] [--db PATH]
                 [--case-prefix PREFIX ...]

Default scope (when no --xlsx given): all test-cases-*.xlsx under
<project>/01-requirements/ — i.e. every project's xlsx in this workspace. Paths
are derived from gate.py's own location so this works cross-machine /
cross-OS without editing.

Exit:  0 if every validator PASS,  1 if any FAIL,  2 on usage/crash.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

THIS = Path(__file__).resolve().parent
PY = sys.executable
sys.path.insert(0, str(THIS))
from _paths import repo_root, westk_root  # noqa: E402

# Derive defaults through the shared path helper. Active defaults use the
# numbered physical workspace layout; historical aliases are not required.
REPO_ROOT = repo_root()
WORKSPACE_ROOT = REPO_ROOT.parent
WESTK_ROOT = westk_root()
DEFAULT_XLSX = str(WORKSPACE_ROOT / "*" / "01-requirements" / "**" / "test-cases-*.xlsx")
DEFAULT_FEATURES = str(WESTK_ROOT / "02-automation" / "01-features")
DEFAULT_DB = str(REPO_ROOT / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db")
DEFAULT_REPORT_DIR = str(REPO_ROOT / "06-artifacts")


def run(label: str, args: list[str]) -> int:
    print("\n" + "=" * 72)
    print(f"[gate] {label}")
    print("=" * 72)
    proc = subprocess.run([PY, *args])
    print(f"[gate] {label} -> exit {proc.returncode}")
    return proc.returncode


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", nargs="+", default=[DEFAULT_XLSX],
                   help="xlsx file(s) or glob(s) to validate")
    p.add_argument("--features", default=DEFAULT_FEATURES)
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    p.add_argument("--case-prefix", action="append", nargs="+", default=[],
                   metavar="PREFIX",
                   help=("limit traceability comparison to case IDs starting "
                         "with one of these prefixes"))
    p.add_argument("--skip", nargs="+", default=[],
                   choices=["schema", "traceability", "evidence", "template-governance", "review-interface", "coverage", "signoff", "case-review", "case-audit"],
                   help="skip one or more validators (debugging only)")
    return p.parse_args()


def flatten_case_prefixes(raw_prefixes: list[list[str]]) -> list[str]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for group in raw_prefixes:
        for prefix in group:
            prefix = prefix.strip()
            if not prefix or prefix in seen:
                continue
            seen.add(prefix)
            prefixes.append(prefix)
    return prefixes


def main() -> int:
    args = parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    exits: dict[str, int] = {}
    case_prefixes = flatten_case_prefixes(args.case_prefix)

    if "schema" not in args.skip:
        exits["schema"] = run(
            "1/9  validate_testcase_xlsx",
            [str(THIS / "validate_testcase_xlsx.py"), *args.xlsx],
        )
    if "traceability" not in args.skip:
        traceability_args = [
            str(THIS / "check_traceability.py"),
            "--xlsx", *args.xlsx,
            "--features", args.features,
            "--db", args.db,
            "--report-dir", args.report_dir,
        ]
        if case_prefixes:
            traceability_args.extend(["--case-prefix", *case_prefixes])
        exits["traceability"] = run(
            "2/9  check_traceability",
            traceability_args,
        )
    if "evidence" not in args.skip:
        exits["evidence"] = run(
            "3/9  validate_evidence",
            [str(THIS / "validate_evidence.py"), *args.xlsx],
        )
    if "template-governance" not in args.skip:
        exits["template-governance"] = run(
            "4/9  check_template_governance",
            [str(THIS / "check_template_governance.py")],
        )
    if "review-interface" not in args.skip:
        exits["review-interface"] = run(
            "5/9  check_requirement_review_interface",
            [str(THIS / "check_requirement_review_interface.py")],
        )
    if "coverage" not in args.skip:
        exits["coverage"] = run(
            "6/9  check_workflow_coverage",
            [str(THIS / "check_workflow_coverage.py")],
        )
    if "signoff" not in args.skip:
        exits["signoff"] = run(
            "7/9  check_signoff_gate",
            [str(THIS / "check_signoff_gate.py")],
        )
    if "case-review" not in args.skip:
        exits["case-review"] = run(
            "8/9  check_testcase_review_gate",
            [str(THIS / "check_testcase_review_gate.py"), "--xlsx", *args.xlsx, "--strict"],
        )
    if "case-audit" not in args.skip:
        exits["case-audit"] = run(
            "9/9  check_testcase_audit_trail",
            [str(THIS / "check_testcase_audit_trail.py"), "--xlsx", *args.xlsx],
        )

    print("\n" + "=" * 72)
    print("[gate] SUMMARY")
    print("=" * 72)
    for name, code in exits.items():
        verdict = "PASS" if code == 0 else f"FAIL (exit {code})"
        print(f"  {name:14s}  {verdict}")

    overall = 0 if all(c == 0 for c in exits.values()) else 1
    print(f"\n[gate] OVERALL: {'PASS' if overall == 0 else 'FAIL'}")
    return overall


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(2)
