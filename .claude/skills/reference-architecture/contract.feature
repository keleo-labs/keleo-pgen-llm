Feature: Reference Architecture Generation
  As a user evaluating technology architecture options
  I want to generate a structured architecture comparison document
  So that I can make informed decisions with clear evaluation criteria

  Background:
    Given a practice or method is specified as the domain framework
    And at least two architecture options are identified

  Scenario: Architecture comparison with recommendation
    When the skill completes all steps
    Then an architecture document is written to reports/<report-slug>/<report-slug>.md
    And the document includes an evaluation framework table
    And each option has topology, strengths, and weaknesses
    And a decision matrix compares options across all dimensions

  Scenario: Report workspace and provenance
    When the skill completes all steps
    Then the report directory contains 00-prompt-history.md alongside the architecture document
    And the history records the user's prompt and each practice resolved as a dependency
    And the history records the narrative strategy decision and the document as a deliverable
    And the session is finalized
    And every option's topology diagram lives in the report directory's assets/ folder

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
