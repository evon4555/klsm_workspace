---
rule_id: westk-prd-layout
title: 西九 PRD 拆 3 个 PDF；注册登录 spec 在 在线购票 §3 不在 V1.1
scope: project-permanent
created: 2026-05-15
origin: dry-run risk review missed multiple registration features because read V1.1 instead of 在线购票
applies_to: [西九]
candidate_for_promotion: no
promoted_to: null
promoted_at: null
---

## Rule

The 西九 Website PDF baseline is split across **3 PDFs** under
`D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\02-prd\2026-05-14\`.
Later PRD drops may appear as Markdown under dated sibling folders such as
`2026-06-16`. Use this map to find the right baseline file before reading:

| File | Scope (verified 2026-05-15) |
|---|---|
| `国际版标准官网 V1.0_总览.pdf` | Overall product overview, user types (registered / guest / visitor), top-nav and entry points. Has registration/login bullet list but not the detailed flow. |
| `国际版标准官网 V1.1.pdf` | Detailed feature spec for **membership, ticket detail pages, account security/deletion, refund/exchange, transfer**. Does NOT contain the main registration/login flow. |
| `国际版标准官网 - 在线购票.pdf` | Online ticketing flow. **§3 注册登录 is where the detailed registration/login spec lives.** Sections: 3.1 用户注册 (email/mobile), 3.2.1.1 OTP login, 3.2.1.2 password login, 3.2.2 第三方平台授权登录 (Google/WhatsApp 等), 3.2.3 游客模式, 3.2.4 西九会员 SSO (待讨论), 3.3 引导/强制登录节点. |

## Why this matters

If asked anything about registration / login spec, go to **`在线购票.pdf`
§3 first**, not V1.1. The 2026-05-15 dry-run risk review and test cases
appeared to miss this section, which is why several PRD-described
features were absent from generated outputs:

- verification-code login auto-registration
- 5-min guest countdown popup
- SSO three-jump scenarios

## How to apply

When reading PRD for a 西九 feature:

1. Identify which functional area the feature touches.
2. Pick the right PDF per the table above.
3. If unsure, **read 在线购票.pdf first** — it's the most under-read of
   the three despite holding the most critical spec (registration /
   login / payment).
4. Use PyMuPDF to extract (see [`westk-prd-pymupdf`](./westk-prd-pymupdf.md)).

## Promotion candidate?

**No** — `scope: project-permanent`. This map is specific to 西九's
3-file split. Other projects (马会 / 标品) will have their own PRD
layouts and this map won't apply.

If 马会 / 标品 have a similar "PRD-split surprise" pattern, write a
sibling rule in their project-rules/; don't generalize this one.
