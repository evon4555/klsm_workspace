# =============================================================================
# Catch-all @na placeholder feature for cookies cases  —  1:1 traceability
#
# These cases exist in the xlsx but have no executable automation yet.
# All scenarios are tagged @na and skip via environment.py before_scenario.
# Promote to real tests by moving the scenario into a real feature file
# and dropping @na.
# =============================================================================
Feature: Documented-only cookies cases (no automation)

  @na @cookies
  Scenario: SIT-TC-WEB-Cookies-001 Cookies with first access
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @cookies
  Scenario: SIT-TC-WEB-Cookies-002 Accept Cookies
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @cookies
  Scenario: SIT-TC-WEB-Cookies-003 Not accept Cookies
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @cookies
  Scenario: SIT-TC-WEB-Cookies-004 Compatibility test with different browser
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @cookies
  Scenario: SIT-TC-WEB-Cookies-005 Cookies can record recent user content
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability
