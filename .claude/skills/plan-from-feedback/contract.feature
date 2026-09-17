Feature: Plan from Feedback
  As a practice engineer
  I want to triage and resolve issues from a feedback register
  So that practice quality improves incrementally and resolution status is tracked

  Background:
    Given a Google Sheet issue register exists with structured table columns A-T
    And the register URL is stored in .claude/user-config.json
    And the table schema includes both input columns (A-P) and resolution columns (Q-T)

  # --- Configuration ---

  Scenario: First-time configuration
    Given .claude/user-config.json does not contain issueRegisterUrl
    When the skill is invoked
    Then the user is prompted for the issue register URL
    And the spreadsheet ID is extracted and saved to user-config.json

  Scenario: Table schema extension
    Given the register table has only 16 columns (input only)
    When the skill reads the register
    Then the table is extended to 20 columns with resolution column definitions
    And the Status dropdown is updated to include all six status values

  Scenario: Table schema already current
    Given the register table already has 20 columns
    When the skill reads the register
    Then no schema update is performed

  # --- Triage Decision: Scope ---

  Scenario: In-scope practice content issue
    Given an issue with Type "Issue" and Document Kind "practice"
    And the issue describes incorrect states, bad checklists, or missing elements
    When the issue is triaged
    Then it is assessed as actionable
    And resolution level L1 (Practice/Method) is assigned

  Scenario: Systemic generation problem
    Given an issue that reveals a pattern recurring across multiple generated practices
    When the issue is triaged
    Then resolution levels L1 and L2 are assigned
    And L2 identifies the specific skill or utility to improve

  Scenario: Schema gap
    Given an issue that reveals a missing construct in the Practice Language
    When the issue is triaged
    Then resolution levels L1, L2, and L3 are assigned
    And L3 identifies the specific schema or semantics file to change

  Scenario: Studio UI enhancement (out of scope)
    Given an issue describing a keleo-studio rendering, navigation, or interaction change
    And the issue does not affect practice/method content or generation
    When the issue is triaged
    Then the issue is omitted entirely
    And no status or resolution columns are written

  Scenario: Duplicate or unclear issue
    Given an issue that duplicates an existing resolved issue or lacks sufficient detail
    When the issue is triaged
    Then the issue is declined with a clear rationale in Resolution Summary

  # --- Triage Decision: Resolution Approach ---

  Scenario: Direct fix
    Given an actionable issue with a clear, bounded problem
    When resolution approach is determined
    Then "Fix" is chosen
    And the plan specifies exact L1 actions

  Scenario: Root cause improvement
    Given an issue reporting a symptom whose root cause is broader
    When resolution approach is determined
    Then "Improve" is chosen
    And the plan addresses the root cause, not just the symptom

  Scenario: Intentional behaviour reported as issue
    Given an issue reporting behaviour that is by design
    When resolution approach is determined
    Then "Decline" is chosen
    And the rationale explains why the behaviour is intentional

  # --- Bundle Resolution ---

  Scenario: Document found locally
    Given the reported document exists in practices/ or baselines/
    When the document is located
    Then the local file path is used directly

  Scenario: Document found in local bundle
    Given the reported document is not in practices/ or baselines/
    But a .keleo bundle containing it exists in bundles/
    When the document is located
    Then the bundle is extracted to /tmp/keleo-extract/
    And the document is copied to the appropriate working directory

  Scenario: Document requires remote download
    Given the reported document is not found locally or in bundles/
    And keleo-studio-gas credentials are configured
    When the document is located
    Then the bundle is downloaded from keleo-studio-gas
    And extracted and copied to the working directory

  Scenario: Document not found anywhere
    Given the reported document cannot be found locally or remotely
    When the document is located
    Then the issue status is set to "Planned"
    And the Resolution Summary explains the document could not be located

  # --- Execution Delegation ---

  Scenario: L1 fix via update-method
    Given an issue requiring content fixes to an existing practice
    When the plan is executed
    Then /update-method is invoked with the document path, baseline, and fix requirements
    And the skill's full lifecycle runs (assess, fix, validate, rebundle)

  Scenario: Multiple issues on same document
    Given three issues all affecting the same practice document
    When the plan is executed
    Then all three are grouped into a single /update-method invocation
    And fix requirements from all issues are combined in the brief

  Scenario: L2 skill/utility improvement
    Given an issue requiring a keleo-pgen-llm skill or utility change
    When the plan is executed
    Then the specific file is modified directly
    And existing functionality is verified not to break

  # --- Register Updates ---

  Scenario: Resolved issue written back
    Given an issue has been successfully resolved
    When the register is updated
    Then Status is set to "Resolved"
    And Resolution Summary contains 1-3 sentences
    And Practice/Method Changes describes L1 changes with file paths
    And keleo-pgen-llm Changes describes L2 changes or "N/A"
    And keleo-language Changes describes L3 changes or "N/A"

  Scenario: Incremental register updates
    Given five issues are being processed
    When each issue is resolved
    Then the register is updated immediately after each resolution
    And not batched until all five are complete

  # --- Question handling ---

  Scenario: Question with no code change
    Given an issue with Type "Question"
    And the answer does not require any content or code changes
    When the issue is triaged and resolved
    Then Resolution Summary contains the answer
    And Status is set to "Resolved"
    And change columns are set to "N/A"

  Scenario: Question revealing a real issue
    Given an issue with Type "Question"
    And investigating the question reveals an actual defect
    When the issue is triaged
    Then it is treated as Type "Issue"
    And resolution levels are assigned based on the defect scope
