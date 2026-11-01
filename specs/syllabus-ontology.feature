Feature: Syllabus ontology
  The syllabus tree is the knowledge graph's spine. Nodes are loaded from reviewed-by-owner
  YAML files; unreviewed content is always labelled as draft.

  Scenario: A valid ontology loads into the syllabus table
    Given YAML files describing nested nodes with unique ids
    When the ontology is loaded
    Then each node is stored with its parent, kind, paper and order

  Scenario: Ids must be unique across all files
    Given two nodes that share an id
    When the ontology is loaded
    Then loading fails and names the duplicate id

  Scenario: Invalid nodes are rejected with a clear message
    Given a node with an unknown kind, an empty title or an invalid id
    When the ontology is loaded
    Then loading fails and names the offending node

  Scenario: Draft content cannot claim to be reviewed
    Given a node with source "draft" and reviewed true
    When the ontology is loaded
    Then loading fails

  Scenario: Reloading is idempotent and keeps the owner's study links
    Given the ontology was loaded and a node has study links
    When the ontology is loaded again with that node renamed
    Then the node keeps its id and links and shows the new title
    And nodes removed from the files are pruned only if they have no links

  Scenario: The tree is served nested and in order
    When the owner opens the Syllabus screen
    Then the tree shows subjects, topics and micro-themes expandable and collapsible
    And every node shows whether it is a draft or reviewed
