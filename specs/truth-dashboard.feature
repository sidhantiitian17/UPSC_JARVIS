Feature: Truth Dashboard and weekly honesty report
  Numbers that cannot flatter: claimed hours next to verified hours, confidence next to accuracy,
  and a forecast that says what the current pace implies.

  Scenario: Claimed versus verified hours
    Given sessions over the last 7 days
    Then claimed hours count all focused time and verified hours count only time whose gate passed
    And the ratio between them is shown

  Scenario: Calibration compares the Green, Amber and Red tags with real accuracy
    Given answered questions with confidence tags
    Then each tag shows its answer count and accuracy
    And a tag with too few answers says there is not enough data

  Scenario: The forecast uses the owner's real pace
    Given an exam date
    Then it shows days left, the average verified minutes per day over 28 days and the hours projected by the exam
    And without an exam date set the dashboard says it is using an assumed date

  Scenario: The weekly report is honest and kind
    Then it lists plain sentences about verified time, the claimed to verified gap and calibration
    And it never uses shaming words

  Scenario: Nothing is shown as predicted UPSC marks
    Then no figure is labelled as predicted marks or rank
