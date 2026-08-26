# Practice Language Validation Rules
#
# Gherkin-style behavioural specifications for generated practice JSON.
# Enforced programmatically by utils/eval-skill-output.py and utils/assess-practice.py.
# Referenced from generate-method SKILL.md — extracted to reduce skill context size.

Feature: Alpha Relationship Integrity

  Rules governing alpha hierarchy, parent relationships, and semantic connections.
  From references/semantics.md Sections 4.1, 6.1, 6.2.

  Scenario: No floating alphas (@rule:semantic-001)
    Given a new alpha is defined that does not exist in the baseline
    When Phase 3 generates the alpha JSON
    Then the alpha has exactly one of contributesTo or mapsTo
    And the target resolves to a baseline, practice-local, or dependency alpha

  Scenario: contributesTo and mapsTo are mutually exclusive (@rule:semantic-002)
    Given a new alpha declares a parent relationship
    When the alpha JSON is generated
    Then the alpha has contributesTo or mapsTo but never both

  Scenario: mapsTo variants match parent states exactly (@rule:semantic-003)
    Given a new alpha has mapsTo pointing to a parent alpha
    When the alpha's states are generated
    Then the state names and sequence exactly match the parent alpha's states

  Scenario: mapsTo variant names omit parent type (@rule:semantic-010)
    Given a new alpha has mapsTo pointing to a parent alpha
    When the alpha name is chosen
    Then the alpha name does not contain the parent alpha's name
    And the alias name (if present) does not contain the parent alpha's name

  Scenario: Redeclared alphas have no contributesTo or mapsTo (@rule:semantic-005)
    Given an alpha name matches a baseline or parent practice alpha
    When the alpha is included in the practice JSON
    Then the alpha has neither contributesTo nor mapsTo
    And only practice-specific checklists, narratives, and Gherkin guidance are added

  Scenario: Competency level names match baseline exactly (@rule:semantic-006)
    Given an activity or persona references a competency level
    When the competencyLevelName value is set
    Then the value exactly matches a CompetencyLevel.name from the baseline for that competency
    And level names are extracted with python3 utils/extract-reference-names.py <baseline>.json --sections competencies

  Scenario: relatesTo only on new alphas (@rule:semantic-007)
    Given an alpha is a redeclaration of a baseline alpha
    When the alpha JSON is generated
    Then no relatesTo array is added (baseline relationships are inherited)

  Scenario: relatesTo entries have required fields (@rule:semantic-008)
    Given a new alpha defines relatesTo relationships
    When the relatesTo array is generated
    Then every entry has relationship, alphaName, and direction fields
    And direction is one of outgoing, incoming, or mutual

  Scenario: contributesToState references valid parent state (@rule:semantic-009)
    Given a state on a new alpha declares contributesToState
    When the state JSON is generated
    Then the contributesToState value is a valid state name on the parent alpha referenced by contributesTo or mapsTo

  Scenario: Baseline references are case-sensitive (@rule:semantic-011)
    Given the practice references baseline elements (alphas, focuses, activitySpaces, competencies)
    When symbolic reference values are set
    Then every reference exactly matches the baseline element's name (case-sensitive)


Feature: Work Product Relationship Integrity

  Rules governing mapsTo and partOf on work products (mirrors alpha relationship rules).

  Scenario: Work product mapsTo variants match parent LODs exactly (@rule:semantic-012)
    Given a new work product declares mapsTo pointing to a parent work product
    When the work product JSON is generated
    Then the variant's LOD names and sequence exactly match the parent work product's LODs
    And checklists within each LOD are domain-specific (not duplicated from parent)

  Scenario: Work product mapsTo naming convention (@rule:semantic-013)
    Given a work product has mapsTo
    When the work product name is assigned
    Then the name does NOT contain the parent work product's name (IS-A makes it redundant)

  Scenario: mapsTo and partOf are mutually exclusive on work products (@rule:semantic-014)
    Given a work product is defined
    When relationship properties are set
    Then the work product has at most one of mapsTo or partOf, never both


