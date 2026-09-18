Feature: Improve Tooling
  As a practice engineer or skill developer
  I want to improve utility scripts and skill instructions
  So that mechanical tasks are handled by scripts and skills produce better output

  Background:
    Given the utils/ directory contains reusable utility scripts
    And utils/README.md is the canonical registry
    And utils/_shared.py provides common functions

  Scenario: Extend an existing utility
    Given the user requests a new capability for an existing util
    When the util is close but missing the requested feature
    Then the skill extends the existing script
    And existing CLI arguments still work identically
    And utils/README.md is updated

  Scenario: Create a new utility
    Given the user requests a mechanical capability
    And no existing util covers the need
    When the skill creates a new script in utils/
    Then the script uses argparse with --help
    And the script imports from _shared.py where applicable
    And the script follows kebab-case naming
    And utils/README.md is updated

  Scenario: Refactor overlapping utilities
    Given two or more utils have overlapping functionality
    When the skill merges them into one
    Then the merged script preserves all original CLI interfaces
    And the original scripts are deleted
    And utils/README.md is updated

  Scenario: Improve skill instructions (direct mode)
    Given the user requests a skill instruction improvement
    When the skill enters plan mode
    Then it reads the skill's SKILL.md and contract.feature
    And proposes specific changes with rationale
    And applies changes only after user approval

  Scenario: Mid-execution util creation
    Given another skill invokes /improve-tooling during execution
    When the request describes a mechanical helper need
    Then the skill auto-proceeds without user interaction
    And creates or extends the util
    And reports back what was created with usage examples

  Scenario: Reject semantic request
    Given a request that requires LLM judgment
    When the operation needs understanding of meaning or quality
    Then the skill rejects the request
    And explains why the task is semantic, not mechanical
    And suggests the caller handle it in the LLM layer

  Scenario: Reject practice-specific request
    Given a request for a script that only works for one practice
    When the script would hardcode practice names or specific data
    Then the skill rejects the request
    And suggests generalizing or handling as a one-off
