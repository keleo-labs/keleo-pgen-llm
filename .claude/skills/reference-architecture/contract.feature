Feature: Reference Architecture Generation
  As a user evaluating technology architecture options
  I want to generate a structured architecture comparison document
  So that I can make informed decisions with clear evaluation criteria

  Background:
    Given a practice or method is specified as the domain framework
    And at least two architecture options are identified

  Scenario: Architecture comparison with recommendation
    When the skill completes all steps
    Then an architecture document is written to reports/
    And the document includes an evaluation framework table
    And each option has topology, strengths, and weaknesses
    And a decision matrix compares options across all dimensions

  Scenario: Architecture with sizing guidance
    Given the user requests sizing information
    When the architecture document is generated
    Then a sizing guidance section includes concrete capacity numbers
    And numbers are presented in tabular format

  Scenario: Implementation approach
    Given the architecture document includes an implementation section
    When the implementation approach is described
    Then it follows a phased structure with dependencies and sequencing

  Scenario: Comparison-only mode
    Given the user does not want a recommendation
    When the architecture document is generated
    Then the executive summary describes key trade-offs instead of a recommendation
    And the comparison section presents balanced assessment without a verdict
