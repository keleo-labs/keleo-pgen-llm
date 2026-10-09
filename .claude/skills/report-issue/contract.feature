Feature: Report Issue
  As a practice consumer
  I want to record issues, enhancements, and questions in the feedback register
  So that they can be triaged and resolved by plan-from-feedback

  Background:
    Given a Google Sheet issue register exists with structured table columns A-T
    And the register URL is stored in .claude/user-config.json
    And the skill writes only the input columns A-P, never the resolution columns Q-T

  # --- Configuration ---

  Scenario: First-time reporter email capture
    Given .claude/user-config.json does not contain issueReporterEmail
    When the skill is invoked
    Then the local git user.email is proposed to the user for confirmation
    And the confirmed address is saved as issueReporterEmail in user-config.json

  Scenario: Reporter email already configured
    Given .claude/user-config.json contains issueReporterEmail
    When the skill is invoked
    Then the stored address is used without prompting

  Scenario: Register not configured
    Given .claude/user-config.json contains no issueRegisterSpreadsheetId or issueRegisterUrl
    When the skill is invoked
    Then the user is prompted for the register URL
    And the ID is saved under the same keys plan-from-feedback reads

  # --- Invocation modes ---

  Scenario: Mid-execution invocation skips capture
    Given another skill invokes this skill with a drafts file path
    When the skill runs
    Then the user is not asked to describe any issue
    And the drafts are filed as the calling skill wrote them

  Scenario: Mid-execution invocation appends without confirmation
    Given a mid-execution invocation with validated, non-duplicate drafts
    When the append runs
    Then no confirmation round is presented to the user
    And the rows are written with Status "New"

  Scenario: Mid-execution duplicate of an open issue
    Given a mid-execution draft matches an open row above the similarity threshold
    When duplicates are checked
    Then that draft is not filed
    And the covering row number is named in the report returned to the calling skill

  Scenario: Mid-execution draft fails validation
    Given a mid-execution draft is missing a required field
    When the drafts are validated
    Then that draft is not filed
    And it is reported back unfiled rather than completed with invented detail

  Scenario: Mid-execution enrichment cannot resolve a document
    Given a mid-execution draft has no document version or kind
    And the document resolves to multiple candidates
    When document context is enriched
    Then the user is not asked to disambiguate
    And the unresolved fields are left blank and noted in the report

  Scenario: Mid-execution report is compact
    Given a mid-execution invocation completes
    When the skill returns
    Then the output lists only rows filed and rows skipped with reasons
    And no further commentary is added to the conversation

  # --- Capture ---

  Scenario: Single issue capture
    Given the user describes one problem with a practice document
    When the issue is captured
    Then exactly one register row is drafted
    And it has a Type, a Summary under 120 characters, and a Description

  Scenario: Multiple issues in one message
    Given the user describes three unrelated problems in a single message
    When the issues are captured
    Then three separate register rows are drafted
    And unrelated observations are not merged into one row

  Scenario: One problem with several symptoms
    Given the user describes one defect that manifests in several places
    When the issue is captured
    Then one register row is drafted
    And the symptoms are described within that row's Description

  Scenario: Classify a missing-content report
    Given the user reports that content is absent or thin
    When the type is classified
    Then Type is "Enhancement"

  Scenario: Classify a wrong-content report
    Given the user reports content that is incorrect or contradicts the source methodology
    When the type is classified
    Then Type is "Issue"

  Scenario: Classify a design query
    Given the user asks why something was modelled a certain way without asserting it is wrong
    When the type is classified
    Then Type is "Question"

  Scenario: Ambiguous type
    Given the report could reasonably be an Issue or an Enhancement
    When the type is classified
    Then the user is asked to choose via AskUserQuestion

  # --- Enrichment ---

  Scenario: Document resolved locally
    Given the reported document exists in practices/ or baselines/
    When document context is enriched
    Then Document Name is the canonical name from the JSON
    And Document Version and Document Kind are read from the document metadata

  Scenario: Document name is ambiguous
    Given the document name resolves to multiple candidates
    When document context is enriched
    Then the user is asked which document they meant

  Scenario: Document not found anywhere
    Given the document cannot be resolved locally or pulled from the remote repository
    When document context is enriched
    Then Document Name is recorded as the user gave it
    And Document Version and Document Kind are left blank rather than invented

  Scenario: Element located
    Given the issue concerns a named element in a resolved document
    When element context is enriched
    Then Selected Element is the exact name from the document
    And Element Type is the element type reported by --locate

  Scenario: Element name paraphrased
    Given the user's element name does not match any element exactly
    But close matches exist in the document
    When element context is enriched
    Then the user is asked to confirm the intended element from the suggestions

  Scenario: Issue reports a missing element
    Given the issue is that an expected element does not exist
    When element context is enriched
    Then Selected Element is left blank
    And the expected element is named in the Description

  Scenario: Relationship between two elements
    Given the issue concerns a relationship between two elements
    When element context is enriched
    Then Secondary Element and Secondary Type are populated by the same lookup

  Scenario: Studio UI issue
    Given the user reports a Keleo Studio rendering or interaction problem
    When the issue is captured
    Then the issue is still recorded in the register
    And it is not declined or withheld by this skill

  # --- Validation and duplicates ---

  Scenario: Draft fails validation
    Given a draft is missing a required field
    When the drafts are validated
    Then the append is not attempted
    And the missing field is captured before proceeding

  Scenario: Duplicate of an open issue
    Given a draft closely matches an existing row with status New, Planned, or In Progress
    When duplicates are checked
    Then the user is told which row already covers it
    And the user chooses whether to skip or file anyway

  Scenario: Duplicate of a resolved issue
    Given a draft closely matches an existing row with status Resolved or Closed
    When duplicates are checked
    Then the possible regression is reported to the user
    And the earlier row number is referenced in the new Description

  Scenario: No silent drops or silent duplicates
    Given any duplicate match is found
    When duplicates are checked
    Then the issue is neither dropped nor filed without telling the user

  # --- Append ---

  Scenario: Confirmation before writing on direct invocation
    Given the skill was invoked directly by the user
    And validated drafts with no blocking duplicates
    When the append is about to run
    Then the drafts are presented to the user
    And no row is written until the user confirms

  Scenario: Rows appended
    Given the user confirms the drafts
    When the append runs
    Then each row is written inside the register table's column range
    And the table range is extended to cover the new rows
    And Status is "New" on every appended row
    And Timestamp, Email, and Page are set by the utility

  Scenario: Resolution columns untouched
    Given rows are appended
    When the register is inspected
    Then columns Q-T of the new rows are empty

  Scenario: Append failure preserves work
    Given the append call fails
    When the error is handled
    Then the drafts are reported to the user in the conversation
    And the scratch JSON file is retained for retry

  Scenario: Handoff to triage
    Given rows were appended successfully
    When the skill completes
    Then the written row numbers are reported
    And the user is told plan-from-feedback picks up New rows on its next run
