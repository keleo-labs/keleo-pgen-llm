Feature: Decision Analysis
  As a user facing a technical or strategic decision
  I want to see a balanced trade-off analysis of my options
  So that I can make an informed, contextual choice

  Background:
    Given a practice or method is specified as the domain framework
    And a question or decision is posed

  Scenario: Balanced multi-option analysis
    Given at least two options are identified
    When the skill completes all steps
    Then an analysis document is written to reports/
    And all options receive comparable depth
    And every option includes both strengths and weaknesses

  Scenario: Contextual synthesis
    When the synthesis section is written
    Then the verdict uses conditional framing ("if X, then A")
    And the synthesis identifies what would change the recommendation

  Scenario: Reusable decision framework
    When the decision framework section is written
    Then the framework is applicable beyond the specific instance analysed
    And a reader with different constraints can apply it independently

  Scenario: Options discovered from practice
    Given the user poses a question without listing options
    When the skill enters planning
    Then candidate options are proposed from the practice's domain knowledge
    And the user confirms or adjusts the option list before analysis
