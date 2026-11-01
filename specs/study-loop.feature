Feature: Study Loop — bookmark a reading range, focus, then pass a recall gate
  As a UPSC aspirant
  I want the app to verify that what I just read is retained
  So that my progress bar reflects real learning, not just time spent

  Background:
    Given a PDF "Laxmikanth.pdf" is in the library with 700 pages
    And the syllabus tree contains node "Polity.Parliament.MoneyBill"
    And the focus timer is set to 50 minutes

  Scenario: Record a reading range with start and end bookmarks
    Given I open "Laxmikanth.pdf" at page 140
    When I set a start bookmark at page 140 paragraph 2
    And I read until page 152 paragraph 4
    And I set an end bookmark
    Then a study session is saved with start (140, p2) and end (152, p4)
    And the session is tagged with at least one syllabus node
    And the session stores date, focused seconds and book name

  Scenario: The reader locks when the focus timer ends
    Given a study session is running with 1 second left
    When the timer reaches zero
    Then the PDF reader is locked
    And the recall gate opens

  Scenario: Gate questions are grounded in the range I read
    Given a finished session for pages 140 to 152
    When the recall gate generates questions
    Then the number of questions is between 10 and 30
    And every question has a source chunk id inside pages 140 to 152
    And every question has a verbatim source quote
    And questions that fail validation are discarded

  Scenario: Gate pass advances honest coverage
    Given the gate has 20 questions
    When I answer 15 correctly
    Then the retention score is 75 percent
    And coverage for the tagged syllabus nodes increases
    And I earn XP proportional to verified retained minutes

  Scenario: Gate fail triggers targeted restudy advice
    Given the gate has 20 questions
    When I answer 8 correctly
    Then coverage does not increase
    And the app shows restudy advice with book name, page and paragraph
    And each wrong answer is added to the spaced repetition queue

  Scenario: Emergency skip has a cost
    Given I am at the recall gate
    When I choose emergency skip
    Then no coverage is awarded
    And tomorrow's gate has double the number of questions

  Scenario: Confidence tagging is captured
    Given I am answering a gate question
    When I tag it Green, Amber or Red
    Then the tag is stored with the attempt
    And my calibration chart can compare tag to accuracy

  Scenario: Bad generated question can be reported
    Given a question looks wrong
    When I click Report bad question
    Then the question is excluded from future gates
    And the report is stored for the evaluation harness
