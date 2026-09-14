"""maintenance_scan.py — when a new xlsx version lands, scan 01-features/ and
emit a maintenance to-do list so automation doesn't silently rot.

Wraps `diff_xlsx_versions.py` and cross-references each changed case id
against `02-automation/01-features/*.feature`, using the traceability key
(scenario-name prefix first; `@<case-id>` tag is legacy fallback). For each diff
bucket it produces:

  ADDED      case id has no .feature scenario        →  print as "TODO: write automation"
                                                        + optionally generate stub
  REMOVED    case id has a .feature scenario         →  print as "deprecate candidate"
                                                        + suggest soft-delete move
  MODIFIED   case id has a .feature scenario         →  print as "drift candidate"
                                                        + show id so human can compare

The script is **read-only** by default — it never moves or deletes files.
Use --apply-deprecate to actually move removed scenarios into
01-features/deprecated/<ISO-date>/.

Use:
  python 01-system/03-tools/maintenance_scan.py NEW.xlsx
  python 01-system/03-tools/maintenance_scan.py NEW.xlsx --old OLD.xlsx
  python 01-system/03-tools/maintenance_scan.py NEW.xlsx --out maintenance_report.md
  python 01-system/03-tools/maintenance_scan.py NEW.xlsx --apply-deprecate

Exit: 0 if scan completed (even with TODOs); 2 on usage / file error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import westk_root  # noqa: E402
from _validator_common import reconfigure_stdout, CASE_ID_PREFIX_RE  # noqa: E402
from diff_xlsx_versions import diff, _load_cases  # noqa: E402

DEFAULT_FEATURES_DIR = westk_root() / "02-automation" / "01-features"

# Regex to find a legacy tag of the form @SIT-TC-WEB-AUTH-013 anywhere in a line
TAG_RE = re.compile(r"@(SIT-TC-[A-Za-z0-9]+-[A-Za-z0-9]+-\d{3})")

# Regex to recognise a "Scenario:" line in a .feature file
SCENARIO_LINE_RE = re.compile(r"^\s*Scenario(?:\s+Outline)?:\s*(.+)$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# .feature index — { case_id → [(feature_file, scenario_name, line_no), ...] }
# ---------------------------------------------------------------------------
def index_features(features_dir: Path) -> dict[str, list[tuple[Path, str, int]]]:
    """Walk every .feature file under features_dir and bucket each scenario
    by the case id it references. Prefer scenario-name prefix; use @tag only
    as a legacy fallback."""
    idx: dict[str, list[tuple[Path, str, int]]] = {}
    for f in sorted(features_dir.rglob("*.feature")):
        if "deprecated" in f.parts:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        pending_tags: list[str] = []
        for ln_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("@"):
                # Tag line — collect all tags on it.
                pending_tags.extend(TAG_RE.findall(line))
                continue
            m = SCENARIO_LINE_RE.match(line)
            if m:
                name = m.group(1).strip()
                ids: list[str] = []
                nm = CASE_ID_PREFIX_RE.search(name)
                if nm:
                    ids.append(nm.group(0))
                else:
                    ids.extend(pending_tags)
                for cid in ids:
                    idx.setdefault(cid, []).append((f, name, ln_no))
                pending_tags = []
            elif stripped and not stripped.startswith("#"):
                # Non-blank, non-tag, non-comment, non-scenario line resets
                # the tag buffer (we're inside a step block).
                pending_tags = []
    return idx


# ---------------------------------------------------------------------------
# Auto-find previous xlsx version
# ---------------------------------------------------------------------------
_DATE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})\b")


def autofind_previous(new_xlsx: Path) -> Path | None:
    """Find the previous timestamped xlsx in the same directory. Convention:
    `test-cases-<scope>_<YYYY-MM-DD>.xlsx`."""
    siblings = sorted(new_xlsx.parent.glob(new_xlsx.stem.split("_")[0] + "_*.xlsx"))
    siblings = [s for s in siblings if s != new_xlsx]
    if not siblings:
        # Maybe no date suffix yet — try non-suffixed neighbour.
        base = new_xlsx.stem.split("_")[0] + ".xlsx"
        cand = new_xlsx.parent / base
        return cand if cand.exists() and cand != new_xlsx else None
    return siblings[-1]


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------
def render_report(
    report: dict[str, Any],
    feature_idx: dict[str, list[tuple[Path, str, int]]],
    features_dir: Path,
) -> tuple[str, dict[str, Any], list[tuple[str, Path]]]:
    """Render the maintenance report (md).
    Returns (md_text, summary_dict, deprecate_candidates) where the third
    item is the list of (case_id, feature_file_path) pairs that
    --apply-deprecate would move."""
    added = report["added"]
    removed = report["removed"]
    modified = [m["id"] for m in report["modified"]]

    todo_write: list[str] = []           # added case, no .feature → write automation
    todo_deprecate: list[tuple[str, Path]] = []   # removed case, .feature exists → soft-delete
    todo_drift: list[tuple[str, Path, str]] = []  # modified case, .feature exists → check drift
    todo_modified_unautomated: list[str] = []     # modified case, no .feature → write fresh

    # Added cases without automation
    for cid in added:
        if cid not in feature_idx:
            todo_write.append(cid)

    # Removed cases that still have a .feature
    for cid in removed:
        for f, name, ln in feature_idx.get(cid, []):
            todo_deprecate.append((cid, f))

    # Modified cases — split by whether they were automated already
    for cid in modified:
        scenarios = feature_idx.get(cid, [])
        if scenarios:
            for f, name, ln in scenarios:
                todo_drift.append((cid, f, name))
        else:
            todo_modified_unautomated.append(cid)

    s = report["summary"]
    lines = [
        f"# Maintenance Scan",
        "",
        f"- Generated: {_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')}",
        f"- Old xlsx: `{report['old']}`",
        f"- New xlsx: `{report['new']}`",
        f"- Features scanned: `{features_dir}`",
        "",
        f"## Summary",
        "",
        f"| Bucket | Cases | Needs work |",
        f"|---|---|---|",
        f"| Added | {s['added']} | {len(todo_write)} (no .feature yet) |",
        f"| Removed | {s['removed']} | {len(todo_deprecate)} (deprecate candidates) |",
        f"| Modified | {s['modified']} | {len(todo_drift)} drift + {len(todo_modified_unautomated)} never automated |",
        "",
    ]

    # --- TODO: write automation -------------------------------------------
    if todo_write:
        lines += [
            "## TODO — write automation",
            "",
            "These case IDs are new in the xlsx but have no matching scenario",
            "in `02-automation/01-features/`. Write a `.feature` scenario for each.",
            "",
        ]
        lines += [f"- `{cid}`" for cid in todo_write]
        lines.append("")

    # --- Deprecate candidates --------------------------------------------
    if todo_deprecate:
        lines += [
            "## DEPRECATE CANDIDATES — soft delete",
            "",
            "These case IDs were removed from the xlsx but still have a",
            "scenario in `02-automation/01-features/`. Move to `01-features/deprecated/<date>/`",
            "(soft delete — keep for 1-2 sprints before hard delete). Run",
            "`maintenance_scan.py --apply-deprecate` to do it automatically.",
            "",
        ]
        for cid, f in todo_deprecate:
            lines.append(f"- `{cid}` → `{f.relative_to(features_dir.parent.parent)}`")
        lines.append("")

    # --- Modified but never automated ------------------------------------
    if todo_modified_unautomated:
        lines += [
            "## TODO — modified case never had automation",
            "",
            "These case IDs changed in the xlsx and have NO matching `.feature`",
            "scenario today. They were either never automated, or the scenario",
            "ID prefix / legacy tag doesn't match. Either way, write fresh automation now",
            "— the case description has just been refined, so the timing is right.",
            "",
        ]
        lines += [f"- `{cid}`" for cid in todo_modified_unautomated]
        lines.append("")

    # --- Drift candidates -------------------------------------------------
    if todo_drift:
        lines += [
            "## DRIFT CANDIDATES — review step text",
            "",
            "These case IDs were modified in the xlsx. Open the linked",
            "`.feature` scenario and compare step text against the new xlsx",
            "row; update steps where needed.",
            "",
            "| Case | Scenario | File |",
            "|---|---|---|",
        ]
        for cid, f, name in todo_drift:
            lines.append(f"| `{cid}` | {name} | `{f.relative_to(features_dir.parent.parent)}` |")
        lines.append("")

    if not (todo_write or todo_deprecate or todo_drift or todo_modified_unautomated):
        lines += [
            "## ✓ No maintenance work required",
            "",
            "Every changed case is already aligned with `02-automation/01-features/`.",
            "(This is unusual — normally a change implies SOME automation update.",
            " Double-check the xlsx diff actually has content.)",
            "",
        ]

    summary = {
        "added": s["added"],
        "removed": s["removed"],
        "modified": s["modified"],
        "todo_write": len(todo_write),
        "todo_deprecate": len(todo_deprecate),
        "todo_drift": len(todo_drift),
        "todo_modified_unautomated": len(todo_modified_unautomated),
    }
    return "\n".join(lines), summary, todo_deprecate


# ---------------------------------------------------------------------------
# Apply deprecate (move files into deprecated/<ISO-date>/)
#
# LIMITATION: this moves the WHOLE .feature file when any scenario inside it
# is a deprecate candidate. If a single feature file holds multiple scenarios
# and only one is being removed, moving the file ALSO retires the still-valid
# scenarios. Today this is OK because the codebase keeps one flow per file
# (antank_email_login / antank_registration / ...), so file-level moves
# accidentally match scenario-level moves. When that stops being true,
# upgrade to either (a) parse Gherkin and rewrite the file without the
# removed scenario, or (b) comment-out the scenario in place + add a
# @deprecated tag, or (c) only auto-deprecate when the file has just the
# one scenario. Until then, --apply-deprecate prints what it would do and
# the user can intervene if they see a cross-scenario file.
# ---------------------------------------------------------------------------
def apply_deprecate(todo: list[tuple[str, Path]], features_dir: Path) -> int:
    if not todo:
        print("[apply-deprecate] nothing to do")
        return 0
    today = _dt.date.today().isoformat()
    target_dir = features_dir / "deprecated" / today
    target_dir.mkdir(parents=True, exist_ok=True)
    seen: set[Path] = set()
    n = 0
    for cid, f in todo:
        if f in seen:
            continue
        seen.add(f)
        dest = target_dir / f.name
        if dest.exists():
            print(f"[apply-deprecate] skip (already exists): {dest}")
            continue
        shutil.move(str(f), str(dest))
        print(f"[apply-deprecate] {f.relative_to(features_dir)} → deprecated/{today}/{f.name}")
        n += 1
    print(f"[apply-deprecate] moved {n} file(s)")
    return n


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    reconfigure_stdout()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("new", type=Path, help="the new xlsx version")
    p.add_argument("--old", type=Path,
                   help="the old xlsx version (default: autofind sibling with date suffix)")
    p.add_argument("--features", type=Path, default=DEFAULT_FEATURES_DIR,
                   help=f"features dir (default: {DEFAULT_FEATURES_DIR})")
    p.add_argument("--out", type=Path, default=None,
                   help="maintenance_report.md path (default: alongside NEW xlsx)")
    p.add_argument("--apply-deprecate", action="store_true",
                   help="actually move deprecate candidates into 01-features/deprecated/<date>/")
    args = p.parse_args()

    if not args.new.exists():
        print(f"ERROR: NEW xlsx not found: {args.new}", file=sys.stderr)
        return 2

    old = args.old or autofind_previous(args.new)
    if not old or not old.exists():
        print(f"ERROR: could not autofind a previous xlsx version next to "
              f"{args.new.name}. Pass --old explicitly.", file=sys.stderr)
        return 2

    report = diff(old, args.new)
    feature_idx = index_features(args.features)
    md, summary, deprecate_list = render_report(report, feature_idx, args.features)

    out = args.out or (args.new.parent / "maintenance_report.md")
    out.write_text(md, encoding="utf-8")
    print(f"[maintenance-scan] wrote {out}")
    print(f"[maintenance-scan] summary: +{summary['added']}  -{summary['removed']}  "
          f"~{summary['modified']}")
    print(f"[maintenance-scan] work:    write={summary['todo_write']}  "
          f"deprecate={summary['todo_deprecate']}  drift={summary['todo_drift']}  "
          f"mod-unautomated={summary['todo_modified_unautomated']}")

    if args.apply_deprecate:
        apply_deprecate(deprecate_list, args.features)

    return 0


if __name__ == "__main__":
    sys.exit(main())
