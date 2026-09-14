# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs     : SIT-TC-WEB-AUTH-017, 018, 059-063 (modified by 2026-06-02 change)
#             + SIT-TC-WEB-AUTH-078..087        (new in 2026-06-02 change)
#   Source  : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#             03-test-design\test-cases-registration-login_2026-06-02.xlsx
#             (sheet "Test Cases")
#   Module  : Website / Third-party Login + Website / Third-party Bind
#   Page    : {antank_url}/websitehtml/index.html#/login        (entry)
#             {antank_url}/websitehtml/index.html#/link-account (Link Your Account)
#
#   Tags    : @third-party  = the module
#             @ui           = pure-UI piece (button visibility, redirect)
#             @bind         = the Link-Your-Account page sub-flow (AUTH-078..087)
#             @needs-oauth-mock = scenario cannot complete without an OAuth
#                                 provider mock; the step that needs the mock
#                                 raises a recognisable skip reason so
#                                 dashboard shows the case as "Skipped" not
#                                 "Failed". Remove this tag once we add a mock
#                                 server for Google/Facebook/X/TikTok/WeChat
#                                 (see 01-system/10-change-management.md
#                                 open question — provider mock).
#
#   To run a single case:   behave --name "SIT-TC-WEB-AUTH-078"
#   To run the whole flow:  behave --tags=@third-party
#   To exclude blocked:     behave --tags=@third-party --tags=~@needs-oauth-mock
#
#   动态码 / Verification Code : same UI components as the registration flow
#                                 — solved via OCR (ddddocr) + IMAP for OTP.
#   PRD source                  : §3.2.2 (2026-05-26 完善绑定流程)
#                                 link: feishu.cn/.../YWQddc6p0opPOAxkY4ucKrxgnVh
#                                       (see CHANGE.md in 01-input/figma/2026-06-02/)
# =============================================================================
Feature: Website 第三方登录 / Third-party login + Link Your Account binding (SIT-TC-WEB-AUTH-017, 018, 059-063, 078-087)

  # ===========================================================================
  # Modified by 2026-06-02 — OAuth main flow now passes through Link page
  # ===========================================================================

  # TC017 — manual step: provider OAuth → Link page → bind via Email/Phone
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-017 Third-party login creates new account
    Given the Website login page is open
    When  I click a third-party provider button
    And   I complete provider OAuth authorization
    Then  the Link Your Account page is shown
    And   I can complete account binding via Email or Phone
    And   a new platform account is created and the OAuth identity is linked

  # TC018 — provider already linked → skip Link page → direct login
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-018 Third-party login with already-linked provider skips Link page
    Given the Website login page is open
    And   the third-party account is already linked to a platform account
    When  I click the same third-party provider button
    And   I complete provider OAuth authorization
    Then  the Link Your Account page is NOT shown
    And   I am logged in directly to the previously-linked account

  # TC059 — Google end-to-end (first-time + repeat)
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-059 Third-party login end-to-end via Google
    Given the Website login page is open
    When  I complete a first-time Google OAuth and Link Your Account binding
    Then  login succeeds and a platform account is created and linked
    And   a subsequent Google login skips Link page and lands directly on home

  # TC060 — Facebook end-to-end
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-060 Third-party login end-to-end via Facebook
    Given the Website login page is open
    When  I complete a first-time Facebook OAuth and Link Your Account binding
    Then  login succeeds and a platform account is created and linked
    And   a subsequent Facebook login skips Link page and lands directly on home

  # TC061 — X (Twitter) end-to-end
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-061 Third-party login end-to-end via X
    Given the Website login page is open
    When  I complete a first-time X OAuth and Link Your Account binding
    Then  login succeeds and a platform account is created and linked
    And   a subsequent X login skips Link page and lands directly on home

  # TC062 — TikTok end-to-end
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-062 Third-party login end-to-end via TikTok
    Given the Website login page is open
    When  I complete a first-time TikTok OAuth and Link Your Account binding
    Then  login succeeds and a platform account is created and linked
    And   a subsequent TikTok login skips Link page and lands directly on home

  # TC063 — WeChat end-to-end (QR-code flow)
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-063 Third-party login end-to-end via WeChat
    Given the Website login page is open
    When  I complete a first-time WeChat OAuth (QR scan) and Link Your Account binding
    Then  login succeeds and a platform account is created and linked
    And   a subsequent WeChat login skips Link page and lands directly on home

  # ===========================================================================
  # Added by 2026-06-02 — Link Your Account sub-flow detail
  # ===========================================================================

  # TC078 — bind via Email, email not yet registered → create new account
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-078 Bind via Email — new account branch
    Given I have just completed OAuth and am on the Link Your Account page in Email mode
    When  I bind via an UNREGISTERED email with valid 动态码, OTP and Terms ticked
    Then  the orange "email not registered" notice is shown
    And   a new platform account is created and the OAuth identity is linked
    And   the success page is shown then auto-login completes

  # TC079 — bind via Email, email already registered → link to existing
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-079 Bind via Email — existing account branch
    Given I have just completed OAuth and am on the Link Your Account page in Email mode
    When  I bind via an ALREADY-REGISTERED email with valid 动态码, OTP and Terms ticked
    Then  the blue "email already registered" notice is shown
    And   the OAuth identity is linked to the existing account (no new account created)
    And   the success page is shown then auto-login to the existing account

  # TC080 — bind via Phone, phone not registered → create new
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-080 Bind via Phone — new account branch
    Given I have just completed OAuth and am on the Link Your Account page
    When  I switch to Phone mode and bind via an UNREGISTERED phone with valid OTP and Terms
    Then  the orange "phone not registered" notice is shown
    And   a new platform account is created and the OAuth identity is linked

  # TC081 — bind via Phone, phone registered → link existing (masked)
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-081 Bind via Phone — existing account branch with masked phone
    Given I have just completed OAuth and am on the Link Your Account page
    When  I switch to Phone mode and bind via an ALREADY-REGISTERED phone with valid OTP and Terms
    Then  the blue "phone already registered" notice is shown with a masked phone number
    And   the OAuth identity is linked to the existing account

  # TC082 — captcha on the Link page
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-082 Bind page captcha is required and refreshable
    Given I am on the Link Your Account page after OAuth
    When  I submit with an empty captcha
    Then  the captcha field reports "Captcha required"
    When  I submit with a wrong captcha value
    Then  the captcha field reports "Captcha incorrect"
    When  I click the 动态码 image to request a fresh captcha
    Then  a fresh captcha image is shown

  # TC083 — OTP send + cooldown + wrong-code retry on Link page
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-083 Bind page OTP send, cooldown and wrong-code retry
    Given I am on the Link Your Account page after OAuth with email entered
    When  I click Get Code
    Then  the OTP arrives within 30 seconds
    And   the Get Code button is disabled or counting down for ~30 seconds
    When  I enter a wrong OTP and submit
    Then  the verification code field reports an error
    When  I enter the correct OTP and submit
    Then  the bind proceeds

  # TC084 — Terms checkbox mandatory; marketing optional
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-084 Bind page Privacy / Terms checkbox is mandatory
    Given I am on the Link Your Account page with all other fields valid
    When  I submit without ticking the Privacy / Ticket Purchase Terms checkbox
    Then  the bind is blocked with a Terms-required message
    When  I tick only the marketing checkbox
    Then  the bind is still blocked
    When  I tick the Privacy / Ticket Purchase Terms checkbox
    Then  the bind proceeds

  # TC085 — Email ↔ Phone mode switch
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-085 Bind page Email and Phone modes can be switched
    Given I am on the Link Your Account page in Email mode
    When  I click "Use phone number"
    Then  the Phone mode is active with the country code dropdown visible
    When  I click "Use email"
    Then  the Email mode is active and the captcha refreshes

  # TC086 — Country code dropdown + phone format validation
  @ui @bind @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-086 Bind page country code and phone format validation
    Given I am on the Link Your Account page in Phone mode
    When  I keep the default country code "CN +86" and enter an 11-digit CN phone
    Then  the phone field has no inline error
    When  I change the country code to "HK +852" and re-enter the CN phone
    Then  the phone field reports a format error
    When  I enter a valid HK phone for "+852"
    Then  the phone field has no inline error

  # TC087 — already-linked OAuth → skip Link page (critical edge case)
  @ui @third-party @needs-oauth-mock
  Scenario: SIT-TC-WEB-AUTH-087 Already-linked third-party account skips the Link page
    Given the third-party account is already linked to a platform account
    When  I click the same provider button on the login page
    And   I complete provider OAuth authorization
    Then  the Link Your Account page is NOT shown
    And   I land directly on the home / member area
    And   no "Account linked successfully" transient page is shown

  # ----- Mobile variant (split 2026-06-12) --------------------------------------
  @na @third-party @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-120 Bind page (third-party auth, Mobile mode) - OTP send, 30s cooldown, wrong-code retry - mobile variant of AUTH-083
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability
