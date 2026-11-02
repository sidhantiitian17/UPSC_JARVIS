Feature: Review queue (FSRS)
  Wrong answers come back at scheduled intervals. The queue is limited per day and mixes subjects.

  Scenario: A wrong gate answer creates or lapses a card
    Given a gate is finished
    Then every wrongly answered question has exactly one card scheduled by FSRS
    And correctly answered questions get no card
    And a question answered wrongly again lapses its existing card and logs an Again review

  Scenario: Rating a card reschedules it and logs the review
    Given a card
    When it is rated Again, Hard, Good or Easy (1 to 4)
    Then FSRS computes the next due date and the card state is updated
    And a review log row stores the rating, the scheduled days and the previous state
    And Again schedules sooner than Good

  Scenario: The queue respects the daily limit
    Given more cards are due than the daily limit
    Then the queue shows at most the remaining allowance for today
    And reviews already done today use up the allowance
    And the limit is configurable and defaults to 40

  Scenario: Subjects are interleaved
    Given due cards from several subjects
    Then no subject is shown more than twice in a row while others remain

  Scenario: Suspended cards and reported questions never appear
    Given a suspended card or a question reported as bad
    Then it is excluded from the queue
