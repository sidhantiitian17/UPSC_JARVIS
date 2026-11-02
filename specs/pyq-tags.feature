Feature: Tagging PYQs to syllabus nodes
  Each previous-year question is linked to the syllabus nodes it tests. A model only suggests;
  a tag counts only after the owner accepts it.

  Scenario: Suggestions come from the LLM, with a keyword fallback
    Given a PYQ with a stem
    When the owner asks for tag suggestions
    Then the question and its options go through LLMClient task "tag_chunk" with the leaf syllabus nodes as candidates
    And if the model is unavailable a keyword match against node titles is used and labelled as such
    And a question without text cannot be tagged

  Scenario: Only the owner's accepted tags count
    When the owner accepts a suggestion
    Then it becomes an accepted tag and a graph link from the PYQ to the node
    And rejecting removes the link and the suggestion is never offered again for that question

  Scenario: Suggesting again keeps the owner's decisions
    Given accepted and rejected tags
    When suggestions are requested again
    Then accepted and rejected tags are unchanged, old pending suggestions are replaced and nothing is duplicated

  Scenario: The owner can add a tag by hand
    Then a known syllabus node can be added as an accepted tag with source owner and an unknown one is refused

  Scenario: Untagged questions can be suggested in a batch
    Then a batch with a limit suggests tags only for questions that have text and no tag yet
