Feature: LLM golden evaluation harness
  Prompt templates are tested against golden fixtures so a prompt or model change that
  makes output worse is caught before it reaches the study loop.

  Scenario: A golden case passes only when output is schema-valid and its checks hold
    Given a golden case with a JSON schema and checks
    When the model output is valid and satisfies every check
    Then the case passes

  Scenario: Invalid or failing output is reported with the reason
    Given a golden case
    When the output is not valid JSON, breaks the schema, or fails a check
    Then the case fails and the report states which check failed

  Scenario: A generated MCQ must quote its source verbatim
    Given the sample task "gate_mcq" and a source passage
    When the model returns a question whose source_quote is not a verbatim substring of the passage
    Then the case fails with "source_quote is not verbatim"

  Scenario: The correct option must be one of the options
    Given a gate_mcq output whose answer_index is outside the options
    Then the case fails

  Scenario: Reports summarise pass rate and are reproducible offline
    Given fixtures and a scripted provider
    When the harness runs with no network
    Then it prints a Markdown report with pass rate per task
    And live providers are used only when explicitly requested

  Scenario: Eval runs never touch the real ledger or cache
    Given the harness uses an in-memory database
    Then the owner's data directory is untouched
