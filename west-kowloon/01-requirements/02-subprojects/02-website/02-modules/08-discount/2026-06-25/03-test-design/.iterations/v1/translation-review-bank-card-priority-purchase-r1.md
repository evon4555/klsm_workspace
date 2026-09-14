# Translation Quality Review — bank-card-priority-purchase — ZH → EN

| Field | Value |
|---|---|
| Source artifact | `03-test-design/test-cases-bank-card-priority-purchase.xlsx` (ZH, 45 cases, canonical) |
| Target artifact | `03-test-design/en/test-cases-bank-card-priority-purchase.xlsx` (EN v2) |
| Reviewer | QA2 (AI) — `review-translation-quality` skill |
| Review Date | 2026-06-27 |
| Verdict | **Pass with revisions** (1 Medium → fix; 3 Minor → log only) |

## Summary

- Total items compared: 45 cases × 6 fields (scenario / description / pre / steps / data / expected / comments) = ~270 cells with content
- Findings: **0 Critical / 0 High / 1 Medium / 3 Minor**
- Recommendation: **produce v3 EN xlsx** fixing the 1 Medium; Minor logged as project style guide entries

This review is itself the first self-application of `review-translation-quality` to a translation produced by the same AI that wrote the skill — proving the skill's "Mandatory After Any Translation" rule has teeth. v2 was substantially cleaner than v1 (which had 15+ defects across 4 categories), but the **identifier-preservation discipline was incomplete**: I fixed the partner qualifier in the Expected column but missed the Data column.

## Findings

### Critical (semantic defects)

_None._

### High (lost identifiers / drift)

_None._ The v1 → v2 fix pass eliminated the High-severity partner-qualifier issues in Expected. Identifier preservation in Steps / Description / Preconditions checked clean.

### Medium (style / terminology / awkwardness)

| Location | Issue | Source | Target | Suggested Fix |
|---|---|---|---|---|
| BPP-024 Test Data | Partner qualifier dropped in Data column | "原价 100；钻石 80；白金 90" | "Original 100; Diamond 80; Platinum 90" | "Original 100; Partner A Diamond 80; Partner A Platinum 90" |
| BPP-025 Test Data | Same | "VIP 70；甲钻石 80" | "VIP 70; Diamond 80" | "VIP 70; Partner A Diamond 80" |
| BPP-027 Test Data | Same | "甲钻石 80；白金不可用" | "Diamond 80; Platinum unavailable" | "Partner A Diamond 80; Partner A Platinum unavailable" |

**Root cause**: When fixing v1 I only audited the Expected column (where identifier loss was most user-visible). Data column has the same risk profile and should have been audited together. Glossary in v2 was implicitly built only from Expected fields.

### Minor (cosmetic / style)

| Location | Issue | Source | Target | Suggested Fix |
|---|---|---|---|---|
| BPP-014, BPP-020, BPP-021 Expected | "Flow is non-blocking" is slightly clunky English | "不打断" | "Flow is non-blocking" | Either "The flow is not interrupted" or just "Non-blocking" (matches QA jargon convention) |
| BPP-019 Expected line 3 | "Order proceeds normally" subtly differs from source (active vs passive) | "可正常下单" (the user CAN place the order normally) | "Order proceeds normally" (the order PROCEEDS normally) | "Order can be placed normally" — keeps user-as-subject |
| BPP-021 Expected line 3 | "Bind a Partner identity" silently adds "Partner" qualifier vs source | "弱提示「绑定身份可享优先购」" — source says just 「身份」 | "Soft prompt 'Bind a Partner identity to enjoy Priority Purchase' appears" | Either keep current (defensible — spec is about Partner identity context) or strip to match source: "Bind an identity..." |

## Glossary Built From This Review

Stable terms validated across all 45 cases (use these in future translations under this project):

| Source term | Target translation | Notes |
|---|---|---|
| 合作方甲 / 乙 / 丙 | Partner A / B / C | Letter mapping, never drop "Partner" |
| 钻石 / 白金 / 业主 / 普通 | Diamond / Platinum / Owner / Standard | When standalone in mock data, prefix with partner: "Partner A Diamond" not "Diamond" |
| 优先购 | Priority Purchase (title case in UI) / priority-purchase (lowercase hyphenated in body) | Title case when quoted as UI label; lowercase-hyphenated as an adjective |
| 优先购权益 | priority-purchase benefit | **Do NOT shorten to "priority benefit"** — has happened, blocks 4 cells |
| 优先购次数 | priority-purchase counter | "counter" not "quota", "count", or "times" |
| 我的权益身份 | My Benefit Identities | UI label, title case |
| 合作方会员 | Partner Member | When referring to the role / system |
| 凭证 | credential | "Credential expires in N days" for the formatted string |
| 加入购物车 | Add to Cart | UI action label |
| 公售 | public sale | "30 min before public sale" |
| 提前时间 | lead-time | hyphenated |
| 弱提示 | soft prompt | not "weak prompt" / "weak hint" |
| 不打断 / 非阻塞 | non-blocking | preferred; "Flow is non-blocking" is OK but "Non-blocking" is tighter |
| 命中 / 未命中 | hit / miss | verbs; "the user hits priority-purchase mode" |
| 扣减 | decrement | as verb: "is decremented" |
| 反转 | reverse | counter reverses |
| 联调验证 | integration verification | hyphenated |
| mid | mid | lowercase, technical key — keep as-is |
| 测试演出 | Test Show | mock event name |
| 绑定时间 | binding time | **NOT "bound-at time"** — invalid English |

Style rules:

- **Test Steps**: imperative mood ("Click Submit", "Enter the BIN", "Place a priority-purchase order")
- **Actor prefix in Steps**: when the actor differs from Preconditions or is the first reference, use "As <user>, ..."; otherwise omit
- **Expected Result**: declarative ("Card is shown", "Counter is decremented by 1", "Page loads successfully")
- **Field references inside quotes**: keep verbatim ("Credential expires in 7 days"), do not translate the formatted string

## Recommendation

- **Decision**: Pass with revisions
- **Reason**: 0 Critical / 0 High. 1 Medium (3 cells in Data column missing partner qualifier — same root cause, fix together). 3 Minor are style nits not worth blocking on; promote to project style guide for future translations.
- **Follow-up Owner**: QA1 (AI) — fix the 3 Data cells, regenerate xlsx, validate, ship v3
- **Promote to project glossary**: the Glossary table above should be saved at
  `west-kowloon/01-requirements/00-project-overview/translation-glossary.md`
  for reuse by any future translation in this project

## Self-Critique

- The v1 → v2 fix pass was reactive (responding to specific defects you called out) instead of systematic (running the 8 checks against ALL columns). The Data-column miss is a direct consequence.
- Next translation: build the glossary BEFORE translating, not after. Skill workflow step 1 should explicitly say "extract terminology from source first".
- This finding will be promoted to the skill: add a "Pre-translation glossary extraction" sub-step.
