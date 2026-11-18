Feature: Export companion semantics for notebook Q&A
  As a reader of Keleo Markdown exports
  I want separate sources that explain how to interpret an export

  Scenario: Generate general companion sources
    Given a user asks for notebook guidance without choosing a practice
    When the companion skill generates the sources
    Then it creates three standalone Markdown guides for reading, evidence and composition
    And each guide identifies the language or export version behind its guidance

  Scenario: Explain the evidence available from a practice export
    Given a practice export describes a state with a checklist and an unresolved dependency
    When the companion sources explain how to answer questions about the state
    Then they distinguish the checklist criteria from a recorded completion
    And they instruct the reader to identify the missing context without filling the gap

  Scenario: Add guides beside an existing export
    Given an export directory already contains practice Markdown and a different file with a guide name
    When the companion skill prepares the guides beside that export
    Then it preserves the existing documents
    And it creates the new guide set in a fresh subdirectory
