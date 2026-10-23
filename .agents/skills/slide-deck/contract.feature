Feature: Slide Deck
  As someone who has to present
  I want a deck generated from my subject and source material
  So that I can walk into the room with something that argues a case

  Background:
    Given the deck-foundation scripts and theme are installed
    And Node 18+ and the gws CLI are available

  Scenario: Deck from a subject and source material
    Given a subject and at least one source document
    When the skill completes
    Then a Slidev markdown file exists in the project directory
    And the deck is published to Google Slides
    And a PDF is exported
    And every slide title is an assertion rather than a topic label
    And the first slide uses the cover layout
    And the last slide states an ask rather than thanks

  Scenario: Terse prompt with no detail
    Given a prompt naming only a subject
    When the skill runs
    Then default audience and length assumptions are stated in one line
    And the skill proceeds without blocking on questions
    And a complete deck is still produced

  Scenario: A source document sets the structure
    Given the user supplies a document as the basis for the deck
    And the user does not ask for a different structure
    When the deck is generated
    Then the slides follow the document's sections in the document's order
    And every section is represented by at least one slide
    And the completion report states the section-to-slide mapping

  Scenario: A restructure is proposed, not imposed
    Given a source document whose order would serve the audience poorly
    When the skill plans the deck
    Then it names the change it would make and gives the reason
    And it follows the source's order unless the user accepts the change

  Scenario: Narrative shape is chosen when there is no source document
    Given a deck request with a subject but no source document
    When the skill structures the deck
    Then a shape from narrative-guide.md is selected
    And the shape is named in the completion report
    And section dividers mark the movements of that shape

  Scenario: Slides carry citations
    Given a slide built from a passage the source document cited
    When the slide is rendered
    Then it carries a sources entry naming that citation
    And the entry links to the URL the source linked to
    And citations appear per slide rather than only on a references slide

  Scenario: Every content slide has speaker notes
    Given a deck generated from a source document
    When the published deck is inspected
    Then every content slide has a speaker-notes box
    And the notes are derived from the source's prose for that section

  Scenario: Figures come from assertions, not bibliography
    Given a source document whose reference list contains a cited work with a figure in its title
    When the deck is generated
    Then that figure does not appear on any slide

  Scenario: Visual review happens before completion is reported
    Given a deck has been published
    When the skill prepares to report completion
    Then the published slides have been rendered to images
    And each rendered slide has been inspected
    And no slide is reported as done with text overflowing its frame

  Scenario: Slide budget respects the speaking slot
    Given a stated speaking slot of N minutes
    When the deck is generated
    Then the content slide count is approximately N
    And section dividers are additional to that count

  Scenario: Conversion-unsafe constructs are not used
    Given the deck uses the Red Hat theme
    When the markdown is written
    Then no slide sets a frontmatter background key
    And no slide places markdown inside a raw HTML block
    And the speaker name uses the byline key rather than presenter
