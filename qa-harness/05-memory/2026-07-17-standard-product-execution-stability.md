# 2026-07-17 - Standard Product Execution Stability

Trigger: Batch Session Configuration runs failed intermittently from repeated
CAPTCHA login, mshow route blank pages, and missing per-case screenshot
mapping.

Decision: Standard Product Behave runs reuse one real API `requests.Session`
per run, seed Playwright UI cookies from that session when available, and keep
request capture enabled for no-write assertions. UI helpers must retry mshow
route recovery and recheck expected row data before marking a schedule page
ready. Runtime evidence is stored in
`case-screenshot-manifest-run-<run_id>.json`.

Verification: Runs `183`, `184`, `185`, `186`, and `187` all passed the full
14-case suite. After API readback evidence was added, run `190` passed the full
14-case suite and is the current fixed execution-review source. Run `189`
errored on a transient UI navigation connection close, while API assertions and
API evidence generation completed.
