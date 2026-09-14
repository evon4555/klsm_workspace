# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs     : SIT-TC-WEB-AUTH-088 .. 093  —  Account Security / Change Password
#   Source  : 2026-06-10 PRD §修改密码 (new section added 2026-06-10)
#             03-test-design/test-cases-registration-login_2026-06-12.scope-clean-2026-06-16.xlsx
#             (sheet "Test Cases")
#   Module  : Website / Personal Center / Change Password
#
#   Status  : @na for now — the new gated change-password flow (old password ->
#             image CAPTCHA -> OTP -> new password focus-out -> auto-logout 1-3s)
#             may not yet be deployed in SIT as of 2026-06-12. Flip the @na
#             tags to @ui once the page is in SIT, and replace the generic
#             Given/Then with the real page-object steps.
# =============================================================================
Feature: Website 修改密码 / Change Password (SIT-TC-WEB-AUTH-088 .. 093)

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-088 Successful change-password flow (old -> CAPTCHA -> OTP -> new -> auto-logout)
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-089 Change password - wrong current password blocks submission
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-090 Change password - wrong or expired OTP blocks submission
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-091 Change password - OTP routing (email-only / mobile-only / both default email)
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-092 Change password - new password fails rule check on focus-out
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password
  Scenario: SIT-TC-WEB-AUTH-093 Change password - image CAPTCHA mandatory and validates
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  # ----- Mobile variants of the above (split 2026-06-12) ------------------------
  # HK SMS infra is out of reach for the mainland team; QA owner verifies manually.

  @na @change_password @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-110 Successful change-password flow (mobile OTP) - mobile variant of AUTH-088
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @change_password @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-111 Change password - wrong or expired mobile OTP blocks submission - mobile variant of AUTH-090
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability
