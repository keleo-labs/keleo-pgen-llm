Feature: Project Plan Generation
  As a user planning a project or engagement
  I want to generate a structured project plan using practice domain knowledge
  So that my plan has domain-informed phases, roles, activities, and success criteria

  Background:
    Given a practice or method is specified as the domain framework
    And project objectives are identified

  Scenario: Standard project plan
    When the skill completes all steps
    Then a plan document is written to reports/
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
    Then a standalone SOW document is written to reports/
    And the SOW derives scope from practice activities

  Scenario: PoC plan
    Given the engagement type is a proof of concept
    When the plan is generated
    Then the plan distinguishes between what the PoC will and will not demonstrate
    And success criteria focus on validation rather than production readiness
