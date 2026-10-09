Feature: Project Plan Generation
  As a user planning a project or engagement
  I want to generate a structured project plan using practice domain knowledge
  So that my plan has domain-informed phases, roles, activities, and success criteria

  Background:
    Given a practice or method is specified as the domain framework
    And project objectives are identified

  Scenario: Standard project plan
    When the skill completes all steps
    Then a plan document is written to reports/<report-slug>/<report-slug>.md
    And the plan includes explicit scope boundaries (in and out)
    And activities map to deliverables
    And success criteria are measurable

  Scenario: Project plan with SOW appendix
    Given the user requests a SOW alongside the plan
    When the skill generates the output
    Then the plan document includes a Statement of Work section
    And the SOW includes a roles and level of effort table
    And the SOW includes an assumptions section

  Scenario: Standalone SOW
    Given the user requests only a SOW
    When the skill generates the output
    Then a standalone SOW document is written to reports/<report-slug>/<report-slug>-sow.md
    And the SOW derives scope from practice activities

  Scenario: Report workspace and provenance
    When the skill completes all steps
    Then the report directory contains 00-prompt-history.md alongside the plan
    And the history records the user's prompt and each practice resolved as a dependency
    And the history records the narrative strategy decision and the plan as a deliverable
    And a SOW, where one was produced, is recorded as a separate deliverable in the same directory
    And the session is finalized

  Scenario: PoC plan
    Given the engagement type is a proof of concept
    When the plan is generated
    Then the plan distinguishes between what the PoC will and will not demonstrate
    And success criteria focus on validation rather than production readiness

  Scenario: Plan is linted and verified before handover
    Given a plan has been written to its workspace
    When it is handed over, exported, or published
    Then lint-report.py has run with all checks and reports no errors
    And the verification gate has run with --expect naming every verifier launched
    And no blocking error survives reconciliation
    And the verdict is recorded in 00-prompt-history.md as a decision

  Scenario: Type-specific verification of estimates and scope
    Given the verification gate runs for a project plan
    When the type-specific verifier checks the plan
    Then every estimate traces to a stated assumption
    And the assumptions are listed in the plan rather than left implied
    And a SOW's scope matches the plan's activities and deliverables

  Scenario: SOW is verified as its own deliverable
    Given a SOW was produced alongside the plan
    When the verification gate runs
    Then the SOW is linted and verified in its own right
    And it is not treated as covered by the plan's verdict
