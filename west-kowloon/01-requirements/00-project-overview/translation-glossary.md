# West Kowloon Project — Translation Glossary

Authority for all translations under this project. Maintained by QA team.
Each entry should be used consistently across all translated artifacts
(test cases, consolidation docs, test reports, review notes).

When `review-translation-quality` is run against a new translation in
this project, this glossary is the **first reference** for terminology
consistency.

| Source (zh-CN) | Target (en) | Notes |
|---|---|---|
| 合作方甲 / 乙 / 丙 | Partner A / B / C | Letter mapping. **Never drop "Partner"** prefix. |
| 钻石 / 白金 / 业主 / 普通 | Diamond / Platinum / Owner / Standard | When standalone in mock data, **prefix with partner**: "Partner A Diamond" not bare "Diamond". |
| 优先购 | Priority Purchase (title case in UI label) / priority-purchase (lowercase hyphenated as adjective) | "Priority Purchase opens..." (UI) vs "priority-purchase benefit" (body) |
| 优先购权益 | priority-purchase benefit | **Do NOT shorten to "priority benefit"** — recurring defect. |
| 优先购次数 | priority-purchase counter | "counter" not "quota" / "count" / "times". |
| 我的权益信息 / 我的权益身份 | Partner Benefits | UI label, title case. Use this for the account benefit page or section name. |
| 合作方会员 | Partner Member | Role / system. |
| 凭证 | credential | "Credential expires in N days" for the formatted UI string. |
| 凭证有效期 | credential validity (days) | |
| 凭证失效时间 / 凭证失效时刻 | credential expiry time | Used in expiry-decision rules. Added 2026-06-29 from 08-discount BPP-046. |
| 凌晨跨日 | midnight rollover | The 00:00 day-boundary transition. Added 2026-06-29 from 08-discount BPP-046. |
| BIN 校验 | BIN validation | UI tag. |
| 加入购物车 | Add to Cart | UI action label. |
| 购物车 | cart | |
| 进入结算 | Proceed to checkout | NOT "Enter checkout" — promoted from 08-discount v2 EN translation review 2026-06-29. |
| 公售 | public sale | "30 min before public sale". |
| 公售时间 | public-sale time | |
| 提前时间 | lead-time | hyphenated. |
| 提前购 | early purchase | |
| 专享价 | exclusive price | |
| 普通价 | standard price | |
| 弱提示 | soft prompt | NOT "weak prompt" / "weak hint" / "soft hint". |
| 不打断 / 非阻塞 | non-blocking | preferred; "Flow is non-blocking" OK but "Non-blocking" is tighter. |
| 命中 / 未命中 | hit / miss | as verb: "the user hits priority-purchase mode". |
| 扣减 | decrement | as verb: "is decremented"; counter is decremented by 1. |
| 反转 | reverse | "counter is reversed" / "refund reverses the counter". |
| 联调 | integration testing | |
| 联调验证 | integration verification | hyphenated. |
| 绑定 / 解绑 | bind / unbind | as verb. "Binding succeeds" / "Click Unbind". |
| 绑定时间 | binding time | **NOT "bound-at time"** — invalid English. |
| 多语言 | multilingual / i18n | "i18n" in technical context; "multilingual" in business text. |
| 标准产品 | standard product | the SaaS baseline product. |
| 标准产品后台 | standard-product backend | hyphenated as adjective. |
| 后台 | admin backend | when standalone. |
| 个人中心 | My Account | UI section. |
| 全额退款 | full refund | |
| 部分退款 | partial refund | |
| 次数耗尽 | counter exhausted / counter at zero | |
| mid | mid | lowercase, technical key — keep as-is. |
| 二次确认 | confirmation dialog | for an "are you sure?" modal. |
| 测试演出 | Test Show | mock event name across BPP cases. |
| 测试经理 | Test Manager | role. |

## Names (do NOT translate)

| Original | Render as |
|---|---|
| 王一凡 | 王一凡 (signature lines preserve Chinese characters) |
| 阮敏慧 | 阮敏慧 |
| 西九 / 西九文化区 | West Kowloon / West Kowloon Cultural District |
| 卡里司马 / 上海卡里司马科技 | (project-internal; keep Chinese in records) |

## Style Rules (Test Case fields)

- **Test Steps**: imperative mood. "Click Submit" / "Enter the BIN" / "Place a priority-purchase order".
- **Actor prefix in Steps**: use "As <user>, ..." when the actor differs from Preconditions or is the first reference; otherwise omit.
- **Expected Result**: declarative. "Card is shown" / "Counter is decremented by 1" / "Page loads successfully".
- **UI label strings inside quotes**: keep verbatim ("Credential expires in 7 days") — do not paraphrase the formatted string.
- **Mock data**: preserve test users (guest1, user1..5), card numbers, prices, dates verbatim.
- **Partner identifiers**: always carry the partner letter ("Partner A Diamond" not bare "Diamond"), even in compact Data column cells.

## Maintenance

- When a new term enters the project (PRD, mindmap, design), add it here BEFORE translating.
- When a target rendering is changed mid-project, update this file FIRST, then back-fix earlier translations.
- This file is project-wide; for harness-wide style rules, see
  `D:\Workspace\qa-harness\01-system\01-skills\review-translation-quality\SKILL.md`.

## Provenance

- Bootstrapped 2026-06-27 from
  `02-modules/08-discount/2026-06-25/03-test-design/.iterations/translation-review-bank-card-priority-purchase-r1.md`
  (translation review found Medium-severity identifier drift; glossary
  promoted to project level to prevent recurrence).
- 2026-06-29: added `进入结算 / 凌晨跨日 / 凭证失效时间` after
  `translation-review-bank-card-priority-purchase-r2.md` caught
  3 Medium style drifts in EN v2 (BPP-046..048) — "Enter checkout"
  vs "Proceed to checkout" + 3rd-person subject vs "As <user>, ..."
  imperative pattern. Drift root cause: I drafted EN by paraphrase
  instead of pattern-matching v1 EN style — promoting these terms
  to glossary so the next translator can grep first.
