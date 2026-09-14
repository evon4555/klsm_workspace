"""check_workflow_coverage.py — verify every skill + template is wired to a
workflow step in 02-qa-workflow.md.

Why this exists: the harness principle says every artifact must be traceable
to a step in the canonical workflow. Without a check, skills or templates
can be added but never referenced from the workflow — they become orphaned
methodology that no one knows when to use.

Run:
    python 01-system/03-tools/check_workflow_coverage.py

Exit 0 if every skill and template is referenced from 02-qa-workflow.md.
Non-zero otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

QA_SYSTEM = Path(__file__).resolve().parent.parent
WORKFLOW = QA_SYSTEM / "02-qa-workflow.md"
SKILLS_DIR = QA_SYSTEM / "01-skills"
TEMPLATES_DIR = QA_SYSTEM / "02-templates"


def main() -> int:
    if not WORKFLOW.exists():
        print(f"FAIL: {WORKFLOW} missing")
        return 2

    wf_text = WORKFLOW.read_text(encoding="utf-8")

    # Each skill is a dir under 01-skills/ containing SKILL.md.
    skills = sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )
    # Templates are .md files under 02-templates/ (minus README/TODO).
    templates = sorted(
        m.stem for m in TEMPLATES_DIR.glob("*.md")
        if m.name not in ("README.md", "TODO.md")
    )

    orphan_skills = [s for s in skills if s not in wf_text]
    orphan_templates = [t for t in templates if t not in wf_text]

    print(f"Skills: {len(skills)} total, {len(orphan_skills)} not mentioned in workflow")
    for s in orphan_skills:
        print(f"  ORPHAN skill: {s}")
    print(f"Templates: {len(templates)} total, {len(orphan_templates)} not mentioned in workflow")
    for t in orphan_templates:
        print(f"  ORPHAN template: {t}")

    failed = len(orphan_skills) + len(orphan_templates)
    print()
    if failed == 0:
        print(f"RESULT: PASS  ({len(skills)} skills + {len(templates)} templates all wired)")
        return 0
    print(f"RESULT: FAIL  ({failed} orphan(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
