"""check_rule_drift.py — scan every project's project-rules/ dir and
report promotion candidates per 01-system/11-rule-promotion.md.

Emits 4 buckets to artifacts/rule_drift_report.md:

  duplicate            same rule_id in 2+ projects → strong promotion signal
  stale-candidate      project-candidate not touched in >90 days
  promotion-tagged     candidate_for_promotion: yes
  orphan               missing frontmatter or rule_id

Exit:
  0  scan completed (regardless of findings — this is informational)
  2  on usage error / directory missing
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import repo_root  # noqa: E402

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO = repo_root()
DEFAULT_REQ_DIR = REPO.parent
DEFAULT_OUT = REPO / "06-artifacts" / "rule_drift_report.md"
STALE_DAYS = 90


def display_path(path: Path) -> str:
    workspace = REPO.parent
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_rule(path: Path) -> dict | None:
    """Read frontmatter. Return None if not a rule file (no frontmatter)."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except Exception:
        return None
    meta["_path"] = path
    meta["_mtime"] = _dt.date.fromtimestamp(path.stat().st_mtime)
    return meta


def scan(req_dir: Path) -> list[dict]:
    rules: list[dict] = []
    project_rule_dirs = list(req_dir.glob("*/01-requirements/00-project-overview/project-rules"))
    project_rule_dirs.extend(req_dir.glob("*/00-project-overview/project-rules"))
    for project_rules_dir in sorted(set(project_rule_dirs)):
        for p in sorted(project_rules_dir.glob("*.md")):
            if p.name == "README.md":
                continue
            r = parse_rule(p)
            if r is None:
                # orphan: file in project-rules but no frontmatter
                rules.append({
                    "_path": p,
                    "_orphan": True,
                    "rule_id": None,
                    "scope": "unknown",
                })
            else:
                parts = list(p.parts)
                if "01-requirements" in parts:
                    project = parts[parts.index("01-requirements") - 1]
                else:
                    project = p.parts[-4]
                r["_project"] = project
                rules.append(r)
    return rules


def render(rules: list[dict]) -> tuple[str, dict[str, int]]:
    today = _dt.date.today()

    duplicates: dict[str, list[dict]] = defaultdict(list)
    stale: list[dict] = []
    tagged: list[dict] = []
    orphans: list[dict] = []

    for r in rules:
        if r.get("_orphan"):
            orphans.append(r)
            continue
        rid = r.get("rule_id")
        if not rid:
            orphans.append(r)
            continue
        duplicates[rid].append(r)

        scope = (r.get("scope") or "").strip()
        if scope == "project-candidate":
            age = (today - r["_mtime"]).days
            if age > STALE_DAYS:
                stale.append({**r, "_age_days": age})
        if str(r.get("candidate_for_promotion", "")).strip().lower() == "yes":
            tagged.append(r)

    real_dupes = {rid: rs for rid, rs in duplicates.items() if len(rs) >= 2}

    counts = {
        "rules_total": sum(1 for r in rules if not r.get("_orphan")),
        "duplicates": len(real_dupes),
        "stale_candidates": len(stale),
        "promotion_tagged": len(tagged),
        "orphans": len(orphans),
    }

    lines = [
        "# Rule Drift Report",
        "",
        f"- Generated: {_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')}",
        f"- Scope: `*/01-requirements/00-project-overview/project-rules/`",
        "",
        "## Summary",
        "",
        f"| Bucket | Count |",
        f"|---|---|",
        f"| Total rule files | {counts['rules_total']} |",
        f"| Duplicate rule_ids (≥2 projects) | {counts['duplicates']} |",
        f"| Stale candidates (>{STALE_DAYS}d, scope=project-candidate) | {counts['stale_candidates']} |",
        f"| Promotion-tagged (candidate_for_promotion: yes) | {counts['promotion_tagged']} |",
        f"| Orphans (no frontmatter / no rule_id) | {counts['orphans']} |",
        "",
    ]

    if real_dupes:
        lines += ["## Duplicates — strong promotion signal", ""]
        for rid, rs in real_dupes.items():
            lines.append(f"### `{rid}`")
            lines.append("")
            for r in rs:
                lines.append(
                    f"- {r['_project']} — `{display_path(r['_path'])}` "
                    f"(scope={r.get('scope', '?')}, mtime={r['_mtime']})"
                )
            lines.append("")
            lines.append(
                f"**Action**: promote `{rid}` to system per "
                f"`01-system/11-rule-promotion.md`. Pick a home, move the body, "
                f"leave stubs in both project copies."
            )
            lines.append("")

    if stale:
        lines += ["## Stale candidates", ""]
        for r in stale:
            lines.append(
                f"- `{r.get('rule_id', '?')}` ({r['_project']}, "
                f"{r['_age_days']}d old) — `{display_path(r['_path'])}`"
            )
        lines.append("")
        lines.append(
            "**Action**: either promote OR downgrade `scope` to "
            "`project-permanent` + `candidate_for_promotion: no`."
        )
        lines.append("")

    if tagged:
        lines += ["## Promotion-tagged (review at next retro)", ""]
        for r in tagged:
            lines.append(
                f"- `{r.get('rule_id', '?')}` ({r['_project']}) — "
                f"`{display_path(r['_path'])}`"
            )
        lines.append("")

    if orphans:
        lines += ["## Orphans — fix metadata", ""]
        for r in orphans:
            lines.append(f"- `{display_path(r['_path'])}` — missing frontmatter / rule_id")
        lines.append("")
        lines.append(
            "**Action**: add the YAML frontmatter block per "
            "`01-system/11-rule-promotion.md`."
        )
        lines.append("")

    if not (real_dupes or stale or tagged or orphans):
        lines += [
            "## ✓ Nothing to action",
            "",
            "All rules well-formed; no duplicates across projects; no stale "
            "candidates; nothing tagged for retro review.",
            "",
        ]

    return "\n".join(lines), counts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--requirements-dir", type=Path, default=DEFAULT_REQ_DIR,
                   help=f"root of project requirement folders (default: {DEFAULT_REQ_DIR})")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT,
                   help=f"output report path (default: {DEFAULT_OUT})")
    args = p.parse_args()

    if not args.requirements_dir.is_dir():
        print(f"ERROR: requirements dir not found: {args.requirements_dir}", file=sys.stderr)
        return 2

    rules = scan(args.requirements_dir)
    md, counts = render(rules)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(f"[rule-drift] wrote {args.out}")
    print(f"[rule-drift] summary: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
