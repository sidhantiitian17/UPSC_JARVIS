Feature: Privacy panel
  The owner can see exactly what JARVIS stores, where, and for how long, and delete it per category.

  Scenario: The panel lists every category with counts and locations
    Then it lists library text, study history, review cards and AI cache with counts
    And it shows the database path, the vault folder and the library folder
    And it states that API keys stay encrypted on this PC and that nothing leaves the PC except AI requests

  Scenario: Deleting needs explicit confirmation
    When a delete is requested without confirmation
    Then nothing is deleted

  Scenario: Deleting a category removes only that category
    When study history is deleted
    Then sessions, attempts, gate results and session tags are gone
    And library text, cards and the syllabus remain

  Scenario: Deleting library text warns about what depends on it
    Then the library category says that sessions tied to those books are removed too

  Scenario: Unknown categories are refused
    Given a category that does not exist
    Then the request is refused
