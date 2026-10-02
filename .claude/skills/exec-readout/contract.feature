Feature: Exec Readout
  As someone reporting to a decision-maker
  I want a deck that leads with the answer
  So that a senior audience gets what they need in the first two slides

  Background:
    Given the deck-foundation scripts and theme are installed
    And material describing the status or findings is available

  Scenario: Readout leads with the answer
    Given status or findings material
    When the skill completes
    Then the deck is published to Google Slides
    And a PDF is exported
    And slide two states the bottom line
    And no supporting detail appears before it

  Scenario: Decisions appear early
    Given the readout requires decisions from the audience
    When the deck is structured
    Then the decisions slide appears in the first third of the deck
    And the decisions are restated on the closing slide with owners and dates

  Scenario: No decisions required
    Given the readout requires no decisions
    When the deck is generated
    Then a slide states explicitly that no action is required

  Scenario: Bad news is stated plainly
    Given source material shows something is off track
    When the deck is written
    Then a slide names what is off track
    And states the variance as a figure
    And states what is being done about it
    And that item also appears in the bottom line

  Scenario: Status labels are defined
    Given the readout uses RAG or similar status labels
    When a status label is shown
    Then the threshold that produced it is stated

  Scenario: Quantified rather than hedged
    Given the readout describes schedule or budget position
    When the wording is inspected
    Then variances are given as figures rather than adjectives

  Scenario: Pyramid structure is used
    Given any readout request
    When the narrative shape is chosen
    Then the Pyramid shape is used
    And supporting arguments follow the answer rather than building to it

  Scenario: Promoting the conclusion is the only reordering
    Given a source document that builds to its conclusion
    When the deck is generated
    Then the conclusion appears on slide two
    And the supporting movements follow the source's sections in the source's order
    And every section of the source is represented by at least one slide

  Scenario: The promotion is declared
    Given a readout built from a source document
    When the skill reports completion
    Then the bottom-line statement is reported
    And the source section it was promoted from is named

  Scenario: The source's emphasis is kept
    Given a source document that treats one finding as principal
    When the bottom line is written
    Then it states that finding
    And not a different one chosen for being more striking

  Scenario: Slides carry citations
    Given a slide built from a passage the source document cited
    When the slide is rendered
    Then it carries a sources entry naming that citation
    And the entry links to the URL the source linked to

  Scenario: Every content slide has speaker notes
    Given a readout generated from source material
    When the published deck is inspected
    Then every content slide has a speaker-notes box
    And the notes are derived from the source's prose
    And a slide showing a status label has the detail behind it in its notes

  Scenario: Figures come from assertions, not bibliography
    Given a source document whose reference list contains a cited work with a figure in its title
    When the deck is generated
    Then that figure does not appear on any slide
