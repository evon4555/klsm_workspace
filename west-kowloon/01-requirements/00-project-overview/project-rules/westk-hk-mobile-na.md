---
rule_id: westk-hk-mobile-na
title: 大陆测试环境不能验 HK 手机号 / SMS — 标 Deferred HK
scope: project-permanent
created: 2026-05-26
origin: 西九 has HK-mobile flows but the harness runs from mainland
applies_to: [西九]
candidate_for_promotion: no
promoted_to: null
promoted_at: null
---

## Rule

Test cases targeting HK SIM cards / HK mobile registration / HK SMS
delivery cannot be exercised end-to-end from the mainland test
environment. Mark them:

- xlsx Status column: **`Deferred`** + yellow row highlight
- Comments: **"Defer HK verification — needs on-site HK SIM"**
- features/ scenario: tag with **`@na`** + skip via environment.py

Do NOT delete the case; the requirement is real, just not testable
from the current infra.

## Why

西九 is a Hong Kong client; the public website supports HK mobile +
SMS OTP. The mainland-hosted SIT environment routes SMS through a
China-side gateway that cannot deliver to +852 numbers. Mobile +
SMS flows therefore require an HK-side tester or a real HK SIM in
a mainland phone, neither of which the automation harness has.

See memory `project_west_kowloon_hk_specific_features`.

## How to apply

For any case whose preconditions or steps involve:

- HK country code (`+852`)
- HK SIM-only SMS OTP
- HK mobile-app deep links

mark Status=Deferred + add the scenario to
`D:\Workspace\west-kowloon\02-automation\01-features\ui_e2e\antank_documented_na.feature` with `@na @mobile`
tags.

## How to verify

`maintenance_scan.py` after a new xlsx should show 0 drift for these —
they should stay @na, not get promoted to real automation.

## Promotion candidate?

**No** — `scope: project-permanent`. This is a 西九-specific quirk
(HK customer, mainland infra). 马会 (also HK) might hit the same
pattern, but the rule should still stay project-bound because the
**workaround** depends on the mainland-test-env setup, which is
arrangement-specific. If 马会 ever shares the exact same env, copy
this rule into 马会's project-rules/ rather than promote.
