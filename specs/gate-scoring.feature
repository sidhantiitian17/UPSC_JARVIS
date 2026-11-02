Feature: Recall gate answering, scoring and consequences
  Answers are scored honestly: a gate below the pass mark never raises coverage,
  skipping has a cost, and every answer carries the owner's confidence tag.

  Scenario: Answering reveals the correct option, the explanation and the source
    Given a question in the gate
    When the owner answers with a confidence tag Green, Amber or Red
    Then the attempt stores the chosen option, correctness and tag
    And the reply shows the correct option, the explanation, the verbatim source quote and its page
    And answering the same question again returns the stored result without a second attempt

  Scenario: Finishing needs every question answered
    Given unanswered questions remain
    When the owner finishes the gate
    Then it is refused

  Scenario: Pass mark is 70 percent
    Given all questions are answered
    When retention is 70 percent or more
    Then the gate passes, the session is done and XP is proportional to verified retained minutes
    And below 70 percent it fails with zero XP

  Scenario: A failed gate gives targeted restudy advice
    Given a failed gate
    Then the result lists book name, page and paragraph of each wrongly answered source
    And correctly answered sources are not listed

  Scenario: Emergency skip has a cost
    Given the owner is at the recall gate
    When they choose emergency skip
    Then no pass, no XP and the session is skipped
    And the next gate built from tomorrow has double the questions, capped at 30
    And that penalty is used up by one gate

  Scenario: The gate waiting for the owner is found after a restart
    Given a session whose end bookmark is set but whose gate is not finished
    Then it is reported as awaiting its gate until the gate is finished or skipped
