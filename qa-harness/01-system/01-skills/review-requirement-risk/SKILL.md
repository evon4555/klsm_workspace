---
name: review-requirement-risk
description: Use this skill when reviewing a software requirement, user story, feature brief, design note, API change, or release scope for QA risk before test strategy or test case design. It identifies ambiguity, business risk, dependency risk, data risk, permission risk, edge cases, regression impact, and non-functional concerns.
---

# Review Requirement Risk

## When To Use (Conditional)

In the West Kowloon / Antank pipeline, this skill is **not invoked per
requirement package by default** — the per-package risk/scope/open-question
work is absorbed by [`consolidate-requirement`](../consolidate-requirement/SKILL.md).
Invoke this skill as a standalone artifact only when:

- The consolidation doc's risk_level is **High** and stakeholders beyond
  QA need a dedicated risk writeup.
- New project kickoff in an unfamiliar domain (regulated industry,
  novel integration, new payment rail).
- Production-bug retrospective requires a backwards-looking risk review
  feeding [`analyze-production-bug`](../analyze-production-bug/SKILL.md).

For routine requirement packages, **do not** produce a separate risk
review file — let the consolidation doc carry the risk content.

## Purpose

Act as a QA risk reviewer before detailed test design starts.

The output should help humans decide whether the requirement is clear enough, what risks need clarification, and what test scope should be considered.

## Inputs

Use any available input. Open every source layer the project provides — do not stop at the first one that looks complete:

- Requirement text
- User story
- Acceptance criteria
- Design or UI description (Figma, screenshots, mockups)
- **Mindmap** — both website-level master and per-requirement narrow captures, if the project uses them
- **PRD or functional specification documents** — read the specific section that covers the feature; large PRDs are usually split by feature area, so the relevant section may not be in the file you opened first
- API or integration description
- Business goal
- Change scope
- Known constraints
- Existing defect or incident context

If important information is missing, proceed with assumptions and list open questions. Mark assumptions explicitly so a reviewer can see what's inferred vs. what's sourced.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../07-source-authority.md` — **read this before resolving any apparent conflict between sources; do not unilaterally pick a winner**

Do not copy these documents into the output. Use them as operating rules.

## Workflow

1. **Identify source layers** available for this requirement: PRD(s), functional spec, mindmap (master + narrow), Figma, wiki, tickets, prior artifacts. Confirm the project's source authority order from `project-context.md` § Source Authority. If not declared, ask the user before proceeding.
2. **Read each source.** Treat the authoritative source as primary; treat reference sources as supplementary. Apply the project's gap rule (e.g., PRD-fills-gap) for items that appear in only one source.
3. Summarize the requirement in business terms.
4. Identify unclear or missing information. If two sources disagree, surface the conflict as an Open Question with both sides quoted; do not silently pick a winner.
5. Analyze risks by category.
6. Identify edge cases and negative scenarios.
7. Identify regression impact.
8. Identify non-functional concerns.
9. Recommend whether the requirement can move to test strategy.

## Risk Categories

Review at least these areas:

- Business flow
- User role and permission
- Data creation, update, deletion, and consistency
- Boundary values
- Error handling
- Integration and third-party dependency
- Compatibility
- Performance
- Security
- Regression impact
- Operations and monitoring

## Output Format

```markdown
# Requirement Risk Review

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| YYYY-MM-DD | name | concise summary of what changed and why; cite the source that drove the change |

(For first draft, one entry. Subsequent revisions add rows; do not create v2 files.)

---

## [SECTION] Requirement Summary

- Business goal:
- Main change:
- Affected users:
- Affected systems:
- Source basis: (list authoritative source and reference sources; cite project's authority rule)

---

## [SECTION] Resolved Questions (Closed Since Previous Revision)

| Source That Resolved | Previous Question | Resolution |
|---|---|---|
|  |  |  |

(Empty on first draft. Populate when a later source layer answers an earlier Open Question.)

---

## [SECTION] Open Questions

| Priority | Question | Why It Matters | Owner | Source |
|---|---|---|---|---|
| High / Medium / Low |  |  |  | which source raised this / left it open |

---

## [SECTION] Risk Review

| Risk Area | Risk | Impact | Suggested Test Focus |
|---|---|---|---|
| Business |  |  |  |
| Data |  |  |  |
| Permission |  |  |  |
| Integration |  |  |  |
| Compatibility |  |  |  |
| Performance |  |  |  |
| Security |  |  |  |
| Regression |  |  |  |

(Add project-specific risk areas as needed: anti-abuse / captcha, authentication mode confusion, localization, deferred-verification flows, etc.)

---

## [SECTION] Edge Cases And Negative Scenarios

-

---

## [SECTION] Recommendation

- Requirement readiness: Ready / Needs Clarification / Not Ready
- Recommended risk level: Low / Medium / High
- Next action:
```

## Quality Rules

- Be specific. Avoid generic risks that do not help test design.
- Separate requirement questions from test ideas.
- If a risk affects release decision, mark it as High.
- If information is missing, state the assumption rather than inventing certainty.
- The final recommendation must be usable as input to test strategy.
- When a previously open question is answered by a newly captured source, **move it to Resolved Questions** in the same revision pass; do not leave answered items in the active Open Questions list.
- When two sources disagree, the Open Question must quote both sides; the recommendation must not unilaterally pick a winner.
