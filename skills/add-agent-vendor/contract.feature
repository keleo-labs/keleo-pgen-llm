Feature: Add an agent vendor
  As a project maintainer
  I want a new agent runtime to consume shared skills
  So that its support does not fork the workflow source

  Background:
    Given canonical skills live in skills/
    And supported vendors are recorded in config/agent-vendors.json

  Scenario: Agent has its own skill discovery directory
    Given the new agent does not discover an existing project skill directory
    When support for the agent is added
    Then thin skill entrypoints point to the canonical skills
    And the wrapper parity check passes

  Scenario: Agent discovers an existing skill directory
    Given the new agent discovers .agents/skills
    When support for the agent is added
    Then its vendor profile reuses those entrypoints
    And no duplicate skill wrappers are created

  Scenario: Hook event differs from current agents
    Given the agent has a documented user-prompt hook with a different payload
    When its project hook is added
    Then prompt history records one user turn for the active session
    And a concurrent session cannot write to that history

  Scenario: Hook event is unavailable
    Given the agent has no compatible question-response hook
    When its support is documented
    Then the documentation gives the manual interaction-recording command
