# =============================================================================
# Catch-all feature for documented-only test cases  —  1:1 traceability
#
#   IDs     : SIT-TC-WEB-AUTH-011, 019, 020, 024, 038,
#             056, 058, 066
#   Source  : D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
#             03-test-design\test-cases-registration-login_2026-06-02.xlsx
#
#   Why this file exists:
#   --------------------------------------------------------------------------
#   The xlsx workbook lists cases that ARE NOT EXECUTABLE today via
#   the harness — either because the case is labeled "NA" in the workbook,
#   because the case is environment-restricted (UAT-only mail content).
#   Behave still needs to know about them so:
#
#     1. the maintenance scanner sees a 1:1 match between xlsx and features
#     2. the dashboard counts these in "skipped" not "missing automation"
#     3. when status changes (e.g. NA → SIT), the scenario can be promoted
#        to a real automated case without renumbering or filename churn
#
#   All scenarios here are tagged @na so they skip cleanly via
#   environment.py's before_scenario hook. The Scenario name carries the
#   case ID for hybrid traceability (@TAG first, scenario-name prefix
#   second — see reference_bdd_traceability_convention memory).
#
#   To promote one of these to a real test:
#     1. Update the xlsx row (status / label / scenario)
#     2. Move the scenario out of this file into the appropriate
#        antank_<flow>.feature (login / registration / forgot_password / ...)
#     3. Drop @na, add real step definitions
#     4. Re-run check_traceability.py — the case ID should still match
# =============================================================================
Feature: Documented-only registration / login cases (no automation)

  # ----------------------------------------------------------------------
  # Group: Login / lockout  (AUTH-011)
  # ----------------------------------------------------------------------
  @na @login
  Scenario: SIT-TC-WEB-AUTH-011 Failed login lockout
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  # ----------------------------------------------------------------------
  # Group: Third-party login error paths  (AUTH-019, 020)
  # ----------------------------------------------------------------------
  @na @third-party
  Scenario: SIT-TC-WEB-AUTH-019 Provider authorization cancelled by user
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @third-party
  Scenario: SIT-TC-WEB-AUTH-020 Provider returns missing identifier
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  # ----------------------------------------------------------------------
  # Group: Guest session  (AUTH-024, 038, 056, 068)
  # ----------------------------------------------------------------------
  @na @guest
  Scenario: SIT-TC-WEB-AUTH-024 Guest timeout clears state
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @guest
  Scenario: SIT-TC-WEB-AUTH-038 Guest 5-min remaining popup countdown
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @guest
  Scenario: SIT-TC-WEB-AUTH-056 Guest active logout clears guest data
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  # ----------------------------------------------------------------------
  # Group: Email content (UAT-only)  (AUTH-058)
  # ----------------------------------------------------------------------
  @na @email
  Scenario: SIT-TC-WEB-AUTH-058 Verification email content elements per language
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  # ----------------------------------------------------------------------
  # Group: Session expiry  (AUTH-066)
  # ----------------------------------------------------------------------
  @na @session
  Scenario: SIT-TC-WEB-AUTH-066 Password-mode session auto-expiry
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability
