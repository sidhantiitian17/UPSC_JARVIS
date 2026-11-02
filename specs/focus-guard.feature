Feature: Focus Guard (opt-in, local)
  While a focus block is running, JARVIS can notice whether the foreground app is study, neutral or a distraction.
  It is off by default, stores only the category and app name, and never window titles or URLs.

  Scenario: Off by default
    Then no window is ever sampled and the service refuses samples while the guard is off

  Scenario: Only focus blocks are watched
    Given the guard is on
    Then sampling happens only while a focus timer is running

  Scenario: Windows are classified by simple rules
    Then PDF readers and note apps are study, games and streaming apps are distraction, the rest is neutral
    And a browser tab is classified by its title keywords, and the title itself is never stored

  Scenario: JARVIS and the pet are ignored
    Given the foreground window is JARVIS or OpenPets
    Then it is not sampled at all

  Scenario: A long distraction gets one gentle nudge
    Given distraction for two minutes in a row
    Then the pet nudges once for that stretch, and again only after a study or neutral window

  Scenario: The weekly summary shows minutes per category
    Then Insights shows study, neutral and distraction minutes during focus blocks and the top distraction apps

  Scenario: Samples can be deleted
    Then the privacy panel counts focus samples and deletes them on request
