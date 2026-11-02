Feature: Obsidian vault mirror
  Study sessions, cards and the daily summary are mirrored as plain Markdown into the owner's vault.
  The mirror is one-way, atomic and can never contain a secret.

  Scenario: Nothing is written when no vault folder is configured
    Given no vault folder is set
    When a gate is finished
    Then no files are written and the gate result is unaffected

  Scenario: A finished gate writes a session note
    Given a vault folder is configured
    When a gate is finished or skipped
    Then JARVIS/Sessions has a note with book, pages, focused minutes, retention, result and syllabus links
    And a failed gate lists the restudy pages with their verbatim quotes

  Scenario: Wrong answers become card files
    When a card is created or lapsed
    Then JARVIS/Cards has a file with the question, options, answer, explanation, source quote and node links

  Scenario: The daily note summarises the day
    Then JARVIS/Daily/YYYY-MM-DD.md lists the day's sessions as links and the verified minutes
    And rewriting it is idempotent

  Scenario: Writes are atomic and safe on Windows
    Then files are written to a temporary name and renamed into place with LF line endings
    And file names never contain characters Windows forbids

  Scenario: Secrets never reach the vault
    Given an API key is stored
    Then no vault file contains it
    And a note whose text contains a stored secret is refused instead of written

  Scenario: A broken vault never breaks studying
    Given the vault folder was deleted or is read-only
    When a gate is finished
    Then the gate still completes and the mirror failure is swallowed
