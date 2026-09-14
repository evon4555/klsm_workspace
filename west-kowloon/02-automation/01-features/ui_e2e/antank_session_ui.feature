# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs    : SIT-TC-WEB-AUTH-013, 027, 028
#   Source : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#            03-test-design\test-cases-registration-login.xlsx
#   Tags   : @session / @compat / @i18n = the module; @ui = pure-UI test mode.
# =============================================================================
Feature: Website 会话与界面 / Session & UI (SIT-TC-WEB-AUTH-013, 027, 028)

  # TC013 — manual step: login / open registered-only page / logout / go back
  @ui @session
  Scenario: SIT-TC-WEB-AUTH-013 Logout clears authenticated access
    Given a registered user is logged in
    When  the user logs out and reopens a registered-only page
    Then  the registered-only page is not accessible

  # TC027 — manual step: open auth screens on a mobile viewport
  @ui @compat
  Scenario: SIT-TC-WEB-AUTH-027 Auth screens are usable on a mobile viewport
    Given the browser uses a mobile viewport
    When  I open the login and registration screens
    Then  the auth form fields and submit controls are visible and usable

  # TC028 — manual step: switch language / inspect auth labels
  @ui @i18n
  Scenario: SIT-TC-WEB-AUTH-028 Auth labels follow the selected language
    Given the Website login page is open for a language check
    When  I switch the interface language
    Then  the auth page labels change to the selected language

  # TC076 — Added 2026-06-01 (iterate round 1). Multi-tab same-browser session
  # sync: login on tab 1, tab 2 reflects logged-in state; logout on tab 1
  # invalidates tab 2 on next action. Sibling to TC072 cross-browser scenario.
  @ui @session @multitab @na
  Scenario: SIT-TC-WEB-AUTH-076 Multi-tab same-browser session sync
    Given a logged-in session on browser tab 1
    When  I open tab 2 to the same site root URL
    Then  tab 2 is authenticated without re-prompting
    When  I log out on tab 1
    And   I trigger a registered-only action on tab 2
    Then  tab 2 either blocks the action or redirects to login
