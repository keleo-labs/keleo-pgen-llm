Feature: Export Keleo documents as notebook sources
  As a practice or method author
  I want Markdown files that ground notebook answers in the source

  Scenario: Export a practice with referenced context
    Given an authored practice has an unfamiliar field and refers to a dependency state
    When the practice is exported for notebook Q&A
    Then its Markdown contains the unfamiliar field
    And the Studio view follows Studio GAS practice resolution
    And the state reference repeats the relevant definition and checklist with provenance

  Scenario Outline: Export a method and its members
    Given a method has <membership> members, an authored order and a binding
    When the method is exported for notebook Q&A
    Then the export contains one method file and a file per member
    And the method file preserves the order and authored binding

    Examples:
      | membership       |
      | embedded         |
      | externally named |

  Scenario: Retrieve an authored published source
    Given Studio publishes a requested practice in a bundle
    When the skill exports that practice by name
    Then it retrieves the exact bundle through Studio MCP and authorised download
    And it uses the archived JSON as the authored source

  Scenario: Export with a supporting dependency gap
    Given a selected practice declares an unavailable supporting dependency
    When the practice is exported for notebook Q&A
    Then its Markdown preserves the authored content
    And the export identifies the missing dependency and labels the Studio view incomplete

  Scenario: Stop when a method member is unavailable
    Given a method names an unavailable member practice
    When the method is exported for notebook Q&A
    Then the export fails before writing any Markdown
