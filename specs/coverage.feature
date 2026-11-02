Feature: Honest coverage and the Today dashboard
  Progress counts only what was read AND remembered. Time on the app is never progress.

  Scenario: Coverage comes from passed gates only
    Given sessions tagged to a syllabus node
    Then only sessions whose gate was passed add verified pages
    And failed, skipped, running or ungated sessions add nothing

  Scenario: Verified pages are weighted by retention
    Given a passed gate with retention 80 percent over 3 pages
    Then it adds 2.4 verified pages to the tagged node

  Scenario: Re-reading the same pages is not double counted
    Given two passed sessions over overlapping pages of the same book
    Then each page counts once, at the best retention achieved on it

  Scenario: Percent verified is only shown when the target is known
    Given a node with a target page count
    Then it shows percent verified, capped at 100
    And a node without a target shows verified pages but no percent

  Scenario: Parents roll up their children
    Given a parent node whose children have verified pages and targets
    Then the parent's verified pages and percent come from its descendants

  Scenario: Today shows verified retained minutes, a heatmap and the next block
    When the owner opens Today
    Then it shows verified minutes today and this week from passed gates
    And a heatmap of daily verified minutes for the last 12 weeks
    And a Continue reading action pointing to the last document and page
    And due cards, with one primary action only
