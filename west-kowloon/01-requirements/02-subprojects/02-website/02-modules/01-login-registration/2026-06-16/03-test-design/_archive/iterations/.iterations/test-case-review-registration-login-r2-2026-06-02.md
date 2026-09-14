# Test Case Review — registration-login (Round 2, 2026-06-02 change set)

Re-review after applying r1 revisions.

---

## [SECTION] Review Summary

- Overall result: **Pass**
- Findings: 0 Critical, 0 Major, 0 Minor
- Reviewer: AI (QA2 role)
- Main concern: (none — proceed to automation)

---

## [SECTION] Verification of r1 findings

| ID | Finding | Status |
|---|---|---|
| C1 | Module name on AUTH-078..087 | ✓ all 10 now `Website / Third-party Bind` |
| C2 | `[Open]` markers buried in expected | ✓ moved to Comments column on AUTH-083 / AUTH-085 |
| M1 | WhatsApp open question | ✓ AUTH-017/018 descriptions reference CHANGE.md Q2 |
| M2 | AUTH-079 placeholder wording | ✓ rewritten to behavior-describing form |
| M3 | AUTH-082 captcha refresh wording | ✓ steps now match AUTH-031/032 convention |

## [SECTION] Coverage check (sanity)

The 17 cases cover the 2026-06-02 PRD §3.2.2 update completely:

- OAuth main flow (modified existing): 7 cases (AUTH-017/018/059-063)
- Link Your Account UI / behavior (new): 10 cases (AUTH-078..087)
  - Email/Phone × New/Existing branches: 4 (AUTH-078..081)
  - Captcha: 1 (AUTH-082)
  - OTP send + retry: 1 (AUTH-083)
  - Terms checkbox: 1 (AUTH-084)
  - Email↔Phone mode switch: 1 (AUTH-085)
  - Country code + phone format: 1 (AUTH-086)
  - Already-linked skip: 1 (AUTH-087)

## [SECTION] Open Questions (tracked in CHANGE.md)

Same as r1; not blockers for Pass:
1. OTP wrong-code upper limit
2. WhatsApp inclusion in provider list
3. Email persistence across Email↔Phone switch
4. AUTH-079/081 exact masked-text UX copy

## [SECTION] Recommendation

Proceed to Phase C: write automation for these 17 cases.
