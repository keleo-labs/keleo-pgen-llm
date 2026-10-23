Feature: Evidence-led diagnosis and executable recommendations
  Shared by all five reporting skills; applies within the agreed report scope.

  @report-724
  Scenario: Diagnosis explains the mechanism
    Given a strategy and evidence of operating constraints
    When a report presents a priority finding
    Then it connects the evidence to the mechanism affecting the outcome and affected participants
    And it distinguishes sourced facts from inferred consequences

  @report-725
  Scenario: Commercial recommendations test mutual value
    Given a report recommends an offer or investment
    When it evaluates viability
    Then it identifies the buyer, outcome, participant benefits and costs, and contracting, billing, delivery and support responsibilities
    And missing evidence is explicit rather than replaced by invented economics

  @report-726
  Scenario: Actions address constraints in dependency order
    Given implementation recommendations are within the agreed scope
    When the report prioritises actions
    Then priority actions trace to findings and specify a role, prerequisite and success evidence
    And blockers precede dependent activities and proposed commitments are labelled

  @report-727
  Scenario: Analysis respects the requested scope
    Given an informational or comparison-only report is requested
    When the report is written
    Then causal analysis remains within that scope without an unsolicited execution plan
    And prose explains the argument while tables support comparison or execution detail
