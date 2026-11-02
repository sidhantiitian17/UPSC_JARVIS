Feature: PYQ weightage trends and Direction Drift Alert
  The owner sees where the exam's questions actually come from, and whether study time follows it.
  Only questions the owner accepted tags for are counted, so the numbers are never guesses.

  Scenario: Weightage per subject and year
    Given accepted PYQ tags
    Then each subject shows its question count per year and its share of all tagged questions
    And a question with several accepted tags splits its weight equally between them
    And suggested and rejected tags are not counted

  Scenario: The chart says how much of the corpus is tagged
    Then the response shows tagged questions, questions with text and the tagged percentage

  Scenario: Direction Drift Alert compares weightage with verified time
    Given enough tagged questions and enough verified minutes in the last 28 days
    Then a subject with a large weightage share but much less than half of that share in time is flagged as under-served
    And a subject with most of the time but little weightage is flagged as heavily studied

  Scenario: No alert without enough data
    Given fewer than 30 tagged questions or fewer than 120 verified minutes
    Then the dashboard says there is not enough data yet and raises no alert

  Scenario: Alerts are supportive
    Then the alert text suggests a next step and never uses shaming words
