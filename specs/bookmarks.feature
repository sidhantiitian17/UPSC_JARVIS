Feature: Start/end bookmarks and study sessions
  The owner marks exactly where a reading range starts and ends (page + paragraph chunk).
  The app saves it as a study session and links it to syllabus nodes.

  Scenario: Chunks of a page can be listed so a paragraph can be chosen
    Given a library document
    When the reader asks for the chunks of page 2
    Then it receives each chunk's id, ordinal and text in reading order

  Scenario: Only one session can run at a time
    Given a session is running
    When another start bookmark is set
    Then it is refused with the running session's id

  Scenario: The end bookmark closes the range and opens the gate
    Given a running session started at (page 1, chunk 0)
    When the end bookmark is set at (page 2, chunk 1) with focused seconds
    Then the session stores start, end, focused seconds and status "gate"
    And the end can never be before the start nor in another document

  Scenario: The range is tagged with syllabus nodes through the LLM
    Given the end bookmark is set
    Then the passage and candidate syllabus nodes go through LLMClient task "tag_chunk"
    And only candidate ids returned by the model are kept, at most three
    And each kept tag is stored as a link from the session to the node

  Scenario: Tagging never blocks the session
    Given the model fails, is unavailable, or returns unknown ids
    Then a deterministic keyword match against node titles is used
    And if nothing matches the session is saved untagged and flagged for manual tagging
    And the owner can set tags manually with known node ids only

  Scenario: Source Budget alert
    Given a syllabus node is already read from three different documents
    When a session from a fourth document is tagged to it
    Then the response warns that the node has more than three sources

  Scenario: A running session can be cancelled
    Given a running session
    When the owner cancels it
    Then it is marked skipped and no tags are stored
