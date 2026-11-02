Feature: Daily planner and commitment contract
  The owner says how many hours are free; the app proposes an hour-wise plan from weak areas and due cards.
  A committed plan that was missed turns into a short catch-up block the next day, never a penalty.

  Scenario: The plan fits the free hours
    Given N free hours
    Then the planned minutes never exceed N hours
    And every study block is long enough to be useful

  Scenario: Due cards get a review block
    Given cards are due
    Then the plan starts with a review block sized to the number of cards, at most a quarter of the time

  Scenario: Weak areas get the study blocks
    Given recall history per subject
    Then study blocks go to the subjects with the lowest recall first
    And with no history, Prelims starter subjects are used

  Scenario: Breaks follow long focus blocks
    Then a break of the configured length follows each focus block when time allows

  Scenario: Invalid free hours are refused
    Given free hours below 1 or above 16
    Then the request is refused

  Scenario: A committed plan is remembered for the day
    When the owner commits a plan
    Then it is stored for today and returned by the status endpoint

  Scenario: A missed commitment becomes a catch-up block
    Given yesterday's committed study minutes and fewer than 70 percent of them verified
    Then today's plan starts with a catch-up block and the status says so
    And meeting the commitment gives no catch-up block
