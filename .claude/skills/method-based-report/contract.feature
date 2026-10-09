Feature: Method-Based Report Generation
  As a user needing a structured report
  I want to generate plain English reports using practice/method narrative frameworks
  So that my audience sees domain insight without Keleo internals

  Background:
    Given a practice, method, or baseline is specified
    And a report subject and purpose are provided

  Scenario: General-purpose report generation
    When the skill completes all steps
    Then a markdown report is written to reports/<report-slug>/<report-slug>.md
    And the report uses narrative structures from the baseline
    And no Keleo terminology appears in the report
    And the report includes APA 7 in-text citations

  Scenario: Multi-practice report
    Given multiple practices are specified
    When the skill loads context with --transitive
    Then the effective context merges all practices with provenance
    And the report draws on domain knowledge from all specified practices

  Scenario: Narrative structure selection
    Given a report purpose is identified during planning
    When narrative structures are selected
    Then the primary structure matches the purpose-to-narrative mapping
    And section headings are plain English translations of narrative elements

  Scenario: Report workspace and provenance
    When the skill completes all steps
    Then the report directory contains 00-prompt-history.md alongside the report
    And the history records the user's prompt and each practice resolved as a dependency
    And the history records the narrative strategy decision and the report as a deliverable
    And the session is finalized
    And any diagrams live in the report directory's assets/ folder

  Scenario: Missing practice context
    Given the user specifies a practice that cannot be resolved locally
    When context resolution fails
    Then the skill suggests downloading from the remote bundle library
    And provides clear error guidance

  Scenario: Report is linted and verified before handover
    Given a report has been written to its workspace
    When the report is handed over, exported, or published
    Then lint-report.py has run with all checks and reports no errors
    And the verification gate has run with --expect naming every verifier launched
    And no blocking error survives reconciliation
    And the verdict is recorded in 00-prompt-history.md as a decision

  Scenario: No type-specific verifier
    Given this is the general-purpose reporting skill
    When the verification gate runs
    Then the four base verifiers run
    And type-specific is omitted from --expect
