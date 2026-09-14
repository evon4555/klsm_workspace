# Source Authority And Conflict Resolution

---

## [SECTION] Purpose

QA work draws on multiple input sources for the same feature: PRD, functional specification, mindmap, Figma design, wiki / Confluence pages, tickets, prior artifacts. These sources frequently disagree, omit information, or change at different speeds.

This document defines how QA should treat sources when they disagree, when one is silent, or when authority is unclear.

The purpose is to prevent two failure modes:

1. **AI confabulation:** unilaterally picking a source as "the truth" without product confirmation, then generating outputs that look authoritative but rest on an arbitrary choice.
2. **Source drift:** the team uses one source consistently while another diverges, leading to features built, tested, or released against stale or incomplete information.

---

## [SECTION] Principles

#### [POINT] 1. Source Authority Is Project-Specific

There is no universal hierarchy that places PRD above mindmap, or mindmap above PRD. Different projects designate different sources as their primary truth.

Each Kasi project must declare its source authority order in its `project-context.md`. AI must consult that declaration before drawing scope conclusions.

#### [POINT] 2. Declare The Authority Order Per Project

In `project-context.md`, record:

- Which source is **authoritative**: when sources disagree, this one wins by default.
- Which sources are **reference**: read for context; do not override authoritative.
- Rule for items appearing only in non-authoritative sources: **include automatically** (e.g., PRD-fills-gap) or **ask the user**.
- Treatment of authoritative-source annotations that flag missing-in-other-source items (e.g., a mindmap node annotated "PRD 上没写"): treat as deliberate scope confirmation; in scope.
- Treatment of authoritative-source narrowing labels that contradict reference source detail (e.g., a mindmap label "只支持邮箱" vs PRD listing email + mobile + third-party): consult the user; do not pick a side.

#### [POINT] 3. Surface Conflicts; Do Not Pick Sides Unilaterally

When AI finds two sources disagree:

- Quote both sides with source paths.
- Suggest interpretations (outdated, phase-narrowing, different scope, error).
- Ask the user to resolve.

AI must NOT silently delete cases, risks, or open questions based on its own judgment of which source wins. A "looks invalid given source X" conclusion is a question, not a decision.

#### [POINT] 4. Revise In Place With Revision History

When source-of-truth content shifts (e.g., a mindmap is captured after a risk review was first drafted from PRD only), revise the affected artifact in place and add a Revision History section:

```markdown
## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| YYYY-MM-DD | name | concise summary of what changed and why |
```

This preserves the audit trail without cluttering the workspace with v1 / v2 / v3 files. Industry standard for non-regulated dry-run / iteration work.

#### [POINT] 5. Track Resolved Open Questions Separately

When a previously open question is answered by a newly captured source, move it from the active Open Questions list to a "Resolved Questions" subsection that names the source that resolved it. This preserves context for later reviewers.

#### [POINT] 6. Deferred Verification Is A First-Class Status

When a test case or risk item is **in scope but unexecutable** in the current environment (HK-only feature for a mainland team; SSO pending product decision; provider sandbox not yet provisioned), mark it **Deferred** with a reason — not deleted, not converted to "skip".

Deferred items must declare:

- The blocking reason.
- The party who can execute (HK-side QA; product after decision; etc.).
- Prerequisite data or environment.

#### [POINT] 7. Re-Generate Derived Artifacts After Source Changes

If a binary or derived artifact (xlsx, docx, image export) is generated from a markdown master, regenerate it on every revision and note the regeneration in the Revision History. Mismatched master + derived is a common source of execution-time confusion.

---

## [SECTION] Workflow Integration

#### [POINT] Requirement Intake

1. List every available input source: PRD(s), functional spec, mindmap, Figma, wiki, tickets, prior artifacts.
2. Confirm the source authority order is recorded in `project-context.md`. If not, ask the user before generating QA outputs.
3. Extract content from each source into a structured form (e.g., mindmap PNG → `mindmap-extract.md`).

#### [POINT] Risk Review And Test Case Design

1. Consume the authoritative source first.
2. Cross-check reference sources for additional detail and to detect conflicts.
3. Apply the project's gap rule (e.g., PRD-fills-gap) for items present in a non-authoritative source only.
4. Surface unresolved conflicts as Open Questions; do not decide unilaterally.

#### [POINT] Re-Work When A New Source Layer Arrives

1. Re-read the authoritative source after the new input.
2. Compare against existing artifact.
3. Revise in place; add Revision History entry; move resolved Open Questions to a Resolved Questions subsection; record new gaps.
4. Do not create vN files.
5. Regenerate derived artifacts (xlsx, exports); note in Revision History.

---

## [SECTION] Example Declaration (West Kowloon Website)

Recorded in `D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-rules\`:

- Authoritative: mindmap (`02-subprojects\02-website\01-source-documents\01-mindmap\` master + per-change-package narrow captures under `02-modules\<module>\<yyyy-mm-dd>\01-input\02-mindmap\`).
- Reference: Website-level PRDs in `02-subprojects\02-website\01-source-documents\02-prd\` (cover the whole Website); requirement-narrow PRD slices, if any, under `01-input\03-prd\`; Figma; IT-PMO documents.
- Items only in PRD: in scope (PRD-fills-gap rule, set 2026-05-15).
- Items only in mindmap and annotated "PRD 上没写": in scope (deliberate inclusion).
- Mindmap narrowing labels that contradict PRD detail: take sub-tree content as truth; treat the label as guidance overriding PRD wording.
