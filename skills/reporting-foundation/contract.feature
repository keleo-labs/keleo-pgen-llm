Feature: Evidence-led diagnosis and executable recommendations
  Shared by the reporting suite; applies within the agreed report scope.

  Scenario: Report context resolves without content mounts
    Given no content repository is mounted
    And the report needs a published practice and baseline
    When the skill prepares context
    Then it retrieves the practice, baseline and transitive dependencies through Studio MCP
    And it resolves their materialized JSON files locally

  Scenario: Selected report lives in its content repository
    Given a private content repository is configured for the new report
    When the approved report workspace is created
    Then reports/<report-slug>/ is a mount into that repository
    And the authored report and its source assets are written there

  Scenario: Completed report workspace has a navigable README
    Given a report and its supporting files have been written
    When the reporting run is finalized
    Then reports/<report-slug>/README.md links the report and prompt history where present
    And it links additional authored files that exist
    And an existing hand-written README is preserved

  Scenario: A report about a Keleo practice uses the relevant Studio diagram form
    Given a report section explains practice dependencies, orchestration, patterns, concerns, activities, alpha states or alpha relationships
    When the section needs a structural figure
    Then the author selects the matching Keleo route from the diagram method page
    And the figure is rendered as SVG from a retained practice JSON or derived spec

  Scenario: A practice pattern figure preserves phase decisions
    Given the report explains a pattern with phase conditions, maturity targets or a guarded return
    When the report illustrates the pattern
    Then it uses the Studio practice pattern renderer from retained practice JSON
    And a portrait layout may show numbered phase parts while keeping the full figure available
    And a guarded return to an earlier part remains visible and names its target phase

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
