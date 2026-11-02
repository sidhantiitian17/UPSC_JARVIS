Feature: PDF reader
  The owner reads library PDFs in the app and always returns to where they stopped.

  Scenario: The reader gets the PDF bytes through the authenticated bridge
    Given a document in the library
    When the reader requests its file
    Then the sidecar returns the PDF bytes with content type application/pdf
    And an unknown document id returns 404
    And a document whose file has moved or been deleted returns a clear 410 message

  Scenario: Last reading position is restored
    Given the owner reads page 7 of a document and leaves
    When the document is opened again
    Then the reader opens on page 7
    And page positions outside the document are rejected

  Scenario: Page navigation and zoom
    Given an open document
    Then the owner can go to the next, previous or a typed page, within the page range
    And zoom in, zoom out and fit width, within sensible limits

  Scenario: Dark reading mode
    Given the app theme is dark
    Then pages are shown with inverted colours so long sessions are comfortable

  Scenario: Text layer for selection and later bookmarks
    Given a rendered page
    Then its text is selectable through a text layer aligned with the canvas

  Scenario: A broken PDF shows a friendly error
    Given the file cannot be opened
    Then the reader shows what went wrong and a way back to the library
