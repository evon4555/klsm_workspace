# Automation Demo Gate

Purpose: capture a short product demo from the Test Manager before automation
scripting starts.

This folder is used after the `04-test-case-review` document is reviewed and
signed. It is not an automation-script folder. It is an information-gathering
gate for the standard-product flow.

## Workflow

1. Test Manager reviews and signs the `04-test-case-review` document.
2. Test Manager adds a short walkthrough in this folder. The walkthrough may be
   a Word document with embedded screenshots, the markdown template, separate
   screenshot files, sanitized network notes, or a combination of these.
3. QA automation scans all demo evidence in this folder and reviews the
   walkthrough against the signed `03-test-design` test cases.
4. If key scenarios are missing, pause `05-execution` and return to
   `03-test-design` / `04-test-case-review` through the normal review gate.
5. If no scenario gap is found, create or update
   `05-execution/automation-assessment-batch-session-configuration.xlsx` from
   `01-source-documents/02-templates/AutomationAssessment_Template.xlsx`.
6. Test Manager reviews and signs
   `05-execution/automation-assessment-review-<scope>.docx`.
7. Only after that sign-off, QA automation updates the package documents and
   starts writing automation scripts.

## Rules

- Do not implement automation scripts from demo notes alone.
- Do not silently add new business coverage in `05-execution`.
- Any missing scenario discovered from the demo must be reflected in
  `03-test-design` first, then reviewed again if needed.
- Keep screenshots and notes sanitized. Do not store secrets, passwords,
  tokens, cookies, or private payloads.
- For this gate, a Word document with embedded screenshots is a valid primary
  demo input. Do not require screenshots to be duplicated into `screenshots/`.

## Expected Files

- `*.docx` - optional primary Test Manager walkthrough, including embedded
  screenshots.
- `automation-demo-walkthrough.md` - optional markdown walkthrough notes.
- `screenshots/` - optional numbered screenshots when images are not embedded
  in Word.
- `network/` - optional sanitized endpoint notes, if API behavior is visible.
