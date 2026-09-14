# CHANGE - SSO Test Design

## 2026-07-13

- Created initial SSO test design from signed requirement consolidation.
- Added `test-cases-sso.md` with 24 SIT cases using the project
  `TestCase_Template.xlsx` column order.
- Generated `test-cases-sso.xlsx` by cloning the official West Kowloon workbook
  template and swapping in the test case data.
- Scope is limited to the signed first-round execution target:
  `http://127.0.0.1:6080/login`.
- Existing login-registration SSO cases `SIT-TC-WEB-AUTH-014` and
  `SIT-TC-WEB-AUTH-039..041` remain unchanged and are referenced only as
  regression impact context.

## Next Step

- Run QA2 review under `03-test-design/.iterations/`.
- After QA2 pass and any required revisions, prepare Test Manager sign-off under
  `04-test-case-review/`.
