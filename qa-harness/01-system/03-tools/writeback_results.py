"""writeback_results.py — Phase-1 validator #4 (also a writer).

Push Behave/dashboard execution results into the xlsx execution columns
(Environment, Execution Date, Executed By, Actual Result, Status,
Comments/Remarks). Screenshots column is left untouched — that is owned by
update_evidence.py.

Source of truth (pick one):
  --from-db PATH              read latest run from dashboard SQLite
                              (default: <qa-harness>/02-platform/02-dashboard/01-backend/dashboard.db)
  --from-behave-json PATH     read a `behave --format=json` output file

Source-row preservation rules (never overwrite a human judgment):
  - rows whose current Status is one of {Deferred, NA, Blocked, Skipped}
    are skipped when the new run status is 'skipped' or 'untested'.
  - --dry-run prints the planned writes without modifying the file.
  - a timestamped .bak copy of the xlsx is written before any save.

Status mapping (Behave -> xlsx):
  passed -> Pass
  failed -> Fail
  skipped -> NA
  untested / undefined -> Not Run

Usage:
  python writeback_results.py --xlsx PATH (--from-db [DB] | --from-behave-json JSON) \\
      [--env SIT] [--executor Evan] [--dry-run]

Exit:  0 success,  1 partial (some unmatched),  2 usage/crash.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from openpyxl import load_workbook

from _validator_common import (
    cell_str, emit_result, extract_case_id, find_columns, reconfigure_stdout,
)
from _paths import repo_root, westk_root

REPO_ROOT = repo_root()
WESTK_ROOT = westk_root()
DEFAULT_DB = str(REPO_ROOT / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db")
AUTOMATION_REF = str(WESTK_ROOT / "02-automation")

STATUS_MAP = {
    "passed": "Pass",
    "failed": "Fail",
    "skipped": "NA",
    "untested": "Not Run",
    "undefined": "Not Run",
}

PROTECTED_STATUS = {"Deferred", "NA", "Blocked", "Skipped"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", required=True, help="target xlsx")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-db", nargs="?", const=DEFAULT_DB,
                     help="read from dashboard.db (default path used when no value)")
    src.add_argument("--from-behave-json", help="read from behave json output")
    p.add_argument("--env", default="SIT", help="filter run by env (db source only)")
    p.add_argument("--executor", default="Evan")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def load_from_db(db_path: Path, env: str) -> tuple[dict[str, dict], str | None]:
    """Aggregate: for each case_id, take the most recent scenario row in this env.

    This avoids a 3-case smoke run overwriting the results of an earlier
    35-case full run.
    """
    if not db_path.exists():
        raise SystemExit(f"db not found: {db_path}")
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    env_lc = env.lower()
    row = cur.execute(
        "SELECT id, env, finished_at FROM test_runs "
        "WHERE LOWER(env) = ? ORDER BY id DESC LIMIT 1",
        (env_lc,),
    ).fetchone()
    if row is None:
        envs = [r[0] for r in cur.execute("SELECT DISTINCT env FROM test_runs")]
        raise SystemExit(f"no test_runs with env={env} (have: {envs})")
    latest_run_id, _, latest_finished_at = row
    print(f"Latest run for env={env}: run_id={latest_run_id} at {latest_finished_at}")

    results: dict[str, dict] = {}
    latest_run_id_by_cid: dict[str, int] = {}
    for name, status, feature, error_msg, run_id in cur.execute(
        "SELECT ts.name, ts.status, ts.feature, ts.error_msg, ts.run_id "
        "FROM test_scenarios ts JOIN test_runs tr ON ts.run_id = tr.id "
        "WHERE LOWER(tr.env) = ? ORDER BY ts.run_id DESC, ts.id DESC",
        (env_lc,),
    ):
        cid = extract_case_id(name)
        if not cid or cid in results:
            continue
        results[cid] = {
            "status": status,
            "feature": feature or "",
            "error": error_msg or "",
            "name": name,
            "run_id": run_id,
        }
        latest_run_id_by_cid[cid] = run_id
    con.close()

    run_date = None
    if latest_finished_at:
        run_date = str(latest_finished_at).split(" ")[0].split("T")[0]
    print(f"Aggregated {len(results)} unique case results across runs in env={env}")
    return results, run_date


def load_from_behave_json(json_path: Path) -> tuple[dict[str, dict], str | None]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    results: dict[str, dict] = {}
    for feat in data:
        feat_loc = feat.get("location", "")
        feat_file = feat_loc.split(":")[0] if feat_loc else feat.get("name", "")
        for elt in feat.get("elements", []):
            if elt.get("type") != "scenario":
                continue
            name = elt.get("name", "")
            cid = extract_case_id(name)
            if not cid:
                continue
            status = elt.get("status", "untested")
            error = ""
            for step in elt.get("steps", []):
                res = step.get("result") or {}
                if res.get("status") == "failed":
                    em = res.get("error_message", "")
                    error = em if isinstance(em, str) else "\n".join(em)
                    break
            results[cid] = {
                "status": status, "feature": feat_file, "error": error, "name": name,
            }
    today = _dt.date.today().isoformat()
    return results, today


def main(argv: list[str]) -> int:
    reconfigure_stdout()
    args = parse_args()

    xlsx_path = Path(args.xlsx)
    if not xlsx_path.exists():
        print(f"xlsx not found: {xlsx_path}")
        return 2

    if args.from_db is not None:
        results, run_date = load_from_db(Path(args.from_db), args.env)
        env_value = args.env
    else:
        results, run_date = load_from_behave_json(Path(args.from_behave_json))
        env_value = args.env

    print(f"Loaded {len(results)} scenario results")

    wb = load_workbook(xlsx_path)
    if "Test Cases" not in wb.sheetnames:
        print(f"no 'Test Cases' sheet in {xlsx_path}")
        return 2
    ws = wb["Test Cases"]
    cols, missing = find_columns(ws)
    needed = {"id", "env", "date", "by", "actual", "status", "comments"}
    if not needed.issubset(cols):
        print(f"missing required headers: {sorted(needed - cols.keys())}")
        return 2

    planned: list[tuple[int, str, str, str]] = []  # (row, cid, old_status, new_status)
    skipped_protected: list[tuple[str, str, str]] = []
    unmatched_in_results = set(results)

    for r in range(2, ws.max_row + 1):
        cid = cell_str(ws, r, cols["id"])
        if not cid or cid not in results:
            continue
        unmatched_in_results.discard(cid)
        info = results[cid]
        behave_status = info["status"]
        new_status = STATUS_MAP.get(behave_status, "Not Run")
        old_status = cell_str(ws, r, cols["status"])

        if old_status in PROTECTED_STATUS and behave_status in ("skipped", "untested", "undefined"):
            skipped_protected.append((cid, old_status, behave_status))
            continue

        new_actual = (
            "As Expected" if behave_status == "passed"
            else (info["error"][:200] if behave_status == "failed"
                  else f"Not executed ({behave_status})")
        )
        new_comments = (
            f"{AUTOMATION_REF} ({info['feature']}, scenario {cid})"
            if info["feature"] else f"{AUTOMATION_REF} (scenario {cid})"
        )

        planned.append((r, cid, old_status, new_status))

        if not args.dry_run:
            ws.cell(row=r, column=cols["env"]).value = env_value
            ws.cell(row=r, column=cols["date"]).value = run_date or _dt.date.today().isoformat()
            ws.cell(row=r, column=cols["by"]).value = args.executor
            ws.cell(row=r, column=cols["actual"]).value = new_actual
            ws.cell(row=r, column=cols["status"]).value = new_status
            ws.cell(row=r, column=cols["comments"]).value = new_comments

    print(f"\nPlanned writes: {len(planned)}")
    for r, cid, old, new in planned[:30]:
        print(f"  row {r}  {cid}  {old or '(empty)'} -> {new}")
    if len(planned) > 30:
        print(f"  ... and {len(planned) - 30} more")

    if skipped_protected:
        print(f"\nProtected rows (kept human judgment): {len(skipped_protected)}")
        for cid, old, behave in skipped_protected[:10]:
            print(f"  {cid}  xlsx={old}  behave={behave}")

    if unmatched_in_results:
        print(f"\nResults with no matching xlsx row: {len(unmatched_in_results)}")
        for cid in sorted(unmatched_in_results)[:10]:
            print(f"  {cid}")

    if not args.dry_run and planned:
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = xlsx_path.with_suffix(f".bak-{ts}.xlsx")
        shutil.copy(xlsx_path, backup)
        wb.save(xlsx_path)
        print(f"\nWrote {xlsx_path} (backup at {backup.name})")
    elif args.dry_run:
        print("\n[DRY RUN] no file written")

    failures = len(unmatched_in_results)
    return emit_result(checked=len(results), failures=failures)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)
