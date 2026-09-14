---
rule_id: westk-source-authority
title: 西九 mindmap is the source of truth; PRDs are reference
scope: promoted
created: 2026-05-15
origin: mindmap-vs-PRD conflict on registration/login scope (2026-05-15)
applies_to: [西九]
candidate_for_promotion: yes
promoted_to: 01-system/07-source-authority.md#project-authority-declarations
promoted_at: 2026-06-03
---

This rule has been promoted to system scope. The active definition lives at:

→ [`01-system/07-source-authority.md`](D:\Workspace\qa-harness\01-system\07-source-authority.md) §
"Project authority declarations" — sub-section **West Kowloon Website**.

The body is kept here for git blame and audit trail. Do not edit; edit
the promoted location instead.

## Original body (frozen 2026-06-03)

For the 西九 Website project, the **mindmap** is the authoritative source
of scope and behaviour. Website-level PRDs in `01-source-documents/02-prd/` and change-package PRD slices under `01-input/03-prd/` are reference material
that provide additional context but do not override the mindmap.

**Why**: Confirmed by the user on 2026-05-15 in response to a
mindmap-vs-PRD conflict on registration/login scope. The mindmap
level-1 label `注册/登录（只支持邮箱）` directly contradicted
`在线购票 PRD §3` which described email + mobile + third-party.

**Apply**:
- mindmap authoritative; PRD reference
- PRD-fills-gap: items only in PRD are still in scope
- Mindmap "PRD 上没写" annotations: still in scope
- Mindmap narrowing labels vs PRD detail: go with mindmap sub-tree
