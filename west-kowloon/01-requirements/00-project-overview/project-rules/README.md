# project-rules — 西九

Rules and conventions surfaced specifically during 西九 work that **may or may
not apply universally**.

This is the **incubator** for rules. The lifecycle is in
[01-system/11-rule-promotion.md](D:\Workspace\qa-harness\01-system\11-rule-promotion.md):

```
written here (project-candidate)
        ↓
  drift-detector flags as "duplicate across projects"
  OR retrospective decides "this is universal"
  OR compliance / security obviously applies broadly
        ↓
  promoted to `01-system` (a stub is left here pointing to the new home)
```

## Per-file frontmatter (mandatory)

Every `*.md` (except this README) must start with:

```yaml
---
rule_id: <short-kebab-id>
title: <one-line title>
scope: project-candidate            # or: project-permanent | promoted
created: YYYY-MM-DD
origin: <what triggered it — incident / PRD / customer ask>
applies_to: [西九]
candidate_for_promotion: yes|no|unknown
promoted_to: null                   # 01-system/<doc>.md once promoted
promoted_at: null
---
```

Without the frontmatter, the rule is invisible to
`D:\Workspace\qa-harness\01-system\03-tools\check_rule_drift.py` and can't be promoted.

## Adding a new rule

1. Pick a short kebab-case `rule_id` (`westk-imap-real-otp`, `westk-hk-sim-na`).
2. Create `<rule_id>.md` with the frontmatter + body explaining
   "what / why / how to apply / how to verify."
3. Run `python D:\Workspace\qa-harness\01-system\03-tools\check_rule_drift.py --requirements-dir D:\Workspace` to confirm it parses.
4. At next retro, decide if it's a promotion candidate.

## Promoting a rule (when 2 projects share it OR retro decides)

See `D:\Workspace\qa-harness\01-system\11-rule-promotion.md` section "How to promote".
