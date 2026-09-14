"""validate_evidence.py — Phase-1 validator #3.

For each Pass/Fail row, check that evidence is present:
  - Actual Result column is non-empty
  - Comments/Remarks column references the automation source
    (a `D:/Workspace/west-kowloon/02-automation/01-features` path or a project-relative feature path)
  - At least one image is embedded into one of the row's cells
    (openpyxl ws._images with anchor inside the row's column range)
  - For Status=Fail, Actual Result must not be a generic 'As Expected' string

Strict mode (the only mode): missing evidence = FAIL.

Usage:
  python validate_evidence.py <xlsx-or-glob> [...]

Exit:  0 PASS,  1 FAIL,  2 usage/crash.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from _validator_common import (
    cell_str, emit_result, expand_paths, find_columns, reconfigure_stdout,
)

JUDGED_STATUSES = {"Pass", "Fail"}
AS_EXPECTED_RE = re.compile(r"^\s*as\s+expected\s*\.?\s*$", re.IGNORECASE)
AUTOMATION_REF_RE = re.compile(
    r"(D:[\\/]Workspace[\\/]west-kowloon[\\/]02-automation|west-kowloon[\\/]02-automation|02-automation[\\/]|01-features[\\/]|features[\\/])",
    re.IGNORECASE,
)


def collect_image_rows(ws) -> set[int]:
    """Return the set of row indices that have at least one embedded image.

    openpyxl's image anchors expose .anchor._from with col/row (0-based) for
    twoCellAnchor / oneCellAnchor. We treat an image as covering its top-left
    cell row.
    """
    rows: set[int] = set()
    for img in getattr(ws, "_images", []):
        anchor = getattr(img, "anchor", None)
        if anchor is None:
            continue
        frm = getattr(anchor, "_from", None)
        if frm is not None:
            rows.add(int(frm.row) + 1)
            continue
        cell_attr = getattr(anchor, "cell", None)
        if isinstance(cell_attr, str):
            m = re.match(r"([A-Z]+)(\d+)", cell_attr)
            if m:
                rows.add(int(m.group(2)))
    return rows


def check_one(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        wb = load_workbook(path, data_only=True)
    except Exception as e:
        return [f"cannot open: {e!r}"]

    if "Test Cases" not in wb.sheetnames:
        return [f"missing sheet 'Test Cases'"]
    ws = wb["Test Cases"]

    cols, missing = find_columns(ws)
    needed = {"id", "status", "actual", "comments"}
    if not needed.issubset(cols):
        return [f"missing required headers: {sorted(needed - cols.keys())}"]

    image_rows = collect_image_rows(ws)

    for r in range(2, ws.max_row + 1):
        cid = cell_str(ws, r, cols["id"])
        if not cid:
            continue
        st = cell_str(ws, r, cols["status"])
        if st not in JUDGED_STATUSES:
            continue

        actual = cell_str(ws, r, cols["actual"])
        if not actual:
            failures.append(f"row {r} ({cid}): status={st} but Actual Result empty")
        elif st == "Fail" and AS_EXPECTED_RE.match(actual):
            failures.append(
                f"row {r} ({cid}): status=Fail but Actual Result = 'As Expected' "
                "(must describe the failure)"
            )

        comments = cell_str(ws, r, cols["comments"])
        if not comments:
            failures.append(f"row {r} ({cid}): Comments/Remarks empty")
        elif not AUTOMATION_REF_RE.search(comments):
            failures.append(
                f"row {r} ({cid}): Comments has no automation reference "
                f"(expected numbered project automation or feature path); got {comments[:80]!r}"
            )

        if r not in image_rows:
            failures.append(
                f"row {r} ({cid}): no embedded screenshot found in row "
                "(strict mode requires an image anchored in this row)"
            )

    return failures


def main(argv: list[str]) -> int:
    reconfigure_stdout()
    if len(argv) < 2:
        print(__doc__)
        return 2

    paths = expand_paths(argv[1:])
    if not paths:
        print(f"no xlsx matched: {argv[1:]}")
        return 2

    total = 0
    for p in paths:
        print(f"=== {p.name}")
        fails = check_one(p)
        if not fails:
            print("  OK")
        else:
            for f in fails:
                print(f"  FAIL: {f}")
            total += len(fails)

    return emit_result(checked=len(paths), failures=total)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(2)
