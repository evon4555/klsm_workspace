# 2026-07-18 - API Automation Evidence Readback

Trigger: Standard Product Batch Session Configuration API cases had dashboard
pass results but no per-case screenshot/evidence artifact.

Decision: API evidence must be case-level and human-readable. For write/update
flows, evidence must show real request metadata, write response, readback API,
before value where available, expected value, after value, and PASS/FAIL
assertion. For safe Y/N fields, set the field to the opposite value as a
precondition before executing the target update so the evidence demonstrates
the value changed.

Verification: Standard Product Batch Session Configuration run `190` passed
14/14 and generated API evidence PNG/JSON for `SIT-TC-STD-CONFIG-003` through
`SIT-TC-STD-CONFIG-011`.
