Feature: Ontology from the owner-supplied official syllabus
  GS-I to GS-IV and Sociology nodes come from the owner's syllabus compilation, not from memory.

  Scenario: Every official point becomes one topic node, verbatim
    Given the syllabus Markdown with provenance
    When the importer runs
    Then GS-I has 12 points, GS-II 20, GS-III 20 and GS-IV 9, matching the totals the document states
    And each node title is the document's text, with only whitespace and listed spelling fixes changed

  Scenario: Sociology keeps the document's structure
    Then Paper I has its 10 numbered sections with lettered topics
    And the thinkers in section 4 are nodes of kind thinker
    And Paper II has parts A, B and C, their roman-numbered groups as topics and lettered items as micro-themes

  Scenario: Spelling mistakes of the source are corrected only in titles
    Then "Durkhteim", "Talcolt" and "G.S. Ghure" are corrected in node titles
    And the dataset Markdown keeps the source text unchanged

  Scenario: Generated nodes are marked owner-supplied and unreviewed
    Then every generated node has source "owner" and reviewed false

  Scenario: The generated files load into the ontology
    Then the loader accepts them with globally unique ids

  Scenario: Regenerating is deterministic
    Then running the importer twice produces identical files
