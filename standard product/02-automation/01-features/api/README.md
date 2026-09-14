# API Features

API scenarios must use Behave plus Python `requests` against real backend
endpoints.

Batch Session Configuration API scenarios are runnable and must generate
per-case API evidence PNG/JSON files in the runtime screenshot manifest.

For write/update cases, `success=true` from the write endpoint is not enough.
The scenario must read back the changed record or field and evidence must show
before value where available, expected value, actual value, and PASS/FAIL
assertion.
