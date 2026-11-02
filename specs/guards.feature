Feature: Sleep guard, burnout guard and bad-day mode
  The app protects the owner's sleep and energy. It nudges and explains; it never locks or shames.

  Scenario: The sleep window may cross midnight
    Given a sleep window from 23:30 to 05:30
    Then 23:45 and 02:00 are inside it and 05:30 and 12:00 are not

  Scenario: The sleep guard reports when it is active
    When the owner opens Today inside the sleep window
    Then the guard status is active and says how long until the window ends
    And the guard can be turned off in Settings

  Scenario: A 12-hour day raises a burnout warning
    Given focused time today of 12 hours or more
    Then the burnout warning is on
    And five days in a row of 9 hours or more raises a heavy-stretch notice

  Scenario: Bad-day mode keeps the streak with a smaller goal
    When the owner switches bad-day mode on for today
    Then today's goal becomes the bad-day goal and the streak can be kept with it
    And switching it off restores the normal goal
    And it can only be changed for today

  Scenario: Guard messages are supportive
    Then no guard text contains shaming words
