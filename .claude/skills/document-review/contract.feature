Feature: Document Review
  As a user with a document to improve
  I want to review it against a practice domain framework
  So that I get actionable, domain-informed improvement recommendations

  Background:
    Given a practice or method is specified as the analytical framework
    And a document is provided for review

  Scenario: Standard document review
    When the skill completes all steps
    Then a review report is written to reports/
    And the report identifies both strengths and weaknesses
    And gap analysis dimensions derive from the practice's domain concerns
    And recommendations are specific and actionable

  Scenario: Google Slides deck review
    Given the document is a Google Slides URL
    When the skill ingests the document
    Then content is extracted via gws CLI
    And slide-level references appear in the review findings

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
