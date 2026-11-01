Feature: Spaced repetition with FSRS
  As a UPSC aspirant
  I want wrong and important items to come back at the right time
  So that I retain facts until the exam

  Scenario: A wrong gate answer becomes a card
    Given I answered a gate question incorrectly
    When the gate result is saved
    Then a card exists for that question
    And its first due date is scheduled by FSRS

  Scenario: Review rating reschedules the card
    Given a card is due today
    When I rate it Again, Hard, Good or Easy
    Then FSRS computes a new due date
    And a review log entry is stored with the rating and the interval

  Scenario: Due queue respects a daily limit and interleaves subjects
    Given 80 cards are due and my daily limit is 40
    When I open the review queue
    Then at most 40 cards are shown
    And cards from different subjects are interleaved

  Scenario: Forgetting risk is visible per syllabus node
    Given cards linked to node "Eco.RBI.Liquidity" have low retrievability
    When I open Insights
    Then the node is listed under forgetting risk

  Scenario: Cards are mirrored to the Obsidian vault
    Given a vault folder is configured
    When a new card is created
    Then a markdown file with the question, answer, source and node exists in the vault
    And the vault file never contains API keys or tokens
