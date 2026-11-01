Feature: Decision heads with measured model selection
  As the app
  I want small local decision models only where they beat simple baselines
  So that free LLM quota is saved without hurting accuracy

  Scenario: Every head has a fallback
    Given a decision head such as "syllabus_node"
    When the chosen model is unavailable
    Then the DecisionClient falls back to rules or the LLM tier
    And the app keeps working

  Scenario: Gold set is human verified and never used for training
    Given a gold set built from verified PYQs
    Then no gold item appears in the training set

  Scenario: Bake-off decides per head
    Given contenders baseline, SetFit, laya and an LLM teacher
    When the bake-off runs on a head
    Then it reports accuracy, macro-F1, calibration error, CPU latency and RAM
    And laya is adopted for that head only if it beats the baseline by at least 3 macro-F1 points
    Or has equal F1 with half the calibration error

  Scenario: Latency budget for interactive heads
    Given a head that runs while the user waits
    When a decision runs on the owner's Windows laptop CPU
    Then it completes within 300 milliseconds
    Or the head uses the baseline instead

  Scenario: Batch heads report throughput instead of latency
    Given a head that runs at ingest time
    Then the bake-off reports decisions per second and no per-decision latency limit applies

  Scenario: Hierarchical tagging respects option limits
    Given the syllabus tree has more than 20 siblings at some level
    When the tree is prepared for a head
    Then siblings are grouped so every question has at most 20 options

  Scenario: Low confidence is escalated
    Given a decision with confidence below the head's threshold
    Then the result is marked unsure
    And it is sent to the LLM tier or to the owner for review

  Scenario: Teacher labels are audited
    Given labels produced by a teacher LLM
    Then the report includes teacher versus human agreement on the verified subset
