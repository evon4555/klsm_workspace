"""Shared helpers for the four Phase-1 harness validators.

Validators in this directory all follow the same contract:
  - exit 0 on PASS, 1 on FAIL, 2 on usage/crash
  - final stdout line: RESULT: PASS|FAIL  checked=N  failures=M
  - all CLI accept absolute paths so they work from any cwd
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Case ID: SIT-TC-{PROJ}-{MODULE}-NNN. Module/project tokens allow mixed case
# (real project usage shows both AUTH and Cookies). Digits suffix is 3-digit.
CASE_ID_RE = re.compile(r"^SIT-TC-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3}$")
CASE_ID_PREFIX_RE = re.compile(r"\bSIT-TC-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3}\b")

# Canonical semantic columns the harness depends on. Keys are stable names;
# the dict value is a list of header-text variants (lowercased+space-collapsed)
# that count as a match. Columns are discovered at runtime from the header row,
# so xlsx files may add extra columns (e.g. 西九's optional 'Label') without
# breaking validators that key on semantics.
CANONICAL_COLS: dict[str, list[str]] = {
    "id":          ["test case id"],
    "module":      ["module/feature", "module"],
    "priority":    ["priority"],
    "severity":    ["severity"],
    "source":      ["collected from"],
    "scenario":    ["test scenario"],
    "description": ["test case description"],
    "precond":     ["preconditions"],
    "steps":       ["test steps"],
    "test_data":   ["test data"],
    "expected":    ["expected result"],
    "owner":       ["test case owner"],
    "env":         ["environment"],
    "date":        ["execution date"],
    "by":          ["executed by"],
    "actual":      ["actual result"],
    "status":      ["status"],
    "comments":    ["comments/remarks", "comments", "remarks"],
    "screenshots": ["screenshots", "screenshot"],
}

REQUIRED_NON_EMPTY = ["id", "module", "scenario", "steps", "expected"]
EXEC_REQUIRED_WHEN_STATUS = ["env", "date", "by", "actual", "comments"]

VALID_PRIORITY = {"High", "Medium", "Low", "P0", "P1", "P2", "P3", ""}
VALID_STATUS = {"Pass", "Fail", "NA", "In Progress", "Not Run",
                "Blocked", "Skipped", "Deferred", ""}
YELLOW_HEX = "FFFFF2CC"


def reconfigure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _normalize_header(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def find_columns(ws) -> tuple[dict[str, int], list[str]]:
    """Map canonical semantic names to actual column indices.

    Returns (mapping, missing). `mapping[name]` is the 1-based column index,
    `missing` is the list of canonical names whose header was not found.
    """
    headers: dict[int, str] = {}
    for col in range(1, ws.max_column + 1):
        headers[col] = _normalize_header(ws.cell(row=1, column=col).value)

    mapping: dict[str, int] = {}
    for name, variants in CANONICAL_COLS.items():
        for col, htext in headers.items():
            if any(htext.startswith(v) for v in variants):
                mapping[name] = col
                break
    missing = [n for n in CANONICAL_COLS if n not in mapping]
    return mapping, missing


def is_yellow(cell) -> bool:
    f = cell.fill
    if f is None or f.fgColor is None:
        return False
    rgb = getattr(f.fgColor, "rgb", None)
    return isinstance(rgb, str) and rgb.upper() == YELLOW_HEX


def extract_case_id(text) -> str | None:
    if not text:
        return None
    m = CASE_ID_PREFIX_RE.search(str(text))
    return m.group(0) if m else None


def expand_paths(args: list[str]) -> list[Path]:
    import glob as _glob
    out: list[Path] = []
    for a in args:
        p = Path(a)
        if any(ch in a for ch in "*?["):
            out.extend(sorted(Path(m) for m in _glob.glob(a, recursive=True)))
        elif p.is_dir():
            out.extend(sorted(p.glob("*.xlsx")))
        elif p.exists():
            out.append(p)
        else:
            out.extend(sorted(Path(m) for m in _glob.glob(a, recursive=True)))
    unique: list[Path] = []
    seen: set[str] = set()
    for p in out:
        if p.name.startswith("~$"):
            continue
        try:
            key = str(p.resolve()).lower()
        except Exception:
            key = str(p.absolute()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def cell_str(ws, row: int, col: int) -> str:
    v = ws.cell(row=row, column=col).value
    return "" if v is None else str(v).strip()


def emit_result(checked: int, failures: int) -> int:
    verdict = "PASS" if failures == 0 else "FAIL"
    print(f"\nRESULT: {verdict}  checked={checked}  failures={failures}")
    return 0 if failures == 0 else 1
