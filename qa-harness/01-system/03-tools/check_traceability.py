"""check_traceability.py — Phase-1 validator #2.

Cross-check requirement IDs across three sources:
  X = test case IDs found in one or more xlsx files
  F = test case IDs referenced by .feature files. New automation must use the
      scenario name prefix; explicit @SIT-TC-... tags are legacy fallback only.
  D = test case IDs found in dashboard SQLite (test_scenarios.name prefix)

PASS = X-F and F-X are both empty (every xlsx case has automation, every
automated scenario points at a real xlsx case).
D is reported as informational/warn only — it shows historical runs.

Outputs:
  - human-readable summary to stdout
  - artifacts/traceability_report.json next to the cwd (or --report-dir <dir>)

Usage:
  python check_traceability.py \\
      --xlsx "<project>/01-requirements/**/test-cases-*.xlsx" \\
      --features <west-kowloon>/02-automation/01-features \\
      --db <qa-harness>/02-platform/02-dashboard/01-backend/dashboard.db

Exit:  0 PASS,  1 FAIL,  2 usage/crash.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import TypeVar

from openpyxl import load_workbook

from _validator_common import (
    CASE_ID_PREFIX_RE, cell_str, emit_result, expand_paths, extract_case_id,
    find_columns, reconfigure_stdout,
)
from _paths import repo_root, westk_root

SCENARIO_RE = re.compile(r"^\s*Scenario(?:\s+Outline)?\s*:\s*(.*)$")
TAG_LINE_RE = re.compile(r"^\s*@")
T = TypeVar("T")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    project_root = westk_root()
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", required=True, nargs="+",
                   help="xlsx file(s) or glob(s)")
    p.add_argument("--features", default=str(project_root / "02-automation" / "01-features"),
                   help="root dir to scan for .feature files (recursive)")
    p.add_argument("--db", default=str(root / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db"),
                   help="dashboard sqlite path (optional)")
    p.add_argument("--report-dir", default=str(root / "06-artifacts"),
                   help="where to write traceability_report.json")
    p.add_argument("--case-prefix", action="append", nargs="+", default=[],
                   metavar="PREFIX",
                   help=("only compare case IDs starting with one of these "
                         "prefixes, e.g. SIT-TC-WEB-AUTH-"))
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


def filter_by_case_prefix(mapping: dict[str, T], prefixes: list[str]) -> dict[str, T]:
    if not prefixes:
        return mapping
    return {
        cid: value
        for cid, value in mapping.items()
        if any(cid.startswith(prefix) for prefix in prefixes)
    }


def collect_xlsx_ids(paths: list[Path]) -> dict[str, list[str]]:
    """case_id -> [xlsx-stem, ...] for diagnostics."""
    out: dict[str, list[str]] = {}
    for p in paths:
        try:
            wb = load_workbook(p, data_only=True, read_only=True)
        except Exception as e:
            print(f"WARN: cannot read {p}: {e}")
            continue
        if "Test Cases" not in wb.sheetnames:
            print(f"WARN: {p.name} has no 'Test Cases' sheet, skipping")
            continue
        ws = wb["Test Cases"]
        cols, missing = find_columns(ws)
        if "id" not in cols:
            print(f"WARN: {p.name} has no 'Test Case ID' header, skipping")
            continue
        id_col = cols["id"]
        for r in range(2, ws.max_row + 1):
            cid = cell_str(ws, r, id_col)
            if not cid:
                continue
            m = CASE_ID_PREFIX_RE.search(cid)
            if not m:
                continue
            out.setdefault(m.group(0), []).append(p.stem)
    return out


def collect_feature_ids(root: Path) -> dict[str, list[tuple[str, int, str]]]:
    """case_id -> [(feature-file-relpath, lineno, source), ...]
    source = 'scenario-prefix' | 'legacy-tag'
    """
    out: dict[str, list[tuple[str, int, str]]] = {}
    if not root.exists():
        print(f"WARN: features root {root} does not exist")
        return out

    for fp in sorted(root.rglob("*.feature")):
        try:
            lines = fp.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            print(f"WARN: cannot read {fp}: {e}")
            continue
        pending_tag_ids: list[str] = []
        for lineno, line in enumerate(lines, start=1):
            if TAG_LINE_RE.match(line):
                pending_tag_ids = []
                for tok in line.strip().split():
                    if tok.startswith("@"):
                        cid = extract_case_id(tok[1:])
                        if cid:
                            pending_tag_ids.append(cid)
                continue
            m = SCENARIO_RE.match(line)
            if not m:
                if line.strip():
                    pending_tag_ids = []
                continue
            scen_name = m.group(1).strip()
            ids_from_tags = pending_tag_ids[:]
            pending_tag_ids = []
            ids_from_prefix = []
            cid = extract_case_id(scen_name)
            if cid and scen_name.startswith(cid):
                ids_from_prefix.append(cid)
            chosen = ids_from_prefix or ids_from_tags
            relpath = str(fp.relative_to(root))
            for cid in chosen:
                src = "scenario-prefix" if ids_from_prefix else "legacy-tag"
                out.setdefault(cid, []).append((relpath, lineno, src))
            if not chosen and scen_name:
                pass
    return out


def collect_db_ids(db_path: Path) -> dict[str, int]:
    """case_id -> last_run_id (latest test_runs.id where scenario ran)."""
    if not db_path.exists():
        print(f"WARN: dashboard db {db_path} not found, skipping")
        return {}
    out: dict[str, int] = {}
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        for run_id, name in cur.execute(
            "SELECT run_id, name FROM test_scenarios ORDER BY run_id DESC"
        ):
            cid = extract_case_id(name)
            if cid and cid not in out:
                out[cid] = run_id
        con.close()
    except Exception as e:
        print(f"WARN: db read failed: {e}")
    return out


def main(argv: list[str]) -> int:
    reconfigure_stdout()
    args = parse_args()

    xlsx_paths = expand_paths(args.xlsx)
    if not xlsx_paths:
        print(f"no xlsx matched: {args.xlsx}")
        return 2

    print(f"Scanning {len(xlsx_paths)} xlsx + features dir {args.features}")
    X = collect_xlsx_ids(xlsx_paths)
    F = collect_feature_ids(Path(args.features))
    D = collect_db_ids(Path(args.db))
    case_prefixes = flatten_case_prefixes(args.case_prefix)
    if case_prefixes:
        X = filter_by_case_prefix(X, case_prefixes)
        F = filter_by_case_prefix(F, case_prefixes)
        D = filter_by_case_prefix(D, case_prefixes)
        print(f"Case prefix filter: {', '.join(case_prefixes)}")

    print(f"\nCase IDs:")
    print(f"  X (xlsx):     {len(X):4d}")
    print(f"  F (features): {len(F):4d}")
    print(f"  D (db):       {len(D):4d}")

    orphans_xf = sorted(set(X) - set(F))
    dirty_fx = sorted(set(F) - set(X))
    drift_df = sorted(set(D) - set(F))

    print(f"\n[X - F] xlsx cases with NO automation: {len(orphans_xf)}")
    by_module: dict[str, list[str]] = {}
    for cid in orphans_xf:
        parts = cid.split("-")
        mod = parts[3] if len(parts) >= 5 else "?"
        by_module.setdefault(mod, []).append(cid)
    for mod, ids in sorted(by_module.items()):
        print(f"  [{mod}] {len(ids):3d}: {', '.join(ids)}")

    print(f"\n[F - X] feature scenarios referencing UNKNOWN case IDs: {len(dirty_fx)}")
    for cid in dirty_fx:
        for fp, ln, src in F[cid]:
            print(f"  {cid}  {fp}:{ln}  ({src})")

    print(f"\n[D - F] db has runs of scenarios no longer in features (WARN): {len(drift_df)}")
    for cid in drift_df[:20]:
        print(f"  {cid}  last_run_id={D[cid]}")
    if len(drift_df) > 20:
        print(f"  ... and {len(drift_df) - 20} more")

    report = {
        "X_count": len(X),
        "F_count": len(F),
        "D_count": len(D),
        "case_prefixes": case_prefixes,
        "orphans_xf": orphans_xf,
        "dirty_fx": [(cid, F[cid]) for cid in dirty_fx],
        "drift_df": drift_df,
        "xlsx_by_id": {cid: srcs for cid, srcs in X.items()},
        "features_by_id": {cid: locs for cid, locs in F.items()},
    }
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "traceability_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"\nReport: {report_path}")

    failures = len(orphans_xf) + len(dirty_fx)
    return emit_result(checked=len(X) + len(F), failures=failures)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)
