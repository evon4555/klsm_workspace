# =============================================================================
# Catch-all @na placeholder feature for tkt cases  —  1:1 traceability
#
# These cases exist in the xlsx but have no executable automation yet.
# All scenarios are tagged @na and skip via environment.py before_scenario.
# Promote to real tests by moving the scenario into a real feature file
# and dropping @na.
# =============================================================================
Feature: Documented-only tkt cases (no automation)

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-001 Nearest selectable session highlighted
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-002 Multi-session same-day display
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-003 Selectable date visual indication
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-004 Calendar ↔ list view toggle
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-005 Price list display + backend cross-check
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-006 Ticket Type list display + backend cross-check
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-007 Real-Name-required Ticket Type — enforcement
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-008 First-time Real-Name fill
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-009 6 ID types selectable + validation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-010 ID display masking
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-011 Name validation + display masking
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-012 Set-as-Self + auto-fill
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-013 Edit / delete participant
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-014 Payment Countdown + reminder
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-015 Payment Countdown duration — configurable
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-016 Admission Ticket list display on Order Confirmation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-017 Contact Information mandatory fields
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-018 Phone validation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-019 International phone check
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-020 Pickup Method — Email
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-021 No-phone alternate pickup
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-022 Charity Donation — editable + correct sum
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-023 Order Summary base accuracy
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-024 Order Summary — Discount display
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-025 Privacy Terms — 4 sub-links
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-026 Order Summary — Service Fee display + calculation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-027 Route to Cybersource
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-028 Cybersource — fill billing
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-029 Pay with Visa test card
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-030 Pay with Master test card
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-031 Pay with JCB test card
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-032 Pay with CUP (UnionPay)
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-033 Pay with Apple Pay
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-034 Pay with Google Pay
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-035 Payment confirm page — info consistency
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-036 Payment Success page — 8 fields
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-037 Payment failures — 5 types
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-038 Payment "other" failure — needs Cybersource confirmation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-039 2-step payment confirmation trigger
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-040 Order Detail basic fields
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-041 Transfer — Admission Ticket absent placeholder
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-042 Contact + Pickup Method display
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-043 Order Info — Payment Reference + Payment Method
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-044 QR Code — multi-ticket + mapping-field semantics
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-045 Order Detail — Summary fields
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-046 Request Refund entry visibility
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-047 Reschedule entry visibility
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-048 Bundle Ticket — placeholder
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-049 Sold Out state in Ticket Selection
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-050 Ticket Type remark display
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-051 Selling Soon state
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-052 Same-day session scenarios
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-053 Add-On — registered user only
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-054 Add-On — single SKU + quantity
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-055 Add-On — Delivery Pay on Delivery
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-056 Add-On — Delivery Prepaid with extra fee
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-057 Add-On — Self Pickup
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-058 Add-On — E-voucher Coupon
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-059 Add-On address reuses personal centre
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-060 Add-On cross-rule — mixed cart blocks
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-061 Refund — 4 eligibility conditions
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-062 Refund button on Order Detail
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-063 Refund Detail Page contents
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-064 Refund Handling Fee calculation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-065 Refund approval — Approved + Success
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-066 Refund approval — Approved + Failure
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-067 Refund approval — Rejected
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-068 Refund User Withdraw
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-069 Reschedule — Admission Ticket placeholder
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-070 Admission Ticket mobile viewport
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-071 Admission Ticket multilingual labels
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-072 Auth state → Ticket Selection / Order Confirmation
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-073 Concurrent Admission Ticket booking — last ticket race
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-074 Payment Countdown expiry → ticket release
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-075 Same-user multi-tab same-ticket race
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-076 Refund with Add-On — fulfillment-state behavior
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-077 Real-Name — duplicate ID across participants
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability

  @na @tkt
  Scenario: SIT-TC-WEB-TKT-078 Transfer — Admission Ticket happy-path placeholder
    Given the case is documented in the xlsx but not executable here
    Then the harness records it as Skipped for 1:1 traceability
