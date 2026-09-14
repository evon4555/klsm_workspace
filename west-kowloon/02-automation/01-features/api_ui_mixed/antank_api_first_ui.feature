# =============================================================================
# API+UI mixed validation reference
#
#   ID      : SIT-TC-WEB-AUTH-009
#   Module  : Website / Registered Login
#   Pattern : API+UI mixed validation
#
#   This scenario is intentionally separate from antank_email_login.feature's
#   pure-UI AUTH-009 coverage. Dashboard users can run it as a focused module:
#   @api_first_ui. It proves the backend identity chain first, then verifies
#   the final profile UI with the same session.
# =============================================================================
Feature: Website API+UI mixed validation - registered login

  @api_first_ui @login @auth009 @ui @SIT-TC-WEB-AUTH-009
  Scenario: SIT-TC-WEB-AUTH-009 API+UI mixed password login reaches profile UI
    Given a registered Website user is available for API-first validation
    When  I validate the login identity chain through API and open the profile UI
    Then  the API member identity and profile UI show the same registered account
