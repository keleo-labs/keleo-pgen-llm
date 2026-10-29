Feature: Shared team meeting briefing
  Teams use evidence and role context to prepare useful discussions.

  @rule:report-740
  Scenario: Inherit and add signals
    Given project-wide signals and additional series signals
    When a meeting briefing is prepared
    Then both sets inform collection
    And the instance records their configuration provenance

  @rule:report-741
  Scenario: Reject a conflicting signal
    Given a series defines an ID already present in project signals
    When configuration is resolved
    Then resolution fails before collection or persistent state changes

  @rule:report-742
  Scenario: Preserve uncertainty
    Given a prior action with no subsequent outcome evidence
    When the retrospective is written
    Then its outcome remains unknown

  @rule:report-743
  Scenario: Reuse across teams
    Given a series configured with local evidence
    When its briefing is generated
    Then all eight sections address that team
    And no assumptions from another team's configuration appear

  Scenario: Keep reusable guidance free of team identifiers
    Given a series has named people, products and internal data sources
    When a meeting workflow is documented for reuse
    Then those identifiers remain in series configuration or private evidence
    And reusable examples use synthetic names and locations

  @rule:report-744
  Scenario: Keep all sections suitable for the team
    Given source material includes private criticism and shareable recognition
    When the briefing is written
    Then only audience-appropriate evidence appears in its eight sections and links
    And private criticism does not appear in Analysis

  @rule:report-745
  Scenario: Select discussion rather than routine status
    Given routine updates and a blocker needing shared alignment
    When the suggested agenda is written
    Then the blocker names its topic, reason and intended outcome
    And routine status does not receive a discussion slot

  @rule:report-746
  Scenario: Keep series journals independent
    Given two series seeded from the same historical journal
    When one series records a new observation
    Then the other series journal is unchanged

  @rule:report-747
  Scenario: Disclose incomplete collection
    Given a configured source is unavailable and other evidence is readable
    When an incomplete draft is requested
    Then the briefing records the gap and uses the available evidence
    And missing evidence is not reported as no developments

  @rule:report-760
  Scenario: Retrieve Google Workspace signals through GWS
    Given a series uses Google Calendar, Gmail or a linked Google document
    When its briefing sources are collected
    Then Google Workspace records are retrieved through the global GWS workflow
    And a source still unreachable after permitted host access is recorded as unavailable rather than replaced with screen scraping

  @rule:report-748
  Scenario: Reuse standing decisions
    Given the series has confirmed practices and narratives
    When another instance is prepared without material changes
    Then those choices are reused without repeated confirmation

  @rule:report-749
  Scenario: Preserve instance evidence
    Given a timezone-qualified meeting start and a configured series
    When its workspace is prepared
    Then a dated instance contains configuration and context snapshots
    And an existing instance is not overwritten

  @rule:report-750
  Scenario: Do not invent objectives or commitments
    Given objectives are unset and a role suggests a possible owner
    When the team requests an incomplete briefing
    Then objectives are labelled unset without an attainment claim
    And the possible owner remains proposed until acceptance is evidenced

  @rule:report-751
  Scenario: Summarise and interpret within one report
    Given confirmed summary and news narrative choices
    When the briefing is composed
    Then article-writing methods inform the summary and hot-take methods inform News
    And the recurring meeting name is the title and the dated instance is the first heading, followed by Suggested agenda
    And the remaining sections place Acknowledgements before News and News before Reminders

  @rule:report-752
  Scenario: Celebrate evidenced contributions
    Given shareable positive feedback, rewards and customer or partner successes
    When the briefing is composed
    Then Acknowledgements before News celebrates the people and their evidenced contributions
    And each person is credited only with the contribution attributed to them in the evidence
    And request completion is distinguished from technical success and commercial success

  @rule:report-753
  Scenario: Avoid inventing recognition
    Given no audience-appropriate positive evidence was found in the reviewed sources
    When Acknowledgements is written
    Then the section states that coverage limit without inventing praise or implying there were no successes

  @rule:report-754
  Scenario: Separate distinct items with APA 7 lists
    Given separate contributions and news developments
    When the briefing is composed
    Then each acknowledgement has its own bullet
    And list items use parallel complete sentences with initial capitals and terminal punctuation

  @rule:report-755
  Scenario: Index the relevant news without a fixed item cap
    Given six relevant evidenced developments among the configured signals
    When News is composed
    Then its opening bullet list indexes all six selected developments
    And each item has a detailed subsection preserving citations and uncertainty

  @rule:report-756
  Scenario: Keep reminders separate from developments
    Given a survey deadline and a training action in the signals
    When the briefing is composed
    Then those actions appear in Reminders rather than as News items
    And their deadlines and applicability follow the source without invented completion or ownership

  @rule:report-757
  Scenario: Brief every suggested agenda topic
    Given proposed discussion topics within the meeting duration
    When Suggested agenda is composed
    Then a summary bullet list precedes one subsection for each topic in the same order
    And each discussion subsection uses bullets to explain evidence, why team attention is needed and the intended outcome

  @rule:report-761
  Scenario: Brief acknowledgements and reminders directly
    Given evidenced acknowledgements and reminders are included as agenda topics
    When their suggested agenda details are composed
    Then the Acknowledgements subsection contains only acknowledgement item bullets
    And the Reminders subsection contains only reminder item bullets
    And neither subsection adds evidence, why, outcome or participant briefing labels

  @rule:report-758
  Scenario: Add configured quota attainment without losing product detail
    Given configured quota views overlap and a finer product business breakdown exists
    When product-quota-attainment supplies comparable targets and booked actuals
    Then Analysis presents attainment for each configured view above the finer breakdown
    And overlapping views are not added into a team total

  @rule:report-759
  Scenario: Preserve business context when quotas are unavailable
    Given the configured quota source denies access
    When the business context is prepared
    Then configured quota and attainment rows remain unavailable with the reason stated
    And the existing verified product breakdown remains available without forecast weights being called attainment
