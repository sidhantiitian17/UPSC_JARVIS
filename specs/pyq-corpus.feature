Feature: PYQ corpus importer and review
  The Phase 0 dataset (generated Markdown with provenance) is imported into SQLite and reviewed by the owner.
  Nothing becomes verified, and no answer key is ever filled, without the owner or the official key.

  Scenario: The dataset imports into SQLite
    Given the Phase 0 Markdown files
    When the owner imports them
    Then every question is stored with phase, year, paper, number, page, source URL and source hash
    And parsed questions keep their stem and four options, failed ones keep their raw text

  Scenario: Importing again is idempotent and never overwrites the owner's work
    Given a question the owner reviewed or verified, or whose answer the owner set
    When the dataset is imported again
    Then the owner's text, answer, answer source and status are unchanged
    And untouched questions are refreshed from the files

  Scenario: Answers never come from a model
    Then an answer is stored only from the official key or from the owner
    And a suggested answer is kept separate and is never used as the answer

  Scenario: The owner fixes a question and marks it verified
    When the owner edits the stem or options
    Then the status becomes reviewed
    And marking it verified needs a stem, four non-empty options, a page and a source URL

  Scenario: Papers and questions can be browsed and filtered
    Then the paper list shows counts per status
    And questions can be filtered by phase, year, paper and status

  Scenario: Bad requests are refused
    Then an unknown question, an invalid answer letter or a verify of an incomplete question is refused
