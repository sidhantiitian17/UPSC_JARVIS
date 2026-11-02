Feature: Pet companion (OpenPets)
  The pet reacts to study events in three modes. It is a coach: short, specific and never shaming.

  Scenario: Each study event has a reaction and, outside silent mode, a short message
    Given the events session start, idle, gate pass, gate not passed, level up and distraction
    Then each maps to one of OpenPets' allowed reactions
    And the message is at most 140 characters

  Scenario: Modes change the tone, not the kindness
    Given Coach, Strict and Silent modes
    Then Coach is warm, Strict is short and factual, and Silent only animates and says nothing
    And no message in any mode contains a shaming word

  Scenario: Messages follow the owner's pet rules
    Then a gate that was not passed points to the restudy list, an idle pet offers a break, and a level-up is small and specific

  Scenario: The pet never gets in the way
    Given OpenPets is not running or rejects a message
    Then JARVIS carries on silently and reports the pet as unavailable

  Scenario: The pet does not nag
    Then idle and distraction messages are rate limited
    And a message other than a celebration is not repeated within 30 seconds

  Scenario: Unknown events and over-long text are refused
    Then only known events are accepted and no text over 140 characters is ever sent
