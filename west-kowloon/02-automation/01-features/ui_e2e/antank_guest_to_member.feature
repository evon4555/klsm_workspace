# =============================================================================
# Converted manual test cases  —  1:1 traceability
#
#   IDs     : SIT-TC-WEB-AUTH-100 .. 109, 113 .. 117, 123 .. 125  —  Guest-to-Member conversion
#   Source  : 2026-06-10 PRD §游客购票引导注册功能 (2026.6.3 新增需求) +
#             游客购票引导注册功能.md spec at 01-input/03-prd/2026-06-10/
#             03-test-design/test-cases-registration-login_2026-06-12.scope-clean-2026-06-16.xlsx
#             (sheet "Test Cases")
#   Module  : Website / Guest checkout -> registered member
#
#   Status  : @na for now — the entire guest-to-member flow (Quick Buy Without
#             Login button, blur-time uniqueness check, opt-in checkbox, account
#             upgrade on payment success, 3-language confirmation) is brand-new
#             and almost certainly not yet in SIT as of 2026-06-12. Flip the
#             @na tags to @ui once the feature lands in SIT.
# =============================================================================
Feature: Website 游客转会员 / Guest-to-Member conversion (SIT-TC-WEB-AUTH-100 .. 109)

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-100 Project detail - Quick Buy Without Login + Buy tickets as member entries
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-101 Order page - contact method picker (chosen is required, the other is optional)
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-102 Order page - when both email and mobile are filled, only the chosen one is submitted
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-103 Order page - contact name is optional and repositioned after email/mobile
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-104 Order page - OTP verification gates submission for guests; logged-in users skip
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-105 Order page - unregistered contact shows the 3-language opt-in checkbox and description
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-106 Order page - registered contact hides the opt-in checkbox
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-107 Submit + payment success WITH opt-in checked upgrades the guest account
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-108 Submit + payment success WITHOUT opt-in does not upgrade
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-109 Payment success page - 3-language registration message and "Go to My Account" button
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  # ----- Mobile variants (split 2026-06-12) -------------------------------------
  # AUTH-104~109 are the email branches; AUTH-113~117 are the mobile branches.
  # HK SMS infra out of reach; QA owner verifies manually.

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-113 Order page (guest, mobile) - mobile OTP (SMS) gates submission - mobile variant of AUTH-104
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-114 Order page - UNREGISTERED mobile shows 3-language opt-in checkbox - mobile variant of AUTH-105
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-115 Order page - REGISTERED mobile hides the opt-in checkbox - mobile variant of AUTH-106
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-116 Submit + payment success WITH opt-in (mobile branch) upgrades and stores mobile - mobile variant of AUTH-107
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-117 Payment success page (mobile branch) - 3-language message with selected mobile contact - mobile variant of AUTH-109
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-123 Order page - contact picker Mobile mode required-marker behavior - mobile variant of AUTH-101
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member @mobile-variant
  Scenario: SIT-TC-WEB-AUTH-124 Submit + payment success WITHOUT opt-in (mobile branch) - no upgrade - mobile variant of AUTH-108
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability

  @na @guest_to_member
  Scenario: SIT-TC-WEB-AUTH-125 Order page - delivery notice follows selected contact method
    Given the case is documented in the xlsx but not executable here
    Then  the harness records it as Skipped for 1:1 traceability
