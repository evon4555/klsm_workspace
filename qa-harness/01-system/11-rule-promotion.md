# Rule Promotion — Project ↔ System Sync

How rules and standards move between **project-specific** and
**system-wide** scope, so the harness stays clean as projects surface
new conventions over time.

The risk this doc addresses: 西九 surfaces a rule (e.g. "always use IMAP
real OTP, never fixed 111111"). Without a policy, that rule either
(a) stays buried in a 西九 doc and the next project re-discovers the
same lesson, or (b) gets unilaterally promoted to `01-system` but doesn't
actually apply universally, polluting the standards for everyone.

This doc defines a **lifecycle** for each rule.

---

## [SECTION] Three rule scopes

| Scope | Lives in | Applies to |
|---|---|---|
| **system** | `01-system/*.md` standards, `01-system/01-skills/`, `01-system/02-templates/` | every project, no opt-out |
| **project-candidate** | `<project>/01-requirements/00-project-overview/project-rules/<rule-id>.md` | this project only; under review for promotion |
| **project-permanent** | `<project>/01-requirements/00-project-overview/project-rules/<rule-id>.md` | this project only; explicitly tagged "non-universal" |

Every project rule starts as **project-candidate**. After enough
evidence, it either gets **promoted to system** or marked
**project-permanent**.

---

## [SECTION] Rule file frontmatter (mandatory)

Every `project-rules/<rule-id>.md` must start with:

```markdown
---
rule_id: westk-imap-real-otp
title: West Kowloon SIT no longer accepts fixed OTP 111111
scope: project-candidate              # or: project-permanent | promoted
created: 2026-05-27
origin: 西九/Website (incident 2026-05-27)
applies_to: [西九]                    # add other projects as they adopt it
candidate_for_promotion: yes          # yes | no | unknown
promoted_to: null                     # filled when promoted; e.g. 01-system/05-evidence-standard.md
promoted_at: null
---

(body — describe the rule, why it exists, how to apply, how to verify)
```

Without the frontmatter the rule is **invisible to the drift-detector**
and can't be promoted. Required for ALL rules.

---

## [SECTION] When to promote — 3 triggers

A rule moves from `project-candidate` → `system` when ANY of these are true:

### Trigger 1: Adoption in 2+ projects

Once the same rule (same `rule_id`, or recognisably the same intent)
exists under 2 different projects' `project-rules/` directories, it's
no longer project-specific by evidence. Promote.

Detected by: `01-system/03-tools/check_rule_drift.py`

### Trigger 2: Compliance / regulatory / security

If a rule touches privacy law, financial regs, accessibility law, or
core security baselines, promote on sight regardless of adoption count.
A single project's compliance team noticing "GDPR DSR response 30-day"
is enough — every project under our umbrella needs to comply.

### Trigger 3: Explicit retrospective decision

In a release retrospective (skill: `qa-retrospective-coach`), the team
may decide "lesson X from this release should be system-wide." Honour
that decision; rename the rule from `westk-X` to neutral wording and
promote.

---

## [SECTION] When NOT to promote — `project-permanent`

Keep at project scope when:

- The rule is environment-specific (e.g. "西九 SIT URL is
  `anticket.lengliwh.com`")
- The rule depends on customer-specific contracts / NDAs
- The rule is a workaround for one customer's quirky backend that no
  other project hits

In those cases, set the frontmatter:

```yaml
scope: project-permanent
candidate_for_promotion: no
# add a one-line reason in the body
```

The drift-detector will then skip it.

---

## [SECTION] How to promote (the act)

1. Pick the right home in `01-system`:
   - Workflow / process rule → add a section in `02-qa-workflow.md` or `08-our-pipeline.md`
   - Evidence / status rule → `05-evidence-standard.md`
   - Quality gate → `04-quality-gates.md`
   - New methodology → create a skill under `01-system/01-skills/<rule-id>/SKILL.md`
   - Source authority / hierarchy rule → `07-source-authority.md`
   - Change-management rule → `10-change-management.md`

2. Move the rule body into the chosen home. Adjust wording to be
   project-neutral (drop "西九-specific" framing).

3. In the **original** `<project>/01-requirements/00-project-overview/project-rules/<rule-id>.md`,
   keep a stub:

   ```markdown
   ---
   rule_id: westk-imap-real-otp
   scope: promoted
   promoted_to: 01-system/05-evidence-standard.md#otp-handling
   promoted_at: 2026-06-15
   ---

   This rule was promoted to system scope. See the link above.
   (Body kept for git blame and project audit trail — DO NOT delete.)
   ```

4. Add a memory entry recording the promotion (so future-AI doesn't
   accidentally re-promote or contradict):

   ```
   project_<rule-id>_promoted_<date>.md
   ```

5. Run the drift-detector again — should show zero duplicates for that
   rule_id now.

---

## [SECTION] How to detect candidates — the drift detector

`01-system/03-tools/check_rule_drift.py` scans every project's
`project-rules/` directory and reports:

| Bucket | What |
|---|---|
| **Duplicate** | Same `rule_id` appears under 2+ projects → strong promotion signal |
| **Stale candidates** | `scope: project-candidate` not touched in >90 days → time to either promote or downgrade to permanent |
| **Promotion-tagged** | `candidate_for_promotion: yes` rules — review at next retro |
| **Orphans** | Files with no frontmatter or no `rule_id` — fix metadata |

Run weekly or before each release. Output goes to
`artifacts/rule_drift_report.md`.

---

## [SECTION] What this doc does NOT change

- Existing system standards (`01-07*`, `08`, `10`) keep their place
- Existing skills and templates keep their place
- The 12-step workflow is unaffected — this is meta-process about HOW
  the standards evolve, not the standards themselves

---

## [SECTION] See also

- `02-qa-workflow.md` step 12 — Retrospective + improvement (where
  promotion decisions are made)
- `08-our-pipeline.md` — the team's concrete pipeline (a "promoted" doc)
- `10-change-management.md` — how requirement changes (different from
  rule changes) are versioned
- memory `project_qa_harness_pipeline_and_change_mgmt` — the prior
  meta-architecture decision that motivated this doc
