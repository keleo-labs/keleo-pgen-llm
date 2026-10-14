Feature: Plan from Feedback — keleo-pgen-llm
  As a practice engineer
  I want register issues published to the project that owns them, and this project's
  issues triaged and resolved from its tracker
  So that defects are visible to their maintainers and every change traces to an issue

  Background:
    Given a Google Sheet register holds reports with full internal detail in columns A-V
    And keleo-labs/keleo-pgen-llm is a public GitHub repository with issues enabled
    And the feedback foundation defines the workflow, routing and sanitisation rules

  # --- Publishing (this project only) ---

  Scenario: Open row published to its owning project
    Given a register row has Status "New" and no Issue URL
    And its fix lands in a skill, prompt or utility
    When the publish step runs
    Then a sanitised issue is created on keleo-labs/keleo-pgen-llm
    And the issue body opens with the register row number
    And the Issue URL and Issue State are written to columns U and V

  Scenario: Practice content is never published
    Given a register row reports a defect in a practice, method or baseline document
    When the publish step runs
    Then no issue is created on any tracker
    And Issue State is set to "Not Published"
    And the row is worked from the register

  Scenario: Practice defect caused by the generator
    Given a register row reports a defect in a practice document
    And the cause is a prompt or utility that would repeat it
    When the publish step runs
    Then an issue is published about the generator only
    And the practice fix stays in the register
    And the published issue does not name the practice that revealed it

  Scenario: Routing asks what must change, not where it was seen
    Given a register row names a practice as its document
    And its fix lands in a utility
    When the owning project is determined
    Then it is published as a keleo-pgen-llm issue

  Scenario: Content routing is refused mechanically
    Given a caller attempts to file practice content on a tracker
    When forge-issues.py is invoked for it
    Then it refuses with the reason rather than creating an issue

  Scenario: Row owned by another project
    Given a register row describes a defect in the bundle repository API
    When the publish step runs
    Then the issue is created on the internal GitLab project that owns it
    And no attempt is made to resolve it from here

  Scenario: Row content determines the owner, not its Document Name
    Given a register row names a practice as its document
    And its content describes a gap in the Practice Language itself
    When the owning project is determined
    Then the issue is routed to keleo-language

  Scenario: Draft carrying internal detail is blocked
    Given a drafted issue body names a customer, a practice or an internal URL
    When it is checked before creation
    Then creation is refused with the offending terms named
    And the draft is rewritten rather than the denylist weakened

  Scenario: Internal tracker skips sanitisation
    Given the owning project's tracker is on internal GitLab
    When the issue is created
    Then the full detail is carried without redaction

  Scenario: Nothing publishable survives sanitisation
    Given a register row cannot be stated safely in general terms
    When the publish step runs
    Then no issue is created
    And Issue State is set to "Not Published" with a reason recorded

  Scenario: Near-duplicate draws a comment
    Given an issue already exists whose title closely matches the draft
    When the publish step runs
    Then a comment naming the new register row is added to the existing issue
    And no second issue is created

  Scenario: First publication run is approved by a person
    Given no issues have been published before
    When the publish step is ready to create issues
    Then the drafted bodies are shown for review
    And nothing is created until approved

  # --- Working the queue ---

  Scenario: Queue comes from the tracker
    Given issues exist on keleo-labs/keleo-pgen-llm
    When the resolution workflow begins
    Then the queue is read from the tracker rather than the register

  Scenario: Register-linked issue pulls its detail
    Given an issue body names a register row
    When it is triaged
    Then the row supplies the document, element and context the issue cannot carry

  Scenario: Natively-filed issue has no row
    Given an issue was filed directly on the tracker by someone outside the team
    When it is triaged
    Then it is worked the same way
    And resolution is recorded on the issue alone

  # --- Levels ---

  Scenario: L1 content fix is delegated
    Given an issue reports wrong content in a practice document
    When the fix is applied
    Then /update-method is invoked with the file, the fixes and the baseline
    And the practice JSON is not hand-edited

  Scenario: Several issues against one document
    Given three open issues name the same practice
    When they are executed
    Then they are combined into a single /update-method invocation

  Scenario: Systemic generation problem
    Given an issue reveals a defect that would recur in the next practice
    When the resolution is planned
    Then the skill, prompt or utility that produced it is fixed as well as the document

  Scenario: Schema gap escalates rather than being fixed
    Given an issue reveals a gap in the Practice Language
    When the resolution is planned
    Then an issue is filed on keleo-language
    And the schema is not edited from this project

  # --- Closing ---

  Scenario: Change links to its issue
    Given a commit resolves an issue
    When the commit message is written
    Then it carries "Refs" or "Closes" with the owning repository and issue number

  Scenario: Both systems updated on close
    Given a fix is complete and validated
    When the issue is closed
    Then the resolution is commented on the issue before closing
    And the register row's Status, resolution columns and Issue State are updated

  Scenario: Register write fails after the issue is closed
    Given the issue has been closed
    And writing the register row fails
    Then the intended values are reported so they can be applied by hand

  # --- Validation ---

  Scenario: Content change is validated before closing
    Given a practice document was changed
    When the change is verified
    Then eval-skill-output.py reports error_pass_rate 1.0
    And the affected bundles are rebuilt

  Scenario: Defect class checked across the corpus
    Given a defect is found in one document
    When the resolution is planned
    Then scan-corpus.py establishes whether it occurs elsewhere
    And any further instances are filed rather than silently left
