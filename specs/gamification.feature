Feature: XP, levels, streaks and freezes
  Rewards follow verified retention, never time on the app. The tone is supportive: a missed day
  pauses a streak, it never shames.

  Scenario: XP comes only from passed gates
    Given sessions with gates
    Then XP is the sum of XP awarded by passed gates
    And failed, skipped and ungated sessions give none

  Scenario: Levels get steadily harder
    Then level n needs 50*n*(n-1) total XP, so level 2 needs 100 and level 3 needs 300
    And the response shows XP into the level and XP to the next level

  Scenario: A day counts when verified minutes reach the daily goal
    Given a daily goal of verified minutes
    When a day reaches it
    Then the streak grows by one
    And today does not break the streak while it is still in progress

  Scenario: Streak freeze protects a missed day
    Given a 7-day streak earns a freeze, up to 2 saved
    When a day is missed and a freeze is available
    Then the freeze is used and the streak is kept without growing

  Scenario: Bad-day mode keeps the streak with a smaller goal
    Given a day marked as a bad day
    Then its goal is the bad-day minimum instead of the daily goal

  Scenario: A broken streak offers a comeback quest
    Given a streak of at least 3 was lost
    When the owner reaches the goal on 3 days in a row
    Then the streak is restored to half the lost streak plus those 3 days

  Scenario: Every change is explained by an event log
    Then the response lists dated events: gate passed, level up, freeze earned or used, streak paused, comeback done
