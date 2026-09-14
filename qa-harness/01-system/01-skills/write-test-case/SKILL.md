---
name: write-test-case
description: Use this skill to write structured QA test cases from requirements, test strategy, risk review notes, user flows, API documentation, UI design, defect history, or release scope. It generates executable test cases with preconditions, test data, steps, expected results, evidence requirements, priority, and coverage categories.
---

# Write Test Case

## Purpose

Generate test cases that are executable, traceable, evidence-friendly, and aligned with business risk.

The goal is not to create many cases. The goal is to cover the right risks with clear steps and observable expected results.

## Inputs

Use any available input. Open every source layer the project provides:

- Requirement
- Test strategy
- Requirement risk review
- Acceptance criteria
- User flow
- API or UI details
- **Mindmap** (website-level master + per-requirement narrow captures, if used by the project)
- **PRD or functional specification** — read the specific feature section; large PRDs are usually split by area
- Figma / design references
- Existing defects
- Regression scope
- Data and permission rules
- Project-level constraints (e.g., HK-only features unreachable from the test team's environment)

If information is missing, state assumptions and create open questions.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../05-evidence-standard.md`
- `../../07-source-authority.md` — **consult before treating any source as definitive**
- `../../templates/test-case-template.md`

## Workflow

1. Confirm the project's source authority order from `project-context.md`. Read the authoritative source first; reference sources after. Apply the project's gap rule (e.g., PRD-fills-gap) for items appearing in only one source.
2. Summarize the feature and test objective using the authoritative source.
3. Identify coverage categories needed.
4. Generate cases for main flow first.
5. Add negative, boundary, data, permission, integration, regression, and anti-abuse cases.
6. Assign priority based on business risk.
7. Define preconditions and test data.
8. Write clear steps and observable expected results.
9. Mark evidence required for important steps.
10. For in-scope features that the current team cannot execute (e.g., HK-only features for a mainland team, SSO pending product decision, provider sandbox not ready), **author the case and mark it Deferred** with reason and prerequisite assumptions. Do not skip authoring.
11. List open questions and assumptions. If two sources disagree on scope, surface it as an open question, do not unilaterally pick.
12. If the test case set has a derived artifact (xlsx, etc.), regenerate it; note in revision history.

## Coverage Categories

Consider:

- Main business flow
- Alternative flow
- Negative scenario
- Boundary value
- Permission and role behavior
- Data state and data consistency
- Error handling
- Integration behavior
- Compatibility
- Regression impact
- Non-functional risk where relevant

For West Kowloon Website scopes that touch ticketing, cart, checkout, payment,
discount, refund, wallet, order detail, or related regression behavior, apply
the project ticket-type split rule from `project-context.md`: consider
`Admission ticket` (门票) and `seat-selection ticket` (座票) as separate flows.
Generate separate cases when behavior, data, inventory/seat locking, pricing,
payment, discount eligibility, order detail, wallet, refund, or downstream
Charisma handling can differ. If one ticket type is not applicable, record the
explicit `NA` rationale in Coverage Notes rather than leaving the missing flow
implicit.

## Output Format

### Project Template Precedence

If the project provides its own test case template (e.g., `<project>/01-requirements/01-source-documents/02-templates/TestCase_Template.xlsx` — see `project-context.md` § Template Usage Rules), the output must be **a clone of the template** with only the data swapped in:

- Use its column set, names, and order. Do not add columns (e.g., do not invent an "Evidence Required" column). Do not remove columns. If a column seems missing, raise it with the user — do not silently add.
- **Preserve all visual formatting**: header fill colors, header text color, font family + size + weight, cell borders, column widths, row heights, freeze panes, merged cells.
- Execution-result columns (Actual Result, Status, Execution Date, Executed By, Screenshots, Comments/Remarks) stay present but blank at design time.
- **Defaults follow the sample row only.** A cell gets a default value only if the template's sample row has it filled in. If the sample leaves a cell blank (e.g., Environment), leave it blank — header tags in parentheses like `(SIT/UAT/PROD)` or `(Pass/Fail)` are valid-value lists, not defaults.
- **Content format follows the sample row's style** (numbered lists for steps and expected results, single-line for IDs, etc.).
- Apply matching column structure to **both** the markdown table and the derived `.xlsx`.

**xlsx regeneration procedure** (do not skip — guessed styling is wrong):

1. `shutil.copy(template_path, target_path)` so the output starts as a byte-level copy of the template.
2. Open the copy. Capture per-column styles from the sample data row (font / fill / border / alignment / number_format / protection) via `copy.copy()` on each.
3. Clear the sample row's *values* (keep styles).
4. Write each real data row, applying the captured per-column styles cell by cell.

Do **not** create a fresh `openpyxl.Workbook()` and rebuild — you will guess colors/fonts/widths wrong and lose theme / named-style / conditional-formatting state.

The default structure below is only for projects without a custom template. Override it whenever the project's template exists.

### Default Structure

Use this structure:

```markdown
# Test Cases

---

## [SECTION] Scope Summary

- Feature:
- Requirement:
- Risk level:
- Assumptions:

---

## [SECTION] Test Case List

| Case ID | Title | Priority | Coverage Category | Preconditions | Test Data | Steps | Expected Result | Evidence Required |
|---|---|---|---|---|---|---|---|---|
| TC-001 |  | P0 / P1 / P2 / P3 | Main flow |  |  | 1.  |  | Yes / No |

---

## [SECTION] Coverage Notes

- Main flow:
- Negative:
- Boundary:
- Permission:
- Data:
- Integration:
- Regression:

---

## [SECTION] Open Questions

| Question | Impact | Owner |
|---|---|---|
|  |  |  |
```

## Case Writing Rules

- Each case should verify one clear scenario.
- Expected results must be observable.
- Steps should be specific enough for another QA to execute.
- P0 or P1 cases should usually require evidence.
- Do not hide assumptions inside test steps.
- If a scenario is **in scope but unexecutable** in the current environment, mark the case Deferred with a reason and prerequisite assumptions (e.g., "Deferred — HK-side verification; requires HK SIM"). Do not delete it.
- If a scenario is genuinely **out of scope** per the authoritative source, do not author it; record the decision in the requirement risk review's Resolved Questions instead.
- Avoid duplicate cases unless they cover different data, roles, or risk.
- For West Kowloon ticketing-related scopes, do not collapse `Admission ticket`
  and `seat-selection ticket` into one case unless the case explicitly states
  why one flow is representative or why the other flow is `NA`.
- For revisions to an existing case set: revise in place, add a Revision
  History row at the top of the file, regenerate any derived artifact (xlsx,
  etc.), and preserve the previous approved version's format and writing style.

## Description Wording Rules

The **Test Case Description** column must be **one grammatical sentence, one scenario, one primary check**. Extra checkpoints belong in Expected Result; extra scenarios belong in new cases. The following punctuation patterns are banned inside Description because each is a symptom of two cases smashed into one row.

### Banned pattern 1 — `;` as an "and also verify X" glue

Semicolon connecting two subject-verb clauses signals **two separate cases**. Split — do not punctuate.

- ❌ `Verify that the Order page enforces a MOBILE OTP (SMS) step for guest users using the Mobile contact method; logged-in users skip OTP.`
- ❌ `Verify that the Order page enforces an EMAIL OTP step for guest users (gates submission); logged-in users continue to skip OTP entirely.`
- ✅ Case A: `Verify that a guest user using the Mobile contact method is required to complete a mobile SMS OTP step before the Order page allows submission.`
- ✅ Case B: `Verify that a logged-in user is not required to complete an OTP step on the Order page.`

**Tell:** if the description names two subject categories with different behaviors (guest vs logged-in, admin vs user, EMAIL vs MOBILE), split — always.

### Banned pattern 2 — ` - ` (space-hyphen-space) as a sentence connector

Hyphen is only allowed inside compound words (`opt-in`, `logged-in`, `3-language`, `email-branch`). A hyphen with spaces around it is being used as an em-dash / "namely" connector; it belongs to prose, not to a test case field.

- ❌ `Payment success page (email branch) - 3-language registration-success message + "Back to Home" button`
- ✅ Description: `Verify the email-branch payment success page renders correctly in all 3 languages.`
- ✅ Expected Result (each element as its own bullet, so Description stays one sentence and does not need `and` to chain independent predicates):
  1. The localized registration-success message renders.
  2. A "Back to Home" button is present.
  3. The page renders equivalently under each supported language.

### Banned pattern 3 — `+` as a checkpoint concatenator

Each `+` inside Description is a separate assertion. Those assertions belong in the Expected Result column as separate bullets, or in a new case if they are independent verifications.

- ❌ `Verify the upgrade branch when the chosen contact method is EMAIL: opt-in checked + payment success converts the guest temp account into a registered account; the chosen EMAIL is stored as the account contact, mobile field is empty; the order is linked.`
- ✅ Description: `Verify that, when a guest chooses EMAIL as the contact method and keeps opt-in checked, a successful payment upgrades the temp account into a registered account.`
- ✅ Expected Result (separate bullets, not smashed into Description):
  1. Temp account is converted to a registered account.
  2. The chosen EMAIL is stored as the account contact.
  3. The mobile field is empty.
  4. The order is linked to the new registered account.

If any of those bullets is orthogonal to the primary check (e.g., order-linking is a separate integration path), promote it to its own case.

### Banned pattern 4 — `:` (colon) introducing a checkpoint list, and `and` chaining multiple independent verifications

A colon followed by "the X renders … and the Y routes …" is the same pathology in different clothes: the writer is enumerating checkpoints inside Description instead of splitting them into Expected Result bullets. `and` used to connect two independently observable predicates has the same effect.

- ❌ `Verify the payment-success page when conversion happened via email: the 3-language registration-success message renders with the selected email placeholder filled in, and the Back to Home button routes to the homepage.`
- ✅ Description: `Verify that, after a guest is upgraded via the email branch, the payment-success page shown to that guest is the localized post-registration page.`
- ✅ Expected Result (each bullet independently observable):
  1. The 3-language registration-success message renders in the currently selected language.
  2. The message's email placeholder is filled with the email the guest just chose.
  3. A "Back to Home" button is present.
  4. Clicking "Back to Home" navigates to the homepage.

**Rule of thumb for `and`:** if you can rewrite the sentence as two "Verify X. Verify Y." statements that each stand on their own, they are two checkpoints — move them to Expected Result (or split into two cases if orthogonal).

### Positive rule

If you cannot state the case in **one grammatical sentence** without reaching for `;`, ` - `, `+`, `:`, or a checkpoint-chaining `and`, that is the signal to split the case or to move detail into Expected Result. Never punctuate your way around it.

### Reader test (apply before saving any Description)

Read the Description aloud, in isolation, without looking at Steps or Expected Result. Ask:

1. **What single thing is being verified?** If you can name only one, good. If you catch yourself listing "and this, and this, and this", you have violated the rule.
2. **Whose behavior is under test?** If the answer is two different subject categories (guest vs logged-in, EMAIL vs MOBILE, admin vs user), split into two cases.
3. **How many things must be true for this case to pass?** If the count is > 1 and the truths are independently observable, move each to Expected Result as its own bullet.

If any of these tests fails, the Description is not yet acceptable regardless of how tidy the punctuation looks.

## Test Steps Wording Rules

Every numbered step is **one atomic action performed by one persona in one branch**. Do not fold two actions, two personas, or two branches into a single case's Steps column. The same pathologies banned in Description are banned in Steps.

### Banned pattern S1 — role/branch switch mid-Steps

If Steps contain "As X …" and later "As Y …", or an "As GUEST" line followed by an "As LOGGED-IN" line, that is **two cases jammed into one**. Split — always.

- ❌ Steps in one case:
  ```
  1. As GUEST: choose Mobile; observe OTP field.
  2. Send OTP via SMS; enter wrong/correct OTP.
  3. As LOGGED-IN: confirm no OTP field on order page.
  ```
- ✅ Case A (guest branch), Steps:
  ```
  1. Open the site as an unauthenticated guest.
  2. Start a new order.
  3. Select Mobile as the contact method.
  4. Enter a valid mobile number.
  5. Click "Send OTP".
  6. Enter the OTP received via SMS.
  7. Submit the order.
  ```
- ✅ Case B (logged-in branch), Steps:
  ```
  1. Log in as a registered user.
  2. Start a new order.
  3. Select Mobile as the contact method.
  4. Enter a valid mobile number.
  5. Submit the order.
  ```

**Tell:** any step whose first token is a persona/role change ("As GUEST:", "As LOGGED-IN:", "Switch to admin:") is a split signal, not a step.

### Banned pattern S2 — `;` chaining two actions inside one numbered step

A numbered step is atomic. If you write "step N: do X; then do Y" you have described two actions — number them separately.

Pure action-action example:

- ❌ `1. Click "Send OTP"; wait 60 seconds; click "Resend".`
- ✅
  ```
  1. Click "Send OTP".
  2. Wait 60 seconds.
  3. Click "Resend".
  ```

Common combined violation (chain + assertion, hits both S2 and S4):

- ❌ `1. As GUEST: choose Mobile; observe OTP field.`
- ✅ Split the `;` chain **and** move the observation to Expected Result (Steps hold actions only, per S4):
  - Steps: `1. Select Mobile as the contact method.`
  - Expected Result: `The OTP field appears on the Order page.`

### Banned pattern S3 — `wrong/correct`, `valid/invalid`, `X/Y` slashes inside a step

A slash between two data variants ("enter wrong/correct OTP", "submit with valid/invalid captcha") crams two scenarios into one step. Each variant is its own case (or, if variants of the same negative-flow case, its own numbered step with its own Expected Result).

- ❌ `2. Send OTP via SMS; enter wrong/correct OTP.`
- ✅ Split into two cases, each with a single deterministic outcome:
  - Case (negative): `Enter an OTP that does not match the delivered SMS OTP. → Order submission is blocked with OTP error.`
  - Case (positive): `Enter the OTP received via SMS. → Order submission proceeds.`

Slashes are only acceptable when they name a single data field with two equivalent representations (e.g., `dd/mm/yyyy`), never as "either of these two scenarios".

### Banned pattern S4 — assertion inside a step

Steps are actions. Assertions live in Expected Result. If a step says "observe X", "confirm Y", or "verify Z", the step is describing what to check, not what to do.

- ❌ `3. As LOGGED-IN: confirm no OTP field on order page.`
- ✅ Steps: `1. Log in ... 2. Start an order and select Mobile ...`
  Expected Result: `The OTP field is not shown on the Order page for logged-in users.`

An "observe" step is allowed only when the observation is a prerequisite for the next action (e.g., "Wait for the OTP email to arrive, then …"). Anything checked purely as a pass/fail criterion belongs in Expected Result.

### Positive rules for Steps

1. One action per numbered step. If you need `;`, `,` (as "then"), `and` (chaining two distinct UI actions), or `/`, split into more steps. `and` is only acceptable when the two joined items name the same atomic action from two angles (e.g., "Click Save and confirm the toast" is still two — split it).
2. One persona for the whole case. Persona is set in the first step (login state) and never changes.
3. One branch/data-variant per case. Positive path and negative path are separate cases.
4. Steps describe what a human does. Assertions describe what a human observes — they live in Expected Result.
