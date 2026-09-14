# Test Case Review — registration-login (Round 1, 2026-06-02 change set)

Review scope: the 17 cases changed by the 2026-06-02 change set
(modified: AUTH-017, 018, 059-063 / added: AUTH-078-087).

Reviewed against `02-qa-workflow.md` § Test case review criteria +
`templates/test-case-template.md` + existing case format conventions.

---

## [SECTION] Review Summary

- Overall result: **Needs Revision**
- Findings: 2 Critical, 3 Major, 1 Minor
- Reviewer: AI (QA2 role)
- Main concern: module-name convention drift — 10 new cases break the
  `Website / <SubModule>` pattern that the other 71 cases follow.

---

## [SECTION] Critical findings (must fix before Pass)

### C1 — Module name convention break (AUTH-078..087)

**Existing 71 cases** use the `Website / <SubModule>` prefix:
- `Website / Native Registration`
- `Website / Registered Login (password mode)`
- `Website / Forgot Password`
- `Website / Third-party Login`  ← used by AUTH-017/018/059-063 (after user edit)
- `Website / SSO`
- ...

**My 10 new cases** (AUTH-078..087) use `Authentication / 3rd-Party Bind`
— breaks the pattern. The "Authentication" / "3rd-Party Bind" terms appear
nowhere else in the workbook.

**Fix**: rename module on AUTH-078..087 to `Website / Third-party Bind`
(matches both the `Website /` prefix AND the "Third-party" terminology
that AUTH-017/018/059-063 already use).

### C2 — Open-question marker buried in expected (AUTH-083, AUTH-085)

PRD §3.2.2 explicitly marks "OTP 失败是否有上限" as `待确认`. AUTH-083
mentions this in expected as `[Open] Whether there is a hard cap...`,
but it's at the END of the expected block — easy to miss during execution.
Same for AUTH-085 about email-persistence-across-switches.

**Fix**: lift `[Open]` markers into a separate **`Open Questions`**
note OR into the `Comments` column where reviewers see them earlier.
At minimum, add to the case-level CHANGE.md (already done — open
questions section).

---

## [SECTION] Major findings (should fix)

### M1 — Provider mismatch unaddressed (AUTH-017, 018, 059-063)

PRD §3.2.2 example providers: "Google, WhatsAPP等". Figma 2026-06-02
buttons: Google, Facebook, TikTok, X, WeChat (5 providers, NO WhatsApp).
CHANGE.md flagged this as open question #2 — fine.

But the modified case **descriptions** still say "Run for each of the 5
providers (Google, Facebook, X, TikTok, WeChat)". This commits to the
figma version of the list. If WhatsApp ends up being in scope, all
five existing per-provider cases (AUTH-059..063) would need a sibling
case for WhatsApp.

**Fix**: in AUTH-017/018 descriptions, add a sentence "See open question
in CHANGE.md re: WhatsApp inclusion." Don't change the 5 per-provider
cases yet — wait for resolution.

### M2 — AUTH-079 expected wording (placeholder leak)

AUTH-079 expected says "your <Provider> account will be linked to:
**<masked email/account>**" — `<masked email/account>` is a placeholder.
The figma shows blue notice. PRD spec is "提示:'检测到该邮箱/手机号已注册...'"
but doesn't give exact masked-email format.

**Fix**: change to "your <Provider> account will be linked to the
existing account (masked email/phone shown for confirmation)" — describe
the behavior, not the literal text, until UX writes the final string.

### M3 — AUTH-082 captcha refresh mechanism (incomplete)

Says "click the captcha image to refresh". Confirm with existing AUTH-031
/ AUTH-032 (captcha cases) which describe the same UI — they use the
phrase "refresh by clicking image". Match wording.

**Fix**: change "Click the captcha image to refresh" to "Click the 动态码
image to request a fresh captcha" (mirrors AUTH-031 wording).

---

## [SECTION] Minor findings

### Min1 — AUTH-085 "field-clear behaviour" still open

Last line says "[Open] confirm with PM whether email is preserved across
switches." This is fine for now but ensure it makes it into the project's
open-questions tracker (= the CHANGE.md). It does — open question #3
already covers this. Leave as-is.

---

## [SECTION] What the user already fixed (positive findings)

- AUTH-017 module renamed from "Authentication / Third-Party Login"
  to "Website / Third-party Login" — matches existing convention ✓
- (other modified cases not re-checked at character level; user said
  "format made consistent")

---

## [SECTION] Recommended action

Apply **all 5 Critical+Major findings**. Re-review (r2) after revise.

---

## [SECTION] Open Questions (do not block Pass — track in CHANGE.md)

1. OTP attempt-count / time-window upper limit (PRD §3.2.2 待确认)
2. Provider list final: 5 (figma) or 6 (figma + WhatsApp from PRD)
3. Email value persistence across Email↔Phone mode switch
4. AUTH-079 / AUTH-081 masked text — exact UX copy
