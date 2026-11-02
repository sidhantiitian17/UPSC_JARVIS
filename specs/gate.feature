Feature: Recall gate question generation
  After a reading session the app builds a recall gate from the range that was read.
  Every question is grounded in that text and validated before the owner ever sees it.

  Scenario: Gate size adapts to the range and stays between 10 and 30
    Given a finished session
    When the gate is built
    Then it has between 10 and 30 questions
    And a larger range or a gate penalty raises the number, never beyond 30

  Scenario: Every generated question is grounded in the range
    Given the model returns questions for the range
    Then each stored question has a source chunk inside the session's range
    And a source quote that is a verbatim substring of that chunk
    And questions that fail validation are discarded and never stored

  Scenario: Validation rejects malformed questions
    Given a question with a fabricated quote, a quote outside the range, duplicate options,
      the wrong number of options, an answer index outside the options, or a repeated stem
    Then it is discarded with the reason recorded in the response

  Scenario: The gate mixes new material, interleaved review and application
    Given earlier validated questions exist for the same syllabus nodes
    Then about 70 percent come from the range just read, 20 percent from the question bank
      and 10 percent are application style
    And interleaved bank questions are marked as such and keep their own source

  Scenario: The quiz is never blocked by the cloud
    Given every LLM provider fails
    Then an offline fill-in-the-blank quiz is built from the same range
    And its questions are marked as fallback and carry the verbatim sentence they came from

  Scenario: A bad question can be reported
    Given a question in a gate
    When the owner reports it
    Then it is excluded from this gate and every future gate
    And the report is stored for the evaluation harness

  Scenario: The gate is built once per session
    Given a gate already exists for a session
    When it is requested again
    Then the same questions are returned and the model is not called

  Scenario: The Brain Context Pack personalises generation
    Given the owner has weak nodes and recent mistakes
    Then a compact profile block (at most about 6000 characters) is added to the generation prompt
