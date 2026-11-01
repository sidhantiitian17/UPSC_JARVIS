Feature: Official PYQ dataset in Markdown
  As a UPSC aspirant
  I want every previous year question stored with provenance and verification status
  So that practice, analysis and model evaluation use only trustworthy questions

  Background:
    Given the official source page is "https://upsc.gov.in/examinations/previous-question-papers"
    And only English-medium papers are in scope
    And Optional Sociology Paper I and Paper II are in scope

  Scenario: Fetcher is polite and resumable
    Given the site's robots.txt allows the listing page
    When the fetcher downloads papers
    Then it waits at least 2 seconds between requests
    And it sends an identifying User-Agent
    And files already downloaded with the same ETag or hash are not downloaded again

  Scenario: Fetcher refuses to guess when the page structure changes
    Given the listing page no longer has the expected structure
    When the fetcher runs
    Then it fails with an explicit error
    And it saves an HTML snapshot for debugging
    And it downloads nothing

  Scenario: Every source is recorded with provenance
    When a PDF is downloaded
    Then manifest.jsonl gains one line with url, exam, year, phase, paper, sha256, bytes and retrieved_at
    And the PDF is stored under raw/ which is never committed

  Scenario: Hindi-medium files are skipped but recorded
    Given a listed paper is in Hindi
    When the fetcher runs
    Then the manifest records it with lang "hi" and status "skipped"

  Scenario: Parser keeps source text intact
    Given a Prelims GS Paper I PDF with 100 questions
    When the parser runs
    Then it produces 100 questions numbered 1 to 100
    And each question has four options a to d
    And each question text is a substring of the extracted page text

  Scenario: Failed segments are flagged, never silently repaired
    Given one question's text cannot be segmented
    When the parser runs
    Then that question has status "failed"
    And the coverage report lists it

  Scenario: Sociology multi-part questions are structured
    Given a Sociology Paper I question with parts a, b and c
    When the parser runs
    Then the question has parts with label, marks and text
    And the section is recorded as A or B

  Scenario: Answers come only from official keys or the owner
    Given no official answer key is available for a paper
    When the dataset is built
    Then every question in that paper has answer null and answer_source "none"
    And any LLM suggested answer is stored only as suggested_answer

  Scenario: Verification is explicit
    Given the review sample is generated
    When the owner verifies a question
    Then its status becomes "verified"
    And the file's verified_count increases

  Scenario: Re-running produces identical output
    Given the dataset was built once
    When the pipeline is run again without source changes
    Then the generated md files have identical hashes

  Scenario: Repository safety
    Then raw PDFs are always gitignored
    And generated md files are committed only after the owner's explicit opt-in is recorded in the roadmap log
