Feature: Batch Session Configuration real automation

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-003 Verify that seat-selection sessions can be batch-updated to a new saleable ticket group
    Given I have a real Standard Product admin requests session
    When I read the "seat saleable group" source sessions through API
    And I submit the "seat saleable group" batch update through API
    Then the "seat saleable group" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-004 Verify that admission-ticket sessions can be batch-updated to a new saleable ticket group
    Given I have a real Standard Product admin requests session
    When I read the "admission saleable group" source sessions through API
    And I submit the "admission saleable group" batch update through API
    Then the "admission saleable group" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-005 Verify that no-seat sessions can be batch-updated to a new saleable ticket group
    Given I have a real Standard Product admin requests session
    When I read the "no seat saleable group" source sessions through API
    And I submit the "no seat saleable group" batch update through API
    Then the "no seat saleable group" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-006 Verify that seat-selection sessions can be batch-updated for calendar display
    Given I have a real Standard Product admin requests session
    When I read the "seat calendar display" source sessions through API
    And I submit the "seat calendar display" batch update through API
    Then the "seat calendar display" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-007 Verify that admission-ticket sessions can be batch-updated for calendar display
    Given I have a real Standard Product admin requests session
    When I read the "admission calendar display" source sessions through API
    And I submit the "admission calendar display" batch update through API
    Then the "admission calendar display" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-008 Verify that no-seat sessions can be batch-updated for calendar display
    Given I have a real Standard Product admin requests session
    When I read the "no seat calendar display" source sessions through API
    And I submit the "no seat calendar display" batch update through API
    Then the "no seat calendar display" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-009 Verify that seat-selection sessions can be batch-updated for session-list display type
    Given I have a real Standard Product admin requests session
    When I read the "seat session list display" source sessions through API
    And I submit the "seat session list display" batch update through API
    Then the "seat session list display" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-010 Verify that admission-ticket sessions can be batch-updated for session-list display type
    Given I have a real Standard Product admin requests session
    When I read the "admission session list display" source sessions through API
    And I submit the "admission session list display" batch update through API
    Then the "admission session list display" readback API shows the target value changed from the precondition

  @batch_session_configuration @api
  Scenario: SIT-TC-STD-CONFIG-011 Verify that no-seat sessions can be batch-updated for session-list display type
    Given I have a real Standard Product admin requests session
    When I read the "no seat session list display" source sessions through API
    And I submit the "no seat session list display" batch update through API
    Then the "no seat session list display" readback API shows the target value changed from the precondition
