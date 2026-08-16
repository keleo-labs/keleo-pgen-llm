# Behavioural Contract: create-baseline-method
#
# Defines what this skill promises to do, what inputs it expects,
# what outputs it produces, and what constraints it operates under.

Feature: Baseline Practice Creation from Foundational Framework

  Background:
    Given source methodology documentation for a foundational framework
    And the user invokes /create-baseline-method

  Scenario: Baseline creation pipeline
    When the four-phase pipeline completes
    Then baselines/<name>/01-analysis-report.md exists (~30-50K words)
    And baselines/<name>/01.5-distilled-essentials.md exists (~15-25K words)
    And baselines/<name>/02-mapping-guide.md exists (~40-60K words)
    And bundles/<name>.keleo exists and passes --verify
    And validate-baseline-json.py reports 0 schema errors

  Scenario: Planning phase is mandatory
    When the skill is invoked
    Then EnterPlanMode is called before any phase execution
    And the plan assesses baseline appropriateness (vs extension practice)

  Scenario: Distillation phase identifies essentials
    Given Phase 1 analysis is complete
    When Phase 1.5 distillation runs
    Then 2-4 focuses are identified (default or custom)
    And 8-15 foundational alphas are distilled
    And 6-12 activity types are generalized
    And 5-10 competencies with 5 levels are identified
    And 3-5 narrative frameworks are defined

  Scenario: Baseline structural rules
    Given Phase 3 generates JSON
    When the JSON is validated
    Then kind is "practiceBaseline"
    And alphas have relatesTo arrays (no contributesTo or mapsTo)
    And focuses, competencies, activitySpaces, and narrativeTypes are defined
    And no activities, workProducts, or patterns are present

  Scenario: .keleo packaging
    Given baseline JSON passes validation
    When packaging runs
    Then package-keleo.py creates a .keleo archive with --verify
    And parent baseline is included if baselinePracticeName is set
