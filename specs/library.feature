Feature: Library
  The owner adds study PDFs; the app extracts text page by page, splits it into addressable
  chunks (page + character offsets) and indexes them for search.

  Scenario: Adding a PDF extracts, chunks and indexes it
    Given a text PDF with several pages
    When the owner adds it to the library
    Then the document is stored with its title and page count
    And every page's text is split into chunks that record page and character offsets
    And a full-text search finds the chunk containing a word from the PDF

  Scenario: The same file is never added twice
    Given a PDF already in the library
    When the owner adds the same bytes again, even under another name
    Then the existing document is returned and no chunks are duplicated

  Scenario: Chunk offsets are exact
    Given any stored chunk
    Then the chunk text equals the page text between its character offsets
    And no chunk exceeds the maximum size

  Scenario: Scanned PDFs are detected and flagged, not rejected
    Given a PDF whose pages contain no extractable text
    When the owner adds it
    Then the document is stored flagged as scanned with a warning
    And no chunks are created

  Scenario: Only real PDF files are accepted
    Given a path that does not exist, is a folder, or is not a PDF
    When the owner adds it
    Then it is refused with a clear message and nothing is stored
