Feature: Shared project writing style
  As a reader of content produced by project skills
  I want clear and consistent language
  So that I can understand the intended meaning on one reading

  Scenario: Reader-facing prose uses the shared clarity rules
    Given a project skill drafts or revises prose for a human reader
    When it prepares the deliverable
    Then it applies the project writing-style skill
    And terms, verbs, sentence length and information order support clear meaning
    And it preserves technical accuracy and sourced claims

  Scenario: Reader-facing strings in structured artifacts use the shared rules
    Given a skill produces a structured artifact with descriptions, narratives or labels
    When it writes the artifact
    Then it applies the clarity rules to reader-facing string values
    And it does not change required syntax, identifiers, quotations or official names

  Scenario: General clarity does not claim formal conformance
    Given a deliverable was revised with the shared writing-style skill
    When the skill reports the result
    Then it does not claim formal ASD-STE100 conformance without the full standard, controlled dictionary and dedicated review
