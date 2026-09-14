# RAG Retrieval

Package: `10-SSO/2026-07-13`

Source PRD:

- `01-input/03-prd/AnTank-consumer-unified-SSO-业务专版.20260617.pdf`
- `01-input/03-prd/AnTank-consumer-unified-SSO-design.20260617.zh-CN.pdf`

Retrieval goal:

- Find similar existing Zentao/current-repository cases, scenarios, and local
  tools before generating test cases for unified SSO.
- Decide whether to reuse, update, or create cases so the new SSO package does
  not duplicate or silently overwrite prior login-registration coverage.

Candidate retrieval sources:

- Current repository package `01-login-registration/2026-06-16`.
- Current repository execution notes for registration/login SSO Deferred/NA
  cases.
- Local SP mock project `C:\Users\klsm\Downloads\westk-consumer-sso-sp-mock`.
- ZenTao story `4305` URL, if authenticated content is later exported.

Decision log:

| Existing case/source | Similarity reason | Decision | Notes |
|---|---|---|---|
| `SIT-TC-WEB-AUTH-014` in `01-login-registration/2026-06-16` | SSO identity synchronization smoke; previously NA because no SSO environment was available. | create | Use as historical risk reference only. New package needs detailed IdP/SP OAuth flow cases. |
| `SIT-TC-WEB-AUTH-039..041` in `01-login-registration/2026-06-16` | WestK SSO three-jump scenarios: BU already logged in, BU not logged in, direct access. | create | Keep old cases unchanged unless sign-off instructs a versioned update. New cases should map to Checking API, authorization callback, token exchange, and SP session behavior. |
| `requirement-risk-review-registration-login.md` | Identifies prior SSO scope as pending environment/product decision and captures integration risk. | reuse | Reuse as adjacent-module risk context in consolidation. |
| `westk-consumer-sso-sp-mock` local Vue app | Provides `/login`, `/callback`, `/status`, `/logout-callback`, and `/debug` routes plus authorize/checking/register/logout/session-sync client behavior. | reuse | Treat as optional execution helper, not as a requirement source. It can support later manual/API-assisted SSO testing after scope sign-off. |
| ZenTao story `4305` | Primary work item URL captured in package. | pending | Story body requires authenticated export before it can be used as source text. |

Decision values:

- `reuse`: no new case needed; link to the existing case or tool.
- `update`: maintain an existing case because the requirement changed.
- `create`: add a new case because current coverage is missing.

Conclusion:

- The existing login-registration package proves that SSO was known but blocked
  by missing environment/scope. It does not cover this new unified SSO
  requirement.
- After consolidation sign-off, create a dedicated SSO integration case set
  under `10-SSO/2026-07-13/03-test-design` and link back to old AUTH SSO cases
  only as regression/impact references.
