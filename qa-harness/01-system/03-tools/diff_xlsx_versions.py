"""diff_xlsx_versions.py — semantic diff between two test-case xlsx versions.

Given OLD.xlsx + NEW.xlsx, emit a JSON report with three buckets:
  - added     case IDs in NEW but not in OLD
  - removed   case IDs in OLD but not in NEW
  - modified  case IDs present in both, with at least one significant cell changed

What counts as "significant" — by default, the meaningful design columns:
  scenario, description, precond, steps, test_data, expected, priority, module

Execution-side columns (status, actual, comments, date, env, screenshots,
executed by) are IGNORED — those rotate every run and are not part of the
requirement contract.

Use:
  python 01-system/03-tools/diff_xlsx_versions.py OLD.xlsx NEW.xlsx
  python 01-system/03-tools/diff_xlsx_versions.py OLD.xlsx NEW.xlsx --out report.json
  python 01-system/03-tools/diff_xlsx_versions.py OLD.xlsx NEW.xlsx --md report.md

Exit: 0 if diff completed (even if changes found); 2 on usage / file error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

# Make the shared helpers importable when run via `python 01-system/03-tools/...`
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _validator_common import (   # noqa: E402
    find_columns, extract_case_id, cell_str, reconfigure_stdout,
)

# Columns whose change matters for "requirement changed" purposes.
# Anything not in this set is treated as run-time / cosmetic noise.
SIGNIFICANT_COLS = (
    "scenario", "description", "precond", "steps",
    "test_data", "expected", "priority", "severity", "module",
)


def _load_cases(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    """Read every test case row from an xlsx. Returns (cases, col_map)
    where cases is keyed by case ID."""
    wb = load_workbook(path, data_only=True)
    ws = wb.active
    cols, missing = find_columns(ws)
    if "id" not in cols:
        raise SystemExit(f"{path.name}: no 'Test Case ID' column found "
                         f"(missing canonical headers: {missing})")
    id_col = cols["id"]
    cases: dict[str, dict[str, str]] = {}
    for row in range(2, ws.max_row + 1):
        cid_raw = cell_str(ws, row, id_col)
        cid = extract_case_id(cid_raw)
        if not cid:
            continue
        record: dict[str, str] = {}
        for name in SIGNIFICANT_COLS:
            if name in cols:
                record[name] = cell_str(ws, row, cols[name])
        record["_row"] = str(row)
        cases[cid] = record
    return cases, cols


def diff(old_path: Path, new_path: Path) -> dict[str, Any]:
    old_cases, _ = _load_cases(old_path)
    new_cases, _ = _load_cases(new_path)

    old_ids = set(old_cases)
    new_ids = set(new_cases)

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)

    modified: list[dict[str, Any]] = []
    for cid in sorted(old_ids & new_ids):
        diffs = {}
        for col in SIGNIFICANT_COLS:
            o, n = old_cases[cid].get(col, ""), new_cases[cid].get(col, "")
            if o != n:
                diffs[col] = {"old": o, "new": n}
        if diffs:
            modified.append({"id": cid, "changes": diffs})

    return {
        "old": str(old_path),
        "new": str(new_path),
        "summary": {
            "old_count": len(old_ids),
            "new_count": len(new_ids),
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
        },
        "added": added,
        "removed": removed,
        "modified": modified,
    }


def render_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        f"# xlsx version diff",
        "",
        f"- **Old:** `{report['old']}`",
        f"- **New:** `{report['new']}`",
        "",
        f"## Summary",
        "",
        f"| | Old | New | Δ |",
        f"|---|---|---|---|",
        f"| Cases | {s['old_count']} | {s['new_count']} | {s['new_count'] - s['old_count']:+d} |",
        f"| Added | | | {s['added']} |",
        f"| Removed | | | {s['removed']} |",
        f"| Modified | | | {s['modified']} |",
        "",
    ]

    if report["added"]:
        lines += ["## Added", ""]
        lines += [f"- `{cid}`" for cid in report["added"]]
        lines.append("")

    if report["removed"]:
        lines += ["## Removed", ""]
        lines += [f"- `{cid}`" for cid in report["removed"]]
        lines.append("")

    if report["modified"]:
        lines += ["## Modified", ""]
        for m in report["modified"]:
            lines.append(f"### `{m['id']}`")
            lines.append("")
            for col, d in m["changes"].items():
                lines.append(f"**{col}**")
                lines.append("")
                lines.append(f"- old: {d['old'][:200]!r}")
                lines.append(f"- new: {d['new'][:200]!r}")
                lines.append("")

    return "\n".join(lines)


def main() -> int:
    reconfigure_stdout()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("old", type=Path, help="older xlsx version")
    p.add_argument("new", type=Path, help="newer xlsx version")
    p.add_argument("--out", type=Path, help="JSON report path (default: stdout)")
    p.add_argument("--md", type=Path, help="also write a human-readable md report")
    args = p.parse_args()

    for f in (args.old, args.new):
        if not f.exists():
            print(f"ERROR: file not found: {f}", file=sys.stderr)
            return 2

    report = diff(args.old, args.new)

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"[diff] wrote {args.out}")
    else:
        print(text)

    if args.md:
        args.md.write_text(render_md(report), encoding="utf-8")
        print(f"[diff] wrote {args.md}")

    s = report["summary"]
    print(f"\n[diff] summary: +{s['added']}  -{s['removed']}  ~{s['modified']}  "
          f"({s['old_count']} → {s['new_count']})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
