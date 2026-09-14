Feature: Batch Session Configuration API plus UI mixed automation

  @batch_session_configuration @mixed
  Scenario: SIT-TC-STD-CONFIG-013 Verify that deleting a row from the preview excludes that session from submission
    Given I have a real Standard Product admin requests session for mixed execution
    And I am logged in to the real Standard Product admin UI
    When I submit a no-seat display update only for the remaining preview row through API
    Then the browser UI evidence shows the remaining row changed and the deleted row unchanged
