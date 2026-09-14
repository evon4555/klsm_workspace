# Test Case Review Template

This template is for QA2(AI) review artifacts under
`03-test-design/.iterations/`. It is not the Test Manager sign-off form.
Human sign-off artifacts belong under `04-test-case-review/` and must have
paired `.md + .docx` files.

---

## [SECTION] Basic Information

- Review ID:
- Project:
- Feature:
- Requirement Link:
- Test Case Set:
- Author:
- Reviewer:
- Review Date:
- Review Result: Pass / Needs Revision / Reject

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

Summarize whether the test cases are sufficient for the requirement and risk level.

### [FIELD] Main Concern

-

### [FIELD] Required Action

-

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main business flow | Covered / Partial / Missing |  |  |
| Alternative flow | Covered / Partial / Missing |  |  |
| Negative scenario | Covered / Partial / Missing |  |  |
| Boundary value | Covered / Partial / Missing |  |  |
| Permission | Covered / Partial / Missing |  |  |
| Data state | Covered / Partial / Missing |  |  |
| Integration | Covered / Partial / Missing |  |  |
| Compatibility | Covered / Partial / Missing |  |  |
| Regression | Covered / Partial / Missing |  |  |
| Non-functional risk | Covered / Partial / Missing |  |  |

---

## [SECTION] Quality Checklist

- [ ] Each case maps to a requirement, risk, or business flow.
- [ ] Preconditions are clear and executable.
- [ ] Test data is defined.
- [ ] Steps are specific enough to execute.
- [ ] Expected results are observable.
- [ ] Priority matches business risk.
- [ ] Duplicate cases are removed or justified.
- [ ] Blocked or not-testable areas are documented.
- [ ] Regression impact is considered.
- [ ] Evidence requirements are clear.
- [ ] For v2+ case sets, added/modified rows preserve the previous approved
      version's format and writing style.

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Critical / High / Major / Minor |  |  |  |  |

---

## [SECTION] Final Decision

- Decision: Pass / Needs Revision / Reject
- Reason:
- Follow-up Owner:
- Due Date:
