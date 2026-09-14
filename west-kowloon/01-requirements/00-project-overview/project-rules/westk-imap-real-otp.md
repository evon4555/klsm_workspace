---
rule_id: westk-imap-real-otp
title: SIT 已不再接受固定 OTP 111111；必须走 IMAP 拿真验证码
scope: project-candidate
created: 2026-05-27
origin: incident 2026-05-27 — fixed 111111 stopped working on forgot-password
applies_to: [西九]
candidate_for_promotion: unknown
promoted_to: null
promoted_at: null
---

## Rule

For any test that needs an email OTP on the 西九 SIT environment, **do
NOT hard-code `111111`** as the verification code. Fetch the real OTP
from the inbox via `02-automation/04-tools/imap_otp_poller.py`:

```python
from test_automation.tools.imap_otp_poller import fetch_latest_otp
otp = fetch_latest_otp(since=datetime.now(timezone.utc) - timedelta(minutes=2))
```

## Why

Before 2026-05-27, SIT accepted `111111` as the universal OTP — every
test used it. On 2026-05-27 that backdoor was removed silently and a
batch of forgot-password tests started failing with OTP rejected. The
real-IMAP path was always intended; the fixed code was a leftover.

See memory `project_sit_otp_regression_2026_05_27` and
`project_west_kowloon_otp_via_imap` for the full audit trail.

## How to apply

- Any new `.feature` step that needs an OTP: use `fetch_latest_otp`.
- Any existing step that still has `111111`: replace.
- Throttle: same mailbox supports ~30s between requests (Aliyun limit).
- ALIMAIL_PASSWORD env var is required.

## Aliyun corp-mail config (merged in from westk-otp-via-imap, 2026-06-03)

The 西九 test email is `evan.wang@antank.com`, hosted on Aliyun corp
mail企业版. To poll OTPs:

| Setting | Value |
|---|---|
| IMAP host | `imap.qiye.aliyun.com:993` SSL |
| Network | TCP 公网可达 (no VPN) |
| Username | `evan.wang@antank.com` |
| Password | **客户端独立密码** (generated in Aliyun mail 后台 → 安全设置; NOT the web login password) |
| Password env var | `ALIMAIL_PASSWORD` (user-level; `tools/imap_otp_poller.py` has winreg fallback) |
| Sender to expect | `public@antank.com` |
| Subject filter | **must match `验证码`** (same mailbox also gets monitoring alerts) |
| OTP regex | `验证码[:：]\s*(\d{6})` (note the full-width colon) |
| OTP TTL | 20 minutes |
| Same-mailbox throttle | **30 seconds between sends** (server-side; multiple OTP-touching cases must serialise with ~35s gap) |

### Aliyun IMAP quirks

`SEARCH FROM "x@y"` returns `BAD` from this server — the poller works
around by fetching the last 30 messages and Python-filtering instead
of relying on IMAP SEARCH.

## Coverage today

Integrated in `02-automation/04-tools/update_evidence.py`:

- `run_tc004` (duplicate-email OTP)
- `run_tc034`, `run_tc055` (login OTP)

Not yet integrated (still using `fake_xxx@126.com` placeholder, which
can't receive real OTP):

- `run_tc001`, `run_tc005`, `run_tc006`, `run_tc035`, `run_tc057`

To enable these, the team must decide a test-email strategy: either
re-route to a real `evan.wang+caseN@antank.com` aliases (Aliyun supports
`+` addressing), or use a dedicated test mailbox per case. Until then
those cases stay NA / known-Fail.

## How to verify

`grep -rn "111111" automation/` should return zero hits in step
definitions or page objects (test data files may legitimately use it).

`python -c "from test_automation.tools.imap_otp_poller import fetch_latest_otp; print(fetch_latest_otp(timeout=5))"` — should error "no OTP within 5s" cleanly (not crash on auth), confirming the env / password is wired.

## Promotion candidate?

**Unknown today.** Other projects may use different IMAP servers / OTP
backends. When 马会 or 标品 lands, see whether they ALSO need real-OTP
fetching — if yes, promote the **pattern** (fetch real OTP via IMAP)
to qa-system as a general "production-only OTP" baseline, but **keep
the Aliyun-specific config above project-scoped** because each project
has its own mailbox infrastructure.
