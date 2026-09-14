# Batch Session Configuration Artifacts

The timestamped pytest/JUnit artifacts in this folder are retained only as an
audit trail of an invalidated local prototype.

They must not be counted as valid API/UI/Mixed automation execution because
they did not use:

- Behave as the test-management runner.
- Python `requests` against real backend APIs.
- Playwright against the real application UI.

The current valid status is recorded in `latest-execution-record.md`.
Dashboard run `194` passed all 14 current-scope cases and is linked to
`case-screenshot-manifest-run-194.json`.
