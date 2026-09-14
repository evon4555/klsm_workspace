# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs    : SIT-TC-WEB-AUTH-021, 022, 023, 025  —  Website / Guest Login
#   Source : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#            03-test-design\test-cases-registration-login.xlsx
#   Page   : {antank_url}/websitehtml/index.html#/login  →  "Continue as guest"
#   Tags   : @guest = the module; @ui = pure-UI test mode.
#
#   "Robot verification" on this site = solving the 动态码 image captcha and
#   accepting the "I understand and agree to the terms" row.
# =============================================================================
Feature: Website 游客登录 / Guest login (SIT-TC-WEB-AUTH-021, 022, 023, 025)

  # TC021 — manual step: open login / select guest / complete robot verification
  @ui @guest
  Scenario: SIT-TC-WEB-AUTH-021 Visitor enters guest mode after robot verification
    Given the Website guest-login panel is open
    When  I complete the robot verification and continue as guest
    Then  a guest session starts

  # TC022 — manual step: open guest login / fail-skip robot verification / continue
  @ui @guest
  Scenario: SIT-TC-WEB-AUTH-022 Failed robot verification blocks guest login
    Given the Website guest-login panel is open
    When  I continue as guest without completing the robot verification
    Then  guest login is blocked

  # TC023 — NA: the guest-session validity countdown is shown inside the
  #         ticketing flow, not on the guest landing page, so it is not
  #         verifiable by pure-UI automation from login. Kept for 1:1
  #         traceability; @na makes environment.py skip it (NA status +
  #         evidence are recorded in the Kasi workbook by update_evidence.py).
  @ui @guest @na
  Scenario: SIT-TC-WEB-AUTH-023 Guest session shows a validity countdown
    Given I have started a guest session
    Then  a guest session validity indicator is shown

  # TC025 — manual step: login as guest / try personal centre, wallet, orders
  @ui @guest
  Scenario: SIT-TC-WEB-AUTH-025 Guest cannot access registered-only functions
    Given I have started a guest session
    When  I open a registered-only page
    Then  access is blocked or the user is prompted to log in
