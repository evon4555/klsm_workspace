# Login And Registration

Scope:

- login
- registration
- OTP and email verification
- forgot password
- third-party login where it belongs to authentication

New module-specific changes should go directly under dated folders in this
module, for example `2026-06-23`.

Source rule:

- Treat `..\..\01-source-documents` as the PRD/source-input history.
- Treat this folder as the generated login/registration working view.
- For each dated PRD update that affects login/registration, create a separate
  dated package directly under this module instead of adding another version into
  a shared top-level changes package.
- Each dated package should include `package.md` and the standard numbered
  output folders: `01-input`, `02-analysis`, `03-test-design`,
  `04-test-case-review`, `05-execution`, `06-execution-review`, and
  `07-release-feedback`.
- For future case generation, record whether the change updates existing cases
  or creates new login/registration cases under the dated package.

Best-practice reference:

- `2026-06-16/02-analysis/api-first-ui-best-practice-auth009.md`
  records the API-first + final UI validation pattern for
  `SIT-TC-WEB-AUTH-009`.
