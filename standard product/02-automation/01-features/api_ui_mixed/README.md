# API + UI Mixed Features

Mixed scenarios must use:

1. Python `requests` for all setup and business-action steps.
2. Playwright only for the final UI state check.
3. A single `@mixed` automation-type tag.

Do not tag the Test Case ID. The full `SIT-TC-...-NNN` ID belongs at the
start of the Scenario name and is the canonical mapping key. The
`api_ui_mixed` folder name is a legacy folder name only; new tags should use
`@mixed`.
