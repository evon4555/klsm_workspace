Feature: Batch Session Configuration real UI automation

  @batch_session_configuration @ui
  Scenario: SIT-TC-STD-CONFIG-001 Verify that an admin user can open the session batch operation menu after selecting sessions
    Given I am logged in to the real Standard Product admin UI
    And I open the no-seat session management UI with session rows
    When I open the session batch operation menu
    Then the batch operation menu shows the three signed actions
    And no batch write API is emitted by the UI flow

  @batch_session_configuration @ui
  Scenario: SIT-TC-STD-CONFIG-002 Verify that batch operations cannot be started when no session is selected
    Given I am logged in to the real Standard Product admin UI
    And I open the no-seat session management UI without session rows
    When I open calendar-display batch modification and pre-generate
    Then the UI blocks pre-generation because no session row is available
    And no batch write API is emitted by the UI flow

  @batch_session_configuration @ui
  Scenario: SIT-TC-STD-CONFIG-012 Verify that pre-generation is blocked when a required target value is missing
    Given I am logged in to the real Standard Product admin UI
    And I open the no-seat session management UI with session rows
    When I open saleable-ticket-group batch modification without selecting a target group
    Then the UI blocks pre-generation because the target group is required
    And no batch write API is emitted by the UI flow

  @batch_session_configuration @ui
  Scenario: SIT-TC-STD-CONFIG-014 Verify that canceling or closing the preview does not save changes
    Given I am logged in to the real Standard Product admin UI
    And I open the no-seat session management UI with session rows
    When I generate a calendar-display preview and return without confirming
    And I generate a session-list-display preview and close without confirming
    Then no batch write API is emitted by the UI flow
