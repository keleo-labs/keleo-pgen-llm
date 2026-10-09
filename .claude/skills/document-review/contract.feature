Feature: Document Review
  As a user with a document to improve
  I want to review it against a practice domain framework
  So that I get actionable, domain-informed improvement recommendations

  Background:
    Given a practice or method is specified as the analytical framework
    And a document is provided for review

  Scenario: Standard document review
    When the skill completes all steps
    Then a review report is written to reports/<report-slug>/<report-slug>.md
    And the report identifies both strengths and weaknesses
    And gap analysis dimensions derive from the practice's domain concerns
    And recommendations are specific and actionable

  Scenario: Google Slides deck review
    Given the document is a Google Slides URL
    When the skill ingests the document
    Then content is extracted via gws CLI
    And slide-level references appear in the review findings

  Scenario: Report workspace and provenance
    When the skill completes all steps
    Then the report directory contains 00-prompt-history.md alongside the review report
    And the history records the user's prompt and the reviewed document as a source
    And the history records each practice resolved as a dependency and the report as a deliverable
    And the session is finalized

  Scenario: Focused review on specific aspects
    Given the user requests a focused review on specific dimensions
    When gap analysis is performed
    Then only the requested dimensions are assessed
    And the review acknowledges which dimensions were out of scope

  Scenario: Review with no practice context
    Given no practice or method is specified
    When the skill enters planning
    Then the skill asks the user to specify a practice framework
    And explains why a practice context is needed for domain-informed review

  Scenario: Review is linted and verified before handover
    Given a review report has been written to its workspace
    When it is handed over, exported, or published
    Then lint-report.py has run with all checks and reports no errors
    And the verification gate has run with --expect naming every verifier launched
    And no blocking error survives reconciliation
    And the verdict is recorded in 00-prompt-history.md as a decision

  Scenario: Type-specific verification of review claims
    Given the verification gate runs for a document review
    When the type-specific verifier checks the review
    Then every criticism cites the specific part of the reviewed document it refers to
    And recommendations are actionable rather than restatements of the gap
    And strengths are identified as well as gaps

  Scenario: The reviewed document is a source
    Given a document is under review
    When the source fidelity verifier runs
    Then the reviewed document is supplied to it as a source
    And every claim the review makes about that document traces to it
