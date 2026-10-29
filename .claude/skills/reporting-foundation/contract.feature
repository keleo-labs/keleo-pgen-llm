Feature: Evidence-led diagnosis and executable recommendations
  Shared by the reporting suite; applies within the agreed report scope.

  Scenario: Recurring team reports use nested instance workspaces
    Given a team-meeting series with persistent configuration
    When an approved meeting instance is prepared
    Then its report, snapshots and provenance occupy a dated series subfolder
    And its recurring meeting name is the title, its dated instance is the first heading and Suggested agenda follows immediately
    And its eight report sections place Acknowledgements before News, News before Reminders and References within final Analysis

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

  @report-728
  Scenario: A briefing opens with its practical decision
    Given a briefing has a practical decision and may draw on sources about a successor operating model
    When the opening is written
    Then it states the subject's practical purpose and the decision facing the reader directly
    And it names a successor model early only when the sources establish that relationship
    And predecessor names and acronym expansions agree with the sources

  @report-729
  Scenario: Ordered steps and decision questions are easy to scan
    Given a briefing contains three or more genuinely ordered steps or distinct decision questions
    When the passage is written
    Then those steps or questions use a numbered list with a brief introduction
    And explanation and connected analysis remain in prose
    And a passage without a genuine sequence or set of distinct questions is not turned into a list merely for formatting
