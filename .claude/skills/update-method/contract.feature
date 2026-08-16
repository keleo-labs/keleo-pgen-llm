# Behavioural Contract: update-method
#
# Defines what this skill promises to do, what inputs it expects,
# what outputs it produces, and what constraints it operates under.

Feature: Practice/Method Update to Latest Guidance

  Background:
    Given one or more existing practice/method/baseline JSON files are provided
    And the user invokes /update-method

  Scenario: Auto-fix mode
    Given assess-practice.py recommends suggestedUpdateMode "auto-fix"
    When auto-fix utilities run
    Then all issues are resolved without user interaction
    And re-assessment confirms 0 errors
    And version is bumped (patch)
    And .keleo package is rebuilt

  Scenario: Remap mode (Phase 2 → 3)
    Given assess-practice.py recommends suggestedUpdateMode "remap"
    And user confirms remap mode
    When existing content is extracted as Phase 1 analysis
    Then Phase 2 mapping applies latest guidance (from generate-method SKILL.md)
    And Phase 3 generates updated JSON
    And diff-practice-json.py shows what changed vs original
    And version is bumped (minor)

  Scenario: Full reanalysis mode (Phase 1 → 2 → 3)
    Given assess-practice.py recommends suggestedUpdateMode "full-reanalysis"
    And user provides source materials
    When all three phases execute
    Then outputs follow same quality gates as generate-method
    And version is bumped (minor)

  Scenario: Add/update references (Mode 3)
    Given user requests reference discovery
    When references are mapped to alpha+state anchors
    Then every reference has at least one links entry with valid URI
    And references are presented to user for approval before applying
    And version is bumped (patch)

  Scenario: Assessment before any update
    When the update workflow begins
    Then assess-practice.py runs first
    And dependencies are resolved via discover-dependencies.py
    And backup-practice.py creates a timestamped backup

  Scenario: Version management
    Given an update completes successfully
    When apply-versioning.py runs
    Then schemaVersion matches deps/language.schema.json
    And dependencyVersions are populated from resolved dependencies
    And version bump matches update mode (patch for auto-fix/references, minor for remap/reanalysis)
