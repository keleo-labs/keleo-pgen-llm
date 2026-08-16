# Behavioural Contract: generate-method
#
# Defines what this skill promises to do, what inputs it expects,
# what outputs it produces, and what constraints it operates under.

Feature: Practice Generation from Methodology Documentation

  Background:
    Given source methodology documentation is provided (URLs, PDFs, or files)
    And the user invokes /generate-method

  Scenario: Single practice generation
    Given the source methodology maps to 3-7 baseline alphas
    And ONE primary alpha is identifiable
    When the three-phase pipeline completes
    Then practices/<name>/01-analysis-report.md exists (~30-50K words)
    And practices/<name>/02-mapping-guide.md exists (~40-60K words)
    And bundles/<name>.keleo exists and passes --verify
    And the .keleo package contains baseline + practice documents
    And validate-practice-json.py reports 0 schema errors
    And assess-practice.py reports 0 error-severity issues

  Scenario: Method generation (multi-practice)
    Given the source methodology maps to 8+ baseline alphas
    And multiple primary alphas are identifiable
    When the delineation gate determines method structure
    Then each practice gets its own mapping section in 02-mapping-guide.md
    And each practice JSON validates independently
    And bundles/<name>.keleo contains externalized method + all practice documents
    And no practice degenerates to activities-only (all have alphas, WPs, patterns)

  Scenario: Planning phase is mandatory
    When the skill is invoked
    Then EnterPlanMode is called before any phase execution
    And the plan includes source material assessment and execution roadmap

  Scenario: Phase compaction between phases
    When Phase 1 completes
    Then context is compacted before Phase 2 begins
    And Phase 2 reads phase-2-mapping.md prompt (not SKILL.md phase guidance)
    And the same compaction applies between Phase 2 and Phase 3

  Scenario: Validation gates
    Given Phase 3 has generated JSON
    When validation runs
    Then validate-practice-json.py passes with 0 schema errors
    And assess-practice.py passes with 0 error-severity issues (using --baseline and --parent as needed)
    And eval-skill-output.py error_pass_rate equals 1.0

  Scenario: .keleo packaging
    Given all practice JSONs pass validation
    When packaging runs
    Then package-keleo.py creates a .keleo archive with --verify
    And all transitive dependencies are included in topological order
    And _effective-context.json is never included as a document
