# =============================================================================
# Converted manual test case  —  1:1 traceability
#
#   ID      : SIT-TC-WEB-AUTH-009  —  Successful password-mode login
#   Source  : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#             03-test-design\test-cases-registration-login.xlsx
#             (sheet "Test Cases", row 9)
#   Module  : Website / Registered Login (password mode)
#   Goal    : Verify a registered user can log in via password mode
#             (email + password + 动态码 image captcha).
#
#   Manual test step              ->  Gherkin step
#   --------------------------------------------------------------------------
#   1. Open login.                ->  Given the Website login page is open
#   2. Select password mode.      ->  (email/password is the default tab)
#   3. Enter email/password/动态码 ->  When I enter ... / And I submit ...
#   4. Submit.                    ->  And I submit the login form ...
#   Expected: login succeeds,     ->  Then login succeeds and the home page
#             identity visible.       is shown
#
#   Test data : config/users.yml  ->  <env>.website_user
#   动态码     : a real image captcha — solved automatically by OCR with
#               retry inside WebsiteLoginPage (mirrors antank_login_page.py).
#   Pure UI   : the form fields are filled in the browser via Playwright;
#               no API login shortcut is used.
# =============================================================================
Feature: Website 登录 / Login — password mode (SIT-TC-WEB-AUTH-009-012, 026, 031, 048-050, 077)

  @ui @login
  Scenario: SIT-TC-WEB-AUTH-009 Registered user logs in via email and password
    Given the Website login page is open
    When  I enter the registered email and password
    And   I submit the login form, solving the 动态码 captcha
    Then  login succeeds and the home page is shown
    And   a screenshot of the logged-in page is saved

  # TC010 — manual step: open / enter email + wrong password / submit
  # UPDATED 2026-06-12 per 2026-06-10 PRD §用户邮箱/手机+密码登录: response MUST
  # surface the GENERIC wording "Username or password incorrect" (3 languages);
  # no account-enumeration leak. Same wording is enforced for TC012 below.
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-010 Wrong password is rejected
    Given the Website login page is open
    When  I submit the login form with a wrong password
    Then  login is rejected and the user stays unauthenticated

  # TC012 — manual step: open / enter unknown email + any password / submit
  # UPDATED 2026-06-12 per 2026-06-10 PRD: unknown account MUST surface the
  # SAME generic wording as TC010 — no "go register" guidance shown.
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-012 Unknown account cannot log in
    Given the Website login page is open
    When  I submit the login form with an unregistered email
    Then  login is rejected and the user stays unauthenticated

  # TC026 — manual step: fill form / click submit repeatedly during loading
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-026 Repeated submit does not double-process
    Given the Website login page is open
    When  I fill the login form and click submit repeatedly
    Then  the submit control shows a loading or disabled state

  # TC031 — manual step: submit valid credentials with no / wrong 动态码
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-031 Password login requires the 动态码 captcha
    Given the Website login page is open
    When  I submit valid credentials with a missing or wrong 动态码
    Then  login is blocked with a captcha error

  # TC048 — submit password-mode logins each with exactly ONE field wrong
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-048 Password login blocked when one field is wrong
    Given the Website login page is open
    When  I submit password-mode logins each with one field wrong
    Then  every wrong-field login attempt is blocked

  # TC049 — submit password-mode logins each with exactly TWO fields wrong
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-049 Password login blocked when two fields are wrong
    Given the Website login page is open
    When  I submit password-mode logins each with two fields wrong
    Then  every wrong-field login attempt is blocked

  # TC050 — submit a password-mode login with ALL THREE fields wrong
  @ui @login
  Scenario: SIT-TC-WEB-AUTH-050 Password login blocked when all fields are wrong
    Given the Website login page is open
    When  I submit a password-mode login with all three fields wrong
    Then  every wrong-field login attempt is blocked

  # TC-051..054 scenarios removed 2026-06-01 — md retired these IDs in
  # iterate round 1 (4-field design vs 3-field SIT build mismatch); user
  # confirmed full deletion 2026-06-01. The 3-field coverage they used to
  # provide is now outside the current direct-login scope.

  # TC077 - Added 2026-06-01 per customer review. Sibling to TC011 (ENTER
  # lockout). Documented-only in automation because the configured unlock
  # mechanism is environment-specific and cannot be exercised repeatably here.
  @ui @login @lockout @na
  Scenario: SIT-TC-WEB-AUTH-077 Locked account can re-authenticate after unlock condition is met
    Given the Website login page is open
    And   a registered account has been driven to locked state per TC011
    When  the configured unlock condition is satisfied
    And   I log in with the valid credentials of that account
    Then  the login succeeds
    And   the failed-login counter is reset
