# Test Design

Status: QA2 review passed; Test Manager review package is awaiting sign-off.

`test-cases-priority-booking-c-end-optimization.*` has been generated because
`../02-analysis/requirement-consolidation-priority-booking-c-end-optimization.md`
was signed off by the Test Manager on 2026-07-15.

QA2 review:

- `./.iterations/qa2-review-priority-booking-c-end-optimization-r1.md`
- Result: Pass

Human review package:

- `../04-test-case-review/test-case-review-priority-booking-c-end-optimization.md`
- `../04-test-case-review/test-case-review-priority-booking-c-end-optimization.docx`
- Status: Awaiting Test Manager sign-off

Signed design decisions:

- Generate the new test cases from the 2026-07-14 business flow.
- Use `../02-analysis/requirement-analysis-detail-priority-booking-c-end-optimization.md` as the detailed signed-scope analysis companion.
- Use `../02-analysis/previous-version-impact-reference.md` and the 2026-06-25 workbook/screenshots as required references.
- Include `Partner Benefits` sync/view/unbind coverage where it supports project-page validation.
- Use first-8-digit bank-card validation and display the validation validity period.
- Hide the cart icon before public sale.
- Exclude checkout-page "priority qualification used" display.
- Exclude dedicated multilingual / fallback matrix this round.
- Apply the ticket-type split rule for Admission ticket and seat-selection ticket where purchase, checkout, inventory, payment, or downstream behavior can differ.
- Yellow-highlight changed cells or rows in the xlsx and add comments explaining the reason where supported.