Feature: Narrative Quality

  Rules governing narrative structure, naming, self-containment, and citation linkage.

  Scenario: Narratives are structured objects (@rule:narrative-001)
    Given a narrative is defined on any element or at practice level
    When the narrative JSON is generated
    Then the narrative has narrativeTypeName and narrativeContexts array
    And each context has seq, narrativeElementName, and context fields

  Scenario: Narrative names describe subject matter (@rule:narrative-003)
    Given a narrative has a name and description
    When the narrative JSON is generated
    Then the name describes the subject matter, not the template type
    And the description explains what the narrative covers, not the framework structure
    And contexts contain direct story content without mentioning the narrative type

  Scenario: Narrative contexts are self-contained (@rule:narrative-005)
    Given a narrative has contexts with narrativeElementName labels
    When the context strings are generated
    Then each context is coherent without its element heading visible
    And bare lists include a framing introduction sentence

  Scenario: Narratives placed on correct elements (@rule:narrative-002)
    Given a narrative describes a specific alpha, activity, or work product
    When the narrative is attached in the JSON
    Then element-specific narratives are on the element's narratives[] property
    And only practice/method-level narratives go in the top-level narratives[] array

  Scenario: All narratives have citation references (@rule:narrative-006)
    Given a narrative is defined
    When the narrative JSON is generated
    Then the narrative includes a citationNames array with at least one citation reference


Feature: Element Naming

  Rules governing element names, descriptions, and name uniqueness.

  Scenario: Descriptions are single sentences under word limit (@rule:naming-001)
    Given an element has a description field
    When the description is generated
    Then element descriptions are at most 20 words
    And state and LOD descriptions are at most 12 words

  Scenario: Checklist names are noun-phrase labels (@rule:naming-002)
    Given a checklist item on an alpha state has name and description
    When the checklist JSON is generated
    Then the name is a short noun phrase (not truncated from the description)
    And the name is not identical to the description

  Scenario: Global name uniqueness across element types (@rule:naming-003)
    Given multiple PracticeElement types are defined (alphas, workProducts, activities, personas, patterns)
    When all element names are collected
    Then no name appears in more than one element type

  Scenario: LOD names describe content maturity (@rule:naming-004)
    Given a work product has levels of detail
    When LOD names are chosen
    Then names describe what the document looks like at that fidelity level, following the rubric in references/workproduct-assessment-rubric.csv (Summarised, Structured, Elaborated, Actionable)
    And every LOD covers the same full scope -- the difference between levels is depth, not breadth or temporal progression
    And names do not use generic labels ("Level 1", "Basic") or concern progression terms ("Established", "Optimized", "Evolved")
    And names do not describe lifecycle events or temporal stages (e.g., "Work Completed", "Definition of Done Met")
    And the litmus test passes: the name answers "what does this document contain?" not "where does the concern stand?"

  Scenario: Activity names differ from ActivitySpace names (@rule:naming-005)
    Given an activity is assigned to an ActivitySpace
    When the activity name is chosen
    Then the activity name is distinct from the ActivitySpace name


Feature: Coverage Completeness

  Rules governing minimum counts and activity-to-state coverage.

  Scenario: Alpha state minimum (@rule:coverage-001)
    Given an alpha is defined in the practice
    When states are assigned to the alpha
    Then the alpha has at least 3 states

  Scenario: Work product LOD minimum (@rule:coverage-002)
    Given a work product is defined in the practice
    When levels of detail are assigned
    Then the work product has at least 2 levels of detail

  Scenario: Alpha states have supporting LODs (@rule:coverage-003)
    Given an alpha state exists on a new (non-baseline) alpha
    When work product LODs are checked
    Then at least one LOD has contributesTo targeting the alpha state

  Scenario: Patterns cover all practice alphas (@rule:coverage-004)
    Given a pattern is defined in the practice
    When PatternViews are checked
    Then every practice alpha appears in at least one PatternView
    And each alpha appears in every view (backfilled if needed)

  Scenario: Alpha states have supporting activities (@rule:coverage-005)
    Given an alpha state beyond the initial state exists on a new alpha
    When activity contributesTo references are checked
    Then at least one activity has contributesTo targeting the alpha state


