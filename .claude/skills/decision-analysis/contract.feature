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
    Then an analysis document is written to reports/<report-slug>/<report-slug>.md
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

  Scenario: Report workspace and provenance
    When the skill completes all steps
    Then the report directory contains 00-prompt-history.md alongside the analysis
    And the history records the user's prompt and each practice resolved as a dependency
    And the history records the narrative strategy decision and the analysis as a deliverable
    And the session is finalized

  Scenario: Options discovered from practice
    Given the user poses a question without listing options
    When the skill enters planning
    Then candidate options are proposed from the practice's domain knowledge
    And the user confirms or adjusts the option list before analysis

  Scenario: Analysis is linted and verified before handover
    Given a decision analysis has been written to its workspace
    When it is handed over, exported, or published
    Then lint-report.py has run with all checks and reports no errors
    And the verification gate has run with --expect naming every verifier launched
    And no blocking error survives reconciliation
    And the verdict is recorded in 00-prompt-history.md as a decision

  Scenario: Type-specific verification of balance
    Given the verification gate runs for a decision analysis
    When the type-specific verifier checks the options
    Then every option receives comparable depth of treatment
    And no option is weakened by thin treatment rather than by evidence
    And stated trade-offs are real rather than token weaknesses on a favoured option
    And the recommendation follows from the analysis rather than the analysis being arranged to reach it
