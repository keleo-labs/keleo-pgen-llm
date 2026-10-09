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

  Scenario: Verification gate at every phase
    Given a phase has completed and passed mechanical validation
    When the verification gate runs
    Then the verifiers named in verification-foundation/verifiers/phase-<N>.md have been launched
    And each has written findings to <output-dir>/_verification/phase-<N>-<verifier>.json
    And verification-gate.py has been run with --gate and --expect naming every verifier launched
    And the phase does not advance while a blocking error survives reconciliation
    And the verdict is recorded in 00-prompt-history.md as a decision

  Scenario: Source fidelity blocks untraceable content
    Given the Phase 1 or Phase 2 verification gate runs
    When a structural claim cannot be traced to a source after directed searching
    Then the finding is reported at error severity
    And the gate exits 1
    And the content is corrected, or the finding is dismissed with the source span cited as evidence

  Scenario: Phase 3 semantic judgement is verified
    Given Phase 3 has generated JSON from a mapping guide
    When the generation-drift verifier runs
    Then outcome measureDescription asserts no metric the mapping guide does not state
    And no element appears in the JSON that is absent from both the mapping guide and the baseline
    And no element specified in the mapping guide is missing from the JSON
    And any fix applied in response is followed by rebundling