Feature: Terminology Aliasing

  Rules governing practice element aliases and keywords.

  Scenario: One alias per element maximum (@rule:aliasing-001)
    Given the practice defines terminology aliases
    When aliases are assigned to baseline elements
    Then each baseline element has at most one alias

  Scenario: Alias names excluded from structural references (@rule:aliasing-002)
    Given an alias maps a baseline name to a domain-specific name
    When the practice JSON uses symbolic references (alphaName, contributesTo, activitySpaceName, etc.)
    Then only canonical baseline names appear in structural reference fields
    And alias names never appear in structural reference fields

  Scenario: Keyword count within range (@rule:aliasing-003)
    Given the practice defines a keywords array
    When keywords are generated
    Then the array contains between 10 and 20 keywords


Feature: Structural Integrity

  Validates that generated JSON has correct shape, required sections, and resolved cross-references.

  Scenario: JSON has correct kind discriminator (@rule:structural-001)
    Given Phase 3 generates a JSON file
    When the JSON is validated
    Then the kind property is "practice" for single practices, "method" for multi-practice methods

  Scenario: All required sections present in JSON (@rule:structural-002)
    Given Phase 3 generates a practice JSON
    When the JSON is validated
    Then alphas, activities, workProducts, patterns, and citations arrays are present and non-empty

  Scenario: Pattern cross-references resolve (@rule:structural-003)
    Given a pattern references alpha names and state names in patternViews
    When Phase 3 generates the JSON
    Then every alphaName in patternViews.alphaStates resolves to an alpha in the practice or baseline
    And every stateName resolves to a valid state on that alpha

  Scenario: Activity-alpha cross-references resolve (@rule:structural-004)
    Given an activity has contributesTo entries referencing alphas and states
    When Phase 3 generates the JSON
    Then every alphaName and stateName in activity contributesTo resolves to a defined alpha and state

  Scenario: Activity-work product cross-references resolve (@rule:structural-005)
    Given an activity has worksOn entries referencing work products and LODs
    When Phase 3 generates the JSON
    Then every workProductName and levelOfDetailName in worksOn resolves to defined elements

  Scenario: Work product partOf references resolve (@rule:structural-006)
    Given a work product has a partOf property
    When Phase 3 generates the JSON
    Then the partOf value resolves to a WorkProduct.name in the same practice, a dependency practice, or the baseline
    And the work product does not reference itself
    And no circular partOf chains exist (A partOf B, B partOf A)


Feature: Process Compliance

  Validates that the three-phase pipeline is executed in order with proper gates.

  Scenario: Phase 1 completed before Phase 2 (@rule:process-001)
    Given the three-phase pipeline is being executed
    When Phase 2 mapping begins
    Then 01-analysis-report.md exists with all 8 required sections
    And analysis has sufficient depth (5+ numbered subsections and 3+ source references)

  Scenario: Phase 2 completed before Phase 3 (@rule:process-002)
    Given the three-phase pipeline is being executed
    When Phase 3 JSON generation begins
    Then 02-mapping-guide.md exists with all 7 required sections
    And at least 3 alphas, 5 activities, and 1 pattern are mapped

  Scenario: Validation run after JSON generation (@rule:process-003)
    Given Phase 3 has generated a JSON file
    When the phase is marked complete
    Then validate-practice-json.py has been run with 0 schema errors
    And assess-practice.py has been run with 0 error-severity issues


Feature: Checklist Bloat Prevention

  Rules governing checklist counts and near-duplicate detection.
  Prevents quota-driven inflation of success criteria.

  Scenario: Checklist count within range (@rule:bloat-001)
    Given an alpha state has a checklist array
    When the checklist items are counted
    Then the count is typically 3-7 items
    And a count above 8 produces a warning
    And a count above 12 produces an error (unless explicitly justified)

  Scenario: No near-duplicate checklist names within a state (@rule:bloat-002)
    Given an alpha state has multiple checklist items
    When checklist names are normalized (lowercase, strip articles/prepositions, sort tokens)
    Then no two names within the same state normalize to the same token set

  Scenario: Cross-alpha criteria not duplicated via relatesTo (@rule:bloat-003)
    Given alpha A has relatesTo alpha B
    When checklists are authored for both alphas
    Then A's state checklists do not restate B's criteria
    And shared verification is expressed through a Work Product whose LODs contributesTo both alphas

  Scenario: evidencedBy stays optional (@rule:bloat-004)
    Given a checklist item is defined on an alpha state
    When the checklist JSON is generated
    Then evidencedBy is never required by generation prompts or assessment rules
    And empty evidencedBy arrays are valid
