# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs    : SIT-TC-WEB-AUTH-015, 016, 033  —  Website / Forgot Password
#   Source : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#            03-test-design\test-cases-registration-login.xlsx
#   Page   : {antank_url}/websitehtml/index.html#/forget
#   Tags   : @forgot = the module; @ui = pure-UI test mode.
#
#   The reset form mirrors registration: email + 动态码 (OCR captcha) +
#   "Get Code" + Verification Code (fixed SIT OTP 111111) + new password.
#   TC015 resets the test account back to its config/users.yml password so
#   the suite stays repeatable.
# =============================================================================
Feature: Website 忘记密码 / Forgot password (SIT-TC-WEB-AUTH-015, 016, 033)

  # TC015 — manual step: open / email + captcha / OTP / new password / submit
  @ui @forgot
  Scenario: SIT-TC-WEB-AUTH-015 Registered user resets the password
    Given the Website forgot-password page is open
    When  I complete the password-reset form with a valid email and OTP
    Then  the password reset succeeds

  # TC016 — manual step: try an unregistered email on the reset form
  @ui @forgot
  Scenario: SIT-TC-WEB-AUTH-016 Invalid reset inputs are blocked
    Given the Website forgot-password page is open
    When  I request a reset code for an unregistered email
    Then  the password reset is blocked with a validation message

  # TC033 — manual step: submit the reset form with no / wrong 动态码
  @ui @forgot
  Scenario: SIT-TC-WEB-AUTH-033 Forgot password requires the 动态码 captcha
    Given the Website forgot-password page is open
    When  I submit the password-reset form with a missing 动态码
    Then  the password reset is blocked with a captcha error

  # TC043 — request an OTP (A), wait past cooldown, request resend (B), then
  # confirm: A != B; submitting A is rejected; B is the operative OTP.
  # Documented-only in automation: SIT enforces a Get Code rate limit > 5 min,
  # so this is not repeatable inside the current same-session automated run.
  # Keep the deterministic requirement traceable here and execute manually
  # unless a controlled wait/test fixture is added.
  @ui @forgot @na
  Scenario: SIT-TC-WEB-AUTH-043 OTP resend invalidates the previous OTP
    Given the Website forgot-password page is open
    When  I request an OTP, wait past the resend cooldown, and request a new OTP
    Then  the previous OTP is rejected and only the latest OTP is accepted

  # TC073 — Added 2026-06-01 after SIT confirmed the direct-reset model on
  # 2026-05-23. Verifies the
  # forgot-password direct-reset OTP flow end-to-end + asserts no
  # temp-password email is ever sent. OTP retrieval via IMAP per
  # project_west_kowloon_otp_via_imap memory.
  @ui @forgot @na
  Scenario: SIT-TC-WEB-AUTH-073 Forgot password direct-reset OTP flow end-to-end
    Given the Website forgot-password page is open
    And   an active registered account with a known old password
    When  I complete the direct-reset flow with email + 动态码 + OTP from IMAP + a new password
    Then  no temp-password email is sent at any step
    And   the old password is rejected on login
    And   the new password is accepted on login
