# Translation Quality Review — 银行卡优先购 v2 新增 — zh-CN → en

| Field | Value |
|---|---|
| Source artifact | `../test-cases-bank-card-priority-purchase.{md,xlsx}` (zh, v2 rows BPP-046..048) |
| Target artifact | `../en/test-cases-bank-card-priority-purchase.xlsx` (en, v2 rows BPP-046..048) |
| Reviewer | QA2 (AI) — review-translation-quality skill |
| Review Date | 2026-06-29 |
| Verdict | **Pass with revisions** (3 Medium style consistency issues, fix in EN v2-rev) |

## Summary

- Total items compared: 3 (BPP-046, BPP-047, BPP-048 — only the v2-new rows)
- Findings: 0 Critical / 0 High / 3 Medium / 0 Minor
- Recommendation: produce EN v2-rev fixing the 3 Medium style drift items, then ship.

## Findings

### Critical / High

None. No semantic drift, no lost identifier, no added or dropped content. Partner A Diamond carried in both Test Data and Steps columns. Mock data (user1, 2026-08-01 10:00, "30 min") preserved verbatim. Counter terminology ("counter" not "quota/count") followed.

### Medium (style consistency with v1 EN)

| Location | Issue | Source (zh) | Target (en, current) | Suggested Fix |
|---|---|---|---|---|
| BPP-046 Steps 2, 4, 6 | "进入结算" rendered as **"Enter checkout"**, but v1 EN consistently uses **"Proceed to checkout"** (BPP-015: "Proceed to checkout") | "时间在公售窗口内进入结算" / "同样在窗口内进入结算" / "等 2 秒后进入结算" | "Enter checkout within the public-sale window" / "Enter checkout within the window again" / "Wait 2 seconds and enter checkout" | Replace 3 occurrences of "Enter checkout" / "enter checkout" → "Proceed to checkout" (verb-noun phrase, matching v1) |
| BPP-047 Steps 2, 4, 6 | "userN 进入结算" rendered as **"user1 enters checkout"** (declarative, 3rd person) — but v1 EN never uses third-person subject + present-simple for steps; it uses **"As user1, proceed to checkout"** (8 occurrences in v1) | "user1 进入结算" ×3 | "user1 enters checkout" ×3 | Replace 3 occurrences with **"As user1, proceed to checkout"** (imperative + actor prefix, matching v1 style and glossary § Style Rules) |
| BPP-048 Step 4 | Same as above + uses "enter checkout" (vs "proceed to checkout") | "user1 进入测试演出 → 加入购物车 → 进入结算" | "user1 enters Test Show → Add to Cart → enter checkout" | "**As user1, navigate to Test Show → Add to Cart → proceed to checkout**" |

### Minor

None.

## Glossary Used (consistent with project glossary)

| Source term | Target rendering | Notes |
|---|---|---|
| 合作方甲 钻石 | Partner A Diamond | Carried in Steps + Test Data ✓ |
| 优先购 | priority-purchase | adj form ✓ |
| 优先购权益 | priority-purchase benefit | not "priority benefit" ✓ |
| 优先购次数 | priority-purchase counter | not "quota" / "times" ✓ |
| 凭证 | credential | ✓ |
| 凭证失效时间 / 凭证失效时刻 | credential expiry / credential expiry time | not in glossary; reasonable rendering |
| 公售 | public sale | ✓ |
| 普通价 | standard price | ✓ |
| 弱提示 | soft prompt | ✓ |
| 不打断 / 非阻塞 | non-blocking | ✓ |
| 命中 / 不命中 | hits / miss | ✓ |
| 次数耗尽 | counter exhausted | from glossary "counter exhausted / counter at zero" ✓ |
| 加入购物车 | Add to Cart | ✓ |
| 进入结算 | **Proceed to checkout** | **3 occurrences in BPP-046/047/048 wrote "Enter checkout" instead — Medium fix** |
| 测试演出 | Test Show | ✓ |
| 王一凡 | 王一凡 | Names preserved in Chinese per glossary ✓ |

**New glossary candidates** (worth promoting to project glossary if recur):
- 进入结算 → Proceed to checkout — recurring; should add to translation-glossary.md
- 凌晨跨日 → midnight rollover — used twice in BPP-046; add to glossary
- 凭证失效时间 → credential expiry time — used multiple places; consistent rendering

## Recommendation

- **Decision**: Pass with revisions
- **Reason**: No semantic drift, identifiers and mock data fully preserved. The 3 Medium findings are all the same root cause — I drafted the EN Steps using my own paraphrase instead of pattern-matching v1 EN style. The fix is mechanical (string replacement); ship after fix.
- **Fix path**: Run a single update pass on EN xlsx that performs:
  1. "Enter checkout" → "Proceed to checkout" (case-sensitive, 3 cells in BPP-046)
  2. "user1 enters checkout" → "As user1, proceed to checkout" (3 cells in BPP-047)
  3. "user1 enters Test Show → Add to Cart → enter checkout" → "As user1, navigate to Test Show → Add to Cart → proceed to checkout" (1 cell in BPP-048)
- **Promote to project glossary**: add 进入结算 / 凌晨跨日 / 凭证失效时间 to `00-project-overview/translation-glossary.md` so the next translator doesn't repeat this drift
- **Follow-up Owner**: QA1 (me) — apply fixes immediately, no re-review needed (mechanical, scope tiny)

## Post-fix audit (2026-06-29, after fixes applied)

After applying the 3 documented fixes, I ran a regex sweep for any
remaining `\buser\d+\s+(verb)` patterns and found **1 additional miss
I overlooked in the initial r2 review**: BPP-048 Step 1 `user1 logs in`
(same root cause). Fixed in the same pass — now reads `Log in as user1`.

Final state after all fixes:
- BPP-046 Steps: 3 "Enter checkout" → "Proceed to checkout"
- BPP-047 Steps: 3 "user1 enters checkout" → "As user1, proceed to checkout"
- BPP-048 Steps: 1 "user1 logs in" → "Log in as user1"; 1 "user1 enters Test Show ... enter checkout" → "As user1, navigate to Test Show ... proceed to checkout"

Project glossary updated with 3 new term entries.

**Process lesson recorded**: my initial r2 review was driven by the 8-check
framework + manual diffing, but I missed the BPP-048 Step 1 because I was
looking at the "common pattern" (proceed to checkout) and not at a wider
3rd-person-subject pattern. Future translation reviews should run a regex
sweep against `\b<actor>\s+(verb)\b` as a sanity check, not rely solely on
eyeballing.
