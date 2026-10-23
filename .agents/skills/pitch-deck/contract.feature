Feature: Pitch Deck
  As someone pitching for a decision
  I want a deck that argues the case and asks for one thing
  So that the audience can say yes

  Background:
    Given the deck-foundation scripts and theme are installed
    And the subject of the pitch is known

  Scenario: Pitch with a clear ask
    Given a stated decision being asked for
    And source material describing what is being pitched
    When the skill completes
    Then the deck is published to Google Slides
    And a PDF is exported
    And the closing slide names that decision, an owner and a date
    And exactly one ask is made

  Scenario: Missing ask blocks generation
    Given a prompt that does not say what decision is being requested
    When the skill runs
    Then the skill asks what the decision is
    And does not generate a deck until the ask is known

  Scenario: Cost of inaction is quantified
    Given a pitch deck is generated
    When the current-state movement is written
    Then it states a cost, delay or risk of not acting
    And that cost is expressed as a figure rather than an adjective

  Scenario: Proof precedes mechanism
    Given the deck contains both evidence and an explanation of how it works
    When the slide order is inspected
    Then the first proof slide appears before the first mechanism slide

  Scenario: A source document sets the structure
    Given the user supplies a report as the basis for the pitch
    And the user does not ask for a different structure
    When the deck is generated
    Then the slides follow the source's sections in the source's order
    And every section of the source is represented by at least one slide
    And the report states the section-to-slide mapping

  Scenario: A restructure is proposed, not imposed
    Given a source document whose order undersells the case for this audience
    When the skill plans the deck
    Then it names the sections it would reorder and gives the reason
    And it follows the source's order unless the user accepts the change

  Scenario: A dropped section is declared
    Given a source section that did not become slides
    When the skill reports completion
    Then that section is named in the report
    And a reason for omitting it is given

  Scenario: Figures are sourced
    Given the deck contains quantitative claims
    When the skill reports completion
    Then every figure carries a source or an illustrative marker
    And the report lists each figure the user must substantiate

  Scenario: Figures come from assertions, not bibliography
    Given a source document whose reference list contains a cited work with a figure in its title
    When the deck is generated
    Then that figure does not appear on any slide
    And only figures the source document asserted are used

  Scenario: Slides carry citations
    Given a slide built from a passage the source document cited
    When the slide is rendered
    Then it carries a sources entry naming that citation
    And the entry links to the URL the source linked to
    And the citation appears on that slide rather than only on a references slide

  Scenario: Every content slide has speaker notes
    Given a deck generated from a source document
    When the published deck is inspected
    Then every content slide has a speaker-notes box
    And the notes are derived from the source's prose for that section
    And the notes carry the caveats and the answers to anticipated objections
    And the slide remains intelligible when its notes are removed

  Scenario: Positioning constraints are respected
    Given the deck concerns Red Hat or partner offerings
    When the content is written
    Then hyperscalers are framed as complementary rather than competitive
    And no competitor is cited as a source
    And no slide argues for migrating away from public cloud

  Scenario: Alternatives are named
    Given the audience has an existing option including doing nothing
    When the deck argues its case
    Then that alternative is named explicitly
    And the argument addresses it rather than ignoring it
