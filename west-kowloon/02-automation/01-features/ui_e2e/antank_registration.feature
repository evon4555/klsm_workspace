# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs     : SIT-TC-WEB-AUTH-001-006, 008  —  Website native registration
#   Source  : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#             03-test-design\test-cases-registration-login.xlsx
#             (sheet "Test Cases")
#   Module  : Website / Native Registration  +  Website / Privacy Policy
#   Page    : {antank_url}/websitehtml/index.html#/register
#
#   Tags    : @registration = the module (run the whole suite with this);
#             @ui           = pure-UI test mode (vs. future @hybrid Mixed-mode).
#   To run a single case, use the scenario name, e.g.
#             behave --name "SIT-TC-WEB-AUTH-005"
#
#   动态码      : a real image captcha — solved automatically by OCR with retry
#                 inside WebsiteRegistrationPage (mirrors website_login_page.py).
#   Verification Code (email OTP) : a fixed test value 111111 in SIT — no real
#                 inbox is needed, so the OTP-gated cases are fully automatable.
#   Pure UI     : the form is filled in the browser via Playwright; no API
#                 shortcut is used.
#
#   Note: TC004 is EXPECTED to fail — the product currently allows duplicate
#   registration of an already-registered email (a defect this case catches).
# =============================================================================
Feature: Website 注册 / Native registration (SIT-TC-WEB-AUTH-001-006, 008, 029-030, 042, 044, 045, 057)

  # TC001 — manual step: open / fill valid data / 动态码 / email OTP / consent / submit
  # UPDATED 2026-06-12 per 2026-06-10 PRD §用户邮箱/手机+密码注册:
  #   Flow is now gated 5-step: select email/mobile -> CAPTCHA -> OTP -> password
  #   (focus-out rule check) -> Submit. Workbook assertions are deterministic;
  #   page-object coverage can be expanded separately.
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-001 New visitor registers successfully
    Given the Website registration page is open
    When  I fill the registration form with brand-new valid account data
    Then  a new account is created and the visitor is signed in

  # TC002 — manual step: open / leave mandatory fields empty / submit
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-002 Empty mandatory fields block registration
    Given the Website registration page is open
    When  I submit the registration form with every field left empty
    Then  registration is blocked with a missing-field validation message

  # TC003 — manual step: open / enter invalid email + weak password / submit
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-003 Invalid email format is rejected
    Given the Website registration page is open
    When  I submit the registration form with an invalid email address
    Then  registration is blocked with an invalid-email validation message

  # TC004 — manual step: open / enter existing email + valid data / submit
  # EXPECTED TO FAIL: the product currently allows the duplicate registration.
  # UPDATED 2026-06-12 per 2026-06-10 PRD §用户邮箱/手机+密码注册 step 5.a.i:
  #   The duplicate-email block MUST surface one of these 3-language strings:
  #     zh-CN  该邮箱已注册，请登录或找回密码。
  #     zh-HK  此電子郵件已註冊，請直接登入或重設密碼。
  #     en     This email address is already registered. Please sign in or reset your password.
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-004 Duplicate email is rejected
    Given the Website registration page is open
    When  I submit the registration form with an already-registered email
    Then  registration is blocked with an existing-account message

  # TC005 — manual step: start registration / request OTP / enter wrong OTP / submit
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-005 Wrong email OTP cannot complete registration
    Given the Website registration page is open
    When  I submit the registration form with a wrong email verification code
    Then  registration is blocked with an OTP-error message

  # TC006 — manual step: request OTP / trigger resend repeatedly / observe timer
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-006 OTP resend follows a cooldown
    Given the Website registration page is open
    When  I request the email verification code
    Then  the resend control enters a countdown cooldown

  # TC008 — manual step: fill some fields / click Privacy Policy link / return
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-008 Privacy Policy link opens the policy
    Given the Website registration page is open
    When  I fill in a registration field and open the Privacy Policy link
    Then  the Privacy Policy content opens and the form data is preserved

  # TC029 — manual step: submit registration with no / wrong / correct 动态码
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-029 Registration requires the 动态码 captcha
    Given the Website registration page is open
    When  I submit the registration form with a missing or wrong 动态码
    Then  registration is blocked with a captcha error

  # TC030 — manual step: click the 动态码 image to refresh it
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-030 The 动态码 captcha refreshes on click
    Given the Website registration page is open
    When  I click the 动态码 image
    Then  a fresh 动态码 image is shown

  # TC042 — manual step: request OTP / immediately request resend within 60s
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-042 OTP resend within 60s is rejected
    Given the Website registration page is open
    When  I request the email verification code and immediately try to resend
    Then  the resend within 60s is rejected and the countdown stays visible

  # TC044 — manual step: enter mismatched password + confirmation / submit
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-044 Mismatched password and confirmation block registration
    Given the Website registration page is open
    When  I submit the registration form with a mismatched password confirmation
    Then  registration is blocked with a password-mismatch message

  # TC045 — manual step: type password / click show/hide toggle / confirm visible vs masked
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-045 Password plaintext toggle reveals and re-masks the value
    Given the Website registration page is open
    When  I type a password and toggle the show/hide eye icon on each password field
    Then  every password field cycles between masked and visible per click

  # TC057 — manual step: visit non-auth page / enter login-register / register / observe landing
  @ui @registration
  Scenario: SIT-TC-WEB-AUTH-057 Registration redirects back to the original entry page
    Given the Website homepage is open as the entry page
    When  I enter the registration flow and complete it with a brand-new email
    Then  the user is redirected back to the entry page, not a confirmation page

  # ----- Mobile variants (split 2026-06-12) -------------------------------------
  # Email-only registration flows live above; mobile counterparts here.
  # HK SMS infra is out of reach for the mainland team; QA owner verifies manually.

  @na @registration @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-118 Successful native registration (Mobile mode) - mobile variant of AUTH-001
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @registration @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-119 Duplicate mobile registration is blocked with the specified 3-language error - mobile variant of AUTH-004
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability
