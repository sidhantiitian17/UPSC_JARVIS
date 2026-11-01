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

  Scenario: Fetcher reads the current listing and the archives listing on the www host
    Given the bare host upsc.gov.in redirects every path to the home page
    And the real listing lives on www.upsc.gov.in as a current page and an archives page
    When the fetcher runs
    Then it requests both listing pages on the www host
    And papers from both pages end up in the manifest
    And it never requests a listing on the bare host

  Scenario: Listing rows without a category column are still read
    Given a Civil Services table whose rows hold only the paper links in a single cell
    When the listing is parsed
    Then every PDF link in the row becomes an entry with an empty category

  Scenario: General Studies titles without the word Paper are classified
    Given Mains entries titled "General Studies - I" to "General Studies - IV"
    When they are classified
    Then they map to gs-1 to gs-4

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

  Scenario: Scanned PDFs are OCRed page by page when requested
    Given a PDF without a text layer and Tesseract installed
    When extraction runs with OCR enabled
    Then every page gets its text from OCR and keeps its page number
    And an unchanged file is not OCRed again on the next run
    And without Tesseract the run fails with an explicit error instead of guessing

  Scenario: OCR keeps margin question numbers attached to their stems
    Given an OCR result where a question number is a separate block left of its first line
    When the word boxes are rebuilt into lines
    Then the number and the stem appear on the same line, in reading order
    And words the OCR is unsure about are dropped instead of kept as junk

  Scenario: Scanned two-column pages are OCRed one column at a time
    Given a scanned page with a clear vertical gutter
    When it is OCRed
    Then the left column text comes before the right column text
    And a page without a gutter is OCRed whole

  Scenario: Two-column pages are read column by column
    Given a PDF page with a left and a right column of questions
    When the text is extracted
    Then the whole left column comes before the right column
    And a full-width page is still read top to bottom

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
