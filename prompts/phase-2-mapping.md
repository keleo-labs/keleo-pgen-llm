# Phase 2: Mapping Prompt

## Context

You are conducting **Phase 2: Mapping** of a methodology translation workflow. This phase maps the structured analysis from Phase 1 into a standardized format using a baseline practice framework and semantic guidance.

## Objective

Transform the Phase 1 analysis into a mapping specification that:
- Maps source concerns to baseline Alphas
- Maps source work products to baseline Work Products
- Maps source activities to baseline Activities and Activity Spaces
- Maps source personas to baseline Personas and Persona Groups
- Maps source workflows to baseline Patterns
- Creates a comprehensive mapping guide for JSON generation (Phase 3)

## Resources Available

You have access to the following resources via the Read tool:

1. **practices/<practice-name>/01-analysis-report.md** (Phase 1 output)
   - Structured analysis of source methodology
   - Read this completely before starting mapping

2. **Baseline Practice JSON** (user-provided)
   - User will specify the baseline practice file path
   - Example: `deps/platform-adoption-kernel.json`
   - Defines canonical framework (alphas, activity spaces, competencies, etc.)

3. **references/semantics.md**
   - Comprehensive semantic guidance for Practice Language
   - Rules for alpha handling (redeclaration vs specialization)
   - Orthogonal tagging taxonomy
   - Checklist standards
   - Narrative management
   - Pattern orchestration
   - READ THIS THOROUGHLY before mapping

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `practices/<practice-name>/01-analysis-report.md`**
   - Review all extracted concerns, work products, activities, competencies, personas, workflows
   - Understand the practice structure (single vs multiple practices)

2. **Read the baseline practice JSON** (path provided by user)
   - **CRITICAL:** Read BOTH names AND descriptions for semantic understanding
   - For each baseline element, understand:
     - **Alphas**: Read alpha description + all state descriptions to understand full scope and progression
     - **Competencies**: Read competency description + all level descriptions to understand expertise range
     - **Activity Spaces**: Read description to understand boundary and purpose
     - **Focuses**: Read description to understand categorization intent
     - **Narrative Types**: Note available types for pattern/narrative selection
   - Build semantic index, not just name list - descriptions reveal nuances critical for mapping decisions
   - Example: Don't just note "Team" alpha exists - understand its full description to assess if source content enriches it or specializes it

3. **Read `references/semantics.md`**
   - Focus on sections:
     - Section 3.1.2: Orthogonal Tagging Taxonomy
     - Section 3.3: Checklists and Dynamic State-Gating
     - Section 4: Alpha-State Trajectory (especially 4.1: Baseline Isolation Rules)
     - Section 5: Work Product Elements
     - Section 6: Execution Boundaries and Organizational Roles
     - Section 7: Narrative Management
     - Section 8: Lifecycle Orchestration (Patterns)
     - Section 9.2.5: Redeclaration vs Specialization Decision Framework

### Step 2: Map Metadata (For Each Practice)

For each practice identified in Phase 1:

**Practice Metadata:**
- **Name**: Exact name from Phase 1
- **Description**: Single sentence (from Phase 1, refined if needed)
- **Tags**: Convert Phase 1 tags to orthogonal structure
  ```
  tags: {
    domainTags: [technical disciplines],
    lifecycleTags: [temporal frameworks],
    organizationalTags: [business units]
  }
  ```
- **Keywords**: 5-10 keywords for search/discovery
- **Narrative**: Create practice-level narrative using baseline narrative type
  - Choose appropriate type: STAR, Hero's Journey, Three-Act Structure, etc.
  - Map practice objectives/outcomes to narrative elements

**Method Metadata (if multiple practices):**
- **Method Name**: Overarching methodology name
- **Method Description**: Single sentence covering all practices
- **Method Narrative**: High-level narrative connecting practices
- **List of Practice Names**: All practices included

### Step 3: Map Citations

For each citation from Phase 1:
- Extract to standard Citation format:
  ```
  Name: Exact source title
  Description: 1 sentence summary
  Authors: [array of author names]
  Date: Publication year
  Source: Publisher/journal
  URL: Retrieval URL (if applicable)
  ```

**CRITICAL:** Citations have NO narratives property (metadata only)

### Step 4: Map Concerns to Alphas

For EACH concern from Phase 1, apply the **Redeclaration vs Specialization Decision Framework** (semantics.md Section 9.2.5):

**CRITICAL FIRST STEP: Semantic Comparison**

Before deciding redeclaration vs specialization, compare source concern against baseline alpha DESCRIPTIONS (not just names):

1. **Read baseline alpha description carefully** - What is the full scope and intent?
2. **Read all baseline alpha state descriptions** - What progression is already defined?
3. **Compare source concern's scope to baseline alpha's described scope**:
   - Does source concern fit entirely within baseline description's scope? → Consider redeclaration
   - Does source concern address narrower/specialized subset? → Consider specialization
   - Does source concern address something semantically different? → New alpha (with contributesTo)

**Decision Questions:**
1. Is this concern **generally applicable** (universal to all uses of baseline alpha as described)?
   - YES → Redeclaration (enrich baseline alpha)
   - NO → Specialization (new alpha with contributesTo)

2. Does this concern use the **same state progression** as baseline alpha states describe?
   - YES → Redeclaration
   - NO → Specialization

**Example Decision Process:**
```
Source Concern: "Team Interactions"
Baseline Alpha: "Team" 
  Description: "People working together with a shared mission..."
  
Analysis:
- Team description covers team formation and collaboration
- Does NOT explicitly cover inter-team interaction patterns
- Team Interactions is related but has distinct progression
- Decision: SPECIALIZATION (contributesTo: Team)

Source Concern: "Cognitive Load Management"  
Baseline Alpha: "Team"
  Description: "People working together with a shared mission..."
  State: "Performing" - "Team delivers value effectively..."
  
Analysis:
- Cognitive load is universal team concern (sizing, scope)
- Fits within baseline Team description scope
- Enhances existing "Performing" state criteria
- Decision: REDECLARATION (add cognitive load checklists to Team states)
```

**Redeclaration (Enrichment):**
```
Alpha Name: [EXACT baseline alpha name]
Description: [EXACT baseline description - DO NOT CHANGE]
Focus Name: [baseline focus name]
States: [EXACT baseline states with ADDED checklists]
  State 1:
    Name: [baseline state name]
    Description: [baseline state description]
    Checklists: [baseline checklists + NEW practice-specific checklists from Phase 1 criteria]
  State 2: ...
Narrative: [NEW practice-specific context]
```

**Specialization (New Alpha):**
```
Alpha Name: [NEW descriptive name from Phase 1 concern]
Description: [From Phase 1 concern description]
Focus Name: [Value | Solution | Endeavor based on perspective]
contributesTo: [baseline alpha name this extends - REQUIRED!]
States: [NEW states from Phase 1 progressive states]
  State 1:
    Name: [from Phase 1]
    Description: [from Phase 1]
    Checklists: [from Phase 1 criteria]
  State 2: ...
Narrative: [from Phase 1 narrative]
```

**CRITICAL RULE:** ALL new alphas MUST have `contributesTo` pointing to a baseline alpha (NO FLOATING ALPHAS)

**Semantic Validation for contributesTo Decisions:**

For EACH new alpha (specialization), validate the contributesTo choice using the **State Alignment Heuristic** (semantics.md Section 9.2.5):

1. **List candidate parent alphas** from baseline that could semantically relate to this new alpha
2. **For EACH candidate parent:**
   - List the parent's state names
   - Compare to your new alpha's state names
   - Count semantic matches (exact names, conceptual synonyms, maturity parallels)
   - Calculate alignment score: matches / total states
3. **Apply decision rule:**
   - ≥70% alignment → Strong match, use this parent (high confidence)
   - 50-69% alignment → Moderate match, likely correct (verify with description fit)
   - 30-49% alignment → Weak match, review decision carefully
   - <30% alignment → No meaningful alignment, try different parent or reconsider as redeclaration
4. **Choose parent with highest alignment score**

**Document validation in mapping guide:**
```
Alpha: [New Alpha Name]
contributesTo: [Chosen Parent Alpha]

State Alignment Validation:
- Parent states: [list parent alpha states]
- New alpha states: [list new alpha states]
- Semantic matches: [list matching states with explanation]
- Alignment score: [X/Y states = Z%]
- Decision rationale: [why this parent is semantically appropriate]

Alternative considered: [other parent alpha and why rejected]
```

**Example Validation:**
```
Alpha: Internal Developer Platform
contributesTo: Platform Consumption Interface

State Alignment Validation:
- Parent states: Envisioned, Scoped, Available, Self Service, Optimized
- New alpha states: Scoped, Deployed, Catalog Available, Self-Service Functional, Optimized
- Semantic matches:
  * "Scoped" = "Scoped" (exact match)
  * "Catalog Available" ~ "Available" (catalog is available)
  * "Self-Service Functional" ~ "Self Service" (same concept)
  * "Optimized" = "Optimized" (exact match)
- Alignment score: 4/5 states = 80%
- Decision rationale: IDP is the consumption interface (portal, catalog, templates) through which developers access platform infrastructure

Alternative considered: Platform - rejected due to 0% state alignment (Platform states focus on infrastructure provisioning: Architecture Selected, Baselined, Provisioned, Ready, Hosting Assets)
```

**Validation Checklist for New Alphas:**
- [ ] contributesTo field present and references valid baseline alpha name
- [ ] State alignment calculated and ≥50%
- [ ] If alignment <70%, description alignment also verified
- [ ] If alignment <50%, decision justified or alpha reconsidered as redeclaration
- [ ] Alternative parents considered and documented
- [ ] Decision rationale provided explaining semantic fit

**Alpha Instances:**
If Phase 1 identified multiple concurrent instances of a concern (e.g., different team types):
```
Alpha Instance Name: [specific instance identifier]
Alpha Name: [parent alpha]
Description: [what this instance represents]
```

### Step 5: Map Work Products

For EACH work product from Phase 1:

**Determine if baseline defines similar work product:**
- YES → Redeclare baseline work product with additional LODs/checklists
- NO → Create new practice work product

**Work Product Structure:**
```
Work Product Name: [from Phase 1 or baseline]
Description: [single sentence from Phase 1]
Levels of Detail: [map Phase 1 levels]
  Level 1:
    Name: [descriptive only, NO "Level X:" prefix]
    Description: [single sentence, max 12 words]
    Seq: [1, 2, 3...]
    Checklists: [3-5 one-sentence characteristics from Phase 1]
    Contributes To: [AlphaContribution objects - which alpha/state this LOD proves]
      - Alpha Name: [alpha]
        State Name: [state]
  Level 2: ...
Narrative: [if Phase 1 provided additional context]
```

**Work Product Instances:**
If Phase 1 identified distinct variants:
```
Work Product Instance Name: [variant identifier]
Work Product Name: [parent work product]
Description: [what this variant represents]
```

**contributesTo REQUIRED on every LOD:**
- Each level of detail MUST specify which alpha states it evidences
- Array of {alphaName, stateName} objects

### Step 6: Map Personas and Persona Groups

**Map Competencies First:**
For each Phase 1 competency, match to baseline competencies:
- Use EXACT baseline competency names (case-sensitive)
- Map Phase 1 competency descriptions to baseline names:
  - Security/Compliance → "Platform Security And Compliance Enforcement"
  - Strategy/Alignment → "Platform Strategic Alignment"
  - Reliability/SRE → "Site Reliability"
  - Stakeholder/Representation → "Stakeholder Representation"
  - Engineering/Development → "Engineering"
  - Analysis/Research → "Analysis"
  - Leadership → "Leadership"
  - Management/Project → "Management"

**Map Personas:**
```
Persona Name: [from Phase 1]
Description: [single sentence from Phase 1]
Competencies: [CompetencyLevelReference objects]
  - Competency Name: [EXACT baseline competency name]
    Competency Level Name: [from baseline competency levels]
Tags: [orthogonal structure]
```

**Map Persona Groups (Teams):**
```
Persona Group Name: [team name from Phase 1]
Description: [single sentence from Phase 1]
Persona Names: [array of persona names - members of this team]
Tags: [organizational tags]
```

### Step 7: Map Activities

For EACH activity from Phase 1:

**Determine Activity Space:**
- Map to baseline Activity Space names (20 baseline activity spaces)
- OR: Create practice-specific activity space if source defines new boundary

**Activity Structure:**
```
Activity Name: [specific name - verb + specific object, NEVER same as activity space name]
Description: [single sentence from Phase 1]
Activity Space Name: [baseline or practice activity space]
Focus Name: [Value | Solution | Endeavor]
Contributes To: [AlphaContribution objects from Phase 1 "Outcomes"]
  - Alpha Name: [alpha]
    State Name: [state]
Works On: [WorkProductContribution objects from Phase 1 "Work Products Used"]
  - Work Product Name: [work product]
    Level Of Detail Name: [level]
Required Competencies: [array of EXACT baseline competency names]
Recommended Competency Levels: [CompetencyLevelReference objects]
  - Competency Name: [EXACT baseline competency name]
    Competency Level Name: [baseline level name]
Involves: [array of Persona Group names - from Phase 1 team mappings]
Narrative: [from Phase 1 "How to Perform" section]
  - Use technique narrative type
  - Include citations to source material
```

**CRITICAL:** Activity names must be specific and different from Activity Space names

### Step 8: Map Patterns

For EACH pattern from Phase 1 (including lifecycle):

**Pattern Structure:**
```
Pattern Name: [from Phase 1]
Description: [single sentence from Phase 1]
Narrative Type Name: [choose from baseline narrative types based on pattern nature]
Pattern Views: [map Phase 1 views]
  View 1:
    Seq: [0 for prerequisites, 1+ for main phases]
    Name: [phase name from Phase 1]
    Description: [essence of this phase, max 12 words]
    Alpha States: [AlphaContribution objects - expected states for this phase]
      - Alpha Name: [alpha]
        State Name: [state]
    Alpha Instances: [if tracking specific instances through pattern]
      - Instance Name: [from AlphaInstanceName]
        Alpha Name: [parent alpha]
        State Name: [target state for this instance in this phase]
        Evidence By: [WorkProductInstance objects proving this state]
          - Instance Name: [work product variant]
            Work Product Name: [work product]
            Level Of Detail Name: [level]
    Activities: [array of activity names active in this phase]
    Narrative Contexts: [narrative slices for this phase]
      - Seq: [1, 2, 3...]
        Narrative Element Name: [element from chosen NarrativeType]
        Context: [1-2 sentences phase-specific context]
  View 2: ...
```

**Pattern Pruning:**
- Only include alphas that **change state** in this pattern
- Omit alphas with identical state across consecutive views
- Use seq: 0 for prerequisite/preparation phases

### Step 9: Map Aliases (If Applicable)

If Phase 1 used different terminology than baseline:

```
Practice Element Aliases:
  - Element Type: [Alpha | WorkProduct | Activity | Persona | etc.]
    Element Name: [CANONICAL baseline name]
    Alias Name: [source methodology's term]
```

**CRITICAL:** ALL structural references use CANONICAL names, NEVER alias names

**Examples:**
- Source uses "Cloud Platform" → Baseline "Platform"
  - Alias: {elementType: "Alpha", name: "Platform", aliasName: "Cloud Platform"}
  - All references use "Platform" (canonical)

### Step 10: Validate Mapping Decisions

**Before finalizing, check:**

1. **All new alphas have contributesTo** (no floating alphas)
2. **All baseline references use EXACT names** (case-sensitive)
3. **Competency names are canonical** (not descriptions)
4. **Tags use orthogonal structure** (domainTags, lifecycleTags, organizationalTags)
5. **Descriptions are single sentences** (max 20 words for elements, max 12 for states/LODs)
6. **Activity names differ from Activity Space names**
7. **Work product LOD names have NO "Level X:" prefix**
8. **All LODs have contributesTo array** (required field)
9. **Narrative contexts are 1-3 sentences** (not paragraphs)
10. **Citations have NO narratives property** (metadata only)

## Output Format

Create a markdown file: `practices/<practice-name>/02-mapping-guide.md`

### File Structure

```markdown
# Phase 2 Mapping Guide: <Methodology Name>

## Metadata
- **Mapping Date**: YYYY-MM-DD
- **Source Analysis**: practices/<practice-name>/01-analysis-report.md
- **Baseline Practice**: <path to baseline JSON>
- **Practice Type**: Single Practice | Method (Multiple Practices)

## Baseline Practice Index

### Focuses (3)
- Value
- Solution
- Endeavor

### Alphas (13 baseline + N practice-defined)
[List all baseline alphas with state counts]
- Platform (6 states)
- Requirements (6 states)
- ...

### Competencies (8)
- Analysis
- Engineering
- Leadership
- Management
- Platform Security And Compliance Enforcement
- Platform Strategic Alignment
- Site Reliability
- Stakeholder Representation

### Activity Spaces (20 baseline)
[List all baseline activity spaces]

### Narrative Types (N available)
[List baseline narrative types for use in patterns/narratives]

---

## Method Mapping (if applicable)

**Method Name:** [name]

**Method Description:** [single sentence]

**Method Keywords:** [5-10 keywords]

**Method Narrative:**
- Narrative Type Name: [chosen type]
- Narrative Contexts:
  - [Element Name]: [context]
  - [Element Name]: [context]

**Method Citations:**
[References used across all practices]
1. Name: ... | Authors: [...] | Date: ... | Source: ... | URL: ...
2. ...

**Practices Included:**
1. Practice Name 1
2. Practice Name 2
...

---

## Practice 1: <Practice Name>

### Practice Metadata

**Name:** [name]

**Description:** [single sentence]

**Baseline Practice Name:** [exact baseline name being extended]

**Tags:**
```json
{
  "domainTags": ["Architecture", "Security", ...],
  "lifecycleTags": ["Adoption", "Migration", ...],
  "organizationalTags": ["Platform Team", ...]
}
```

**Keywords:** [5-10 keywords]

**Practice Narrative:**
- Narrative Type Name: [STAR | Hero's Journey | Three-Act Structure | etc.]
- Narrative Contexts:
  - Situation: [context]
  - Task: [context]
  - Action: [context]
  - Result: [context]

### Citations

1. **Name:** Exact source title
   - **Description:** 1 sentence summary
   - **Authors:** [Author 1, Author 2]
   - **Date:** YYYY
   - **Source:** Publisher or journal
   - **URL:** https://...

2. [Next citation]
...

### Alpha Mappings

#### Redeclared Baseline Alphas

**Alpha: Platform** (Redeclaration - Enrichment)
- **Type:** Redeclaration
- **Baseline Alpha:** Platform
- **Description:** [EXACT baseline description]
- **Focus Name:** Solution
- **States:** [Baseline states with ADDED checklists]
  - **State: Architecture Selected**
    - **Description:** [baseline description]
    - **Seq:** 1
    - **Baseline Checklists:** [count]
    - **Added Checklists:**
      1. Cloud provider selected and approved
      2. Multi-region strategy defined
      3. ...
- **Narrative:**
  - Narrative Type Name: Essay
  - Narrative Contexts:
    - Introduction: Platform adoption requires...
    - Body: Key considerations include...
    - Conclusion: Success depends on...

#### New Practice-Defined Alphas

**Alpha: Platform Capability** (Specialization)
- **Type:** Specialization
- **Source Concern:** [from Phase 1 Section 2.X]
- **Description:** Individual platform service or capability maturity
- **Focus Name:** Solution
- **contributesTo:** Platform
- **States:**
  - **State: Identified**
    - **Description:** Capability need recognized
    - **Seq:** 1
    - **Checklists:**
      1. Capability requirement documented
      2. Stakeholders identified
      3. ...
  - **State: Designed**
    - **Description:** Capability interface and behavior specified
    - **Seq:** 2
    - **Checklists:**
      1. API contract defined
      2. ...
- **Narrative:** [from Phase 1]

#### Alpha Instances

**Alpha Instance: Core Platform**
- **Instance Name:** Core Platform
- **Alpha Name:** Platform
- **Description:** Primary production platform infrastructure
- **Narrative:** [optional context for this instance]

**Alpha Instance: Security Platform**
...

### Work Product Mappings

**Work Product: Architecture**
- **Type:** Redeclaration | New Practice Work Product
- **Source:** [from Phase 1 Section 3.X]
- **Description:** Technical architecture and design decisions
- **Levels of Detail:**
  - **Level: Outlined**
    - **Description:** High-level architecture sketch
    - **Seq:** 1
    - **Checklists:**
      1. Component diagram created
      2. Technology stack identified
      3. Integration points listed
    - **Contributes To:**
      - Alpha Name: Platform
        State Name: Architecture Selected
  - **Level: Defined**
    - **Description:** Comprehensive architecture documentation
    - **Seq:** 2
    - **Checklists:**
      1. Detailed component specifications
      2. Data flow diagrams
      3. Security architecture
      4. Scalability approach
    - **Contributes To:**
      - Alpha Name: Platform
        State Name: Provisioned
- **Narrative:** [if additional context needed]

**Work Product: [Next]**
...

#### Work Product Instances

**Work Product Instance: Platform Architecture**
- **Instance Name:** Platform Architecture
- **Work Product Name:** Architecture
- **Description:** Core platform technical architecture

### Persona and Persona Group Mappings

#### Competency Mapping

[Table showing Phase 1 competencies → Baseline competencies]

| Phase 1 Competency | Baseline Competency | Rationale |
|:-------------------|:-------------------|:----------|
| Cloud Architecture | Engineering | Technical build skills |
| Security Governance | Platform Security And Compliance Enforcement | Security/compliance enforcement |
| ... | ... | ... |

#### Personas

**Persona: Platform Engineer**
- **Source:** [from Phase 1 Section 6.X]
- **Description:** Engineers core platform infrastructure and services
- **Competencies:**
  - Competency Name: Engineering
    Competency Level Name: Advanced
  - Competency Name: Site Reliability
    Competency Level Name: Intermediate
- **Tags:**
  - domainTags: [Architecture, Infrastructure]
  - lifecycleTags: [Adoption, Operations]
  - organizationalTags: [Platform Team]

**Persona: [Next]**
...

#### Persona Groups

**Persona Group: Platform Team**
- **Source:** [from Phase 1 Section 7.X]
- **Description:** Team building and maintaining platform infrastructure
- **Persona Names:**
  - Platform Engineer
  - Platform Architect
  - Site Reliability Engineer
- **Tags:**
  - organizationalTags: [Platform Team]

### Activity Mappings

**Activity: Design Security Architecture**
- **Source:** [from Phase 1 Section 4.X]
- **Description:** Define security controls and compliance architecture
- **Activity Space Name:** Architect and Build the Foundation
- **Focus Name:** Solution
- **Contributes To:**
  - Alpha Name: Platform
    State Name: Architecture Selected
  - Alpha Name: Security Framework (if specialized alpha)
    State Name: Designed
- **Works On:**
  - Work Product Name: Architecture
    Level Of Detail Name: Defined
  - Work Product Name: Security Policy
    Level Of Detail Name: Drafted
- **Required Competencies:**
  - Platform Security And Compliance Enforcement
  - Engineering
- **Recommended Competency Levels:**
  - Competency Name: Platform Security And Compliance Enforcement
    Competency Level Name: Advanced
  - Competency Name: Engineering
    Competency Level Name: Intermediate
- **Involves:**
  - Security Team
  - Platform Team
- **Narrative:**
  - Narrative Type Name: Technique
  - Narrative Contexts:
    - Overview: Security architecture design establishes...
    - Technique: Begin by conducting threat modeling...
    - Common Pitfalls: Avoid treating security as an afterthought...
  - Citation Names:
    - Security Architecture Best Practices

**Activity: [Next]**
...

### Pattern Mappings

**Pattern: Platform Adoption Journey**
- **Source:** [from Phase 1 Section 8.X]
- **Description:** Overarching lifecycle for platform adoption
- **Narrative Type Name:** Hero's Journey
- **Pattern Views:**

  **View: Preparation** (seq: 0)
  - **Name:** Preparation
  - **Description:** Establish foundation and readiness
  - **Alpha States:**
    - Alpha Name: Platform
      State Name: Opportunity Identified
    - Alpha Name: Requirements
      State Name: Conceived
  - **Alpha Instances:**
    - Instance Name: Core Platform
      Alpha Name: Platform
      State Name: Opportunity Identified
      Evidence By:
        - Instance Name: Platform Vision Document
          Work Product Name: Requirements
          Level Of Detail Name: Outlined
  - **Activities:**
    - Assess Current State
    - Define Platform Vision
  - **Narrative Contexts:**
    - Seq: 1
      Narrative Element Name: Ordinary World
      Context: Organization faces infrastructure challenges limiting agility and scale.

  **View: Foundation Build** (seq: 1)
  - **Name:** Foundation Build
  - **Description:** Build core platform infrastructure
  - **Alpha States:**
    - Alpha Name: Platform
      State Name: Architecture Selected
    - Alpha Name: Platform
      State Name: Provisioned
  - **Activities:**
    - Design Security Architecture
    - Deploy Infrastructure
  - **Narrative Contexts:**
    - Seq: 1
      Narrative Element Name: Call to Adventure
      Context: Team commits to building cloud-native platform...

  [Additional views...]

**Pattern: [Next Pattern]**
...

### Alias Mappings

[If source uses different terminology]

**Practice Element Aliases:**

1. **Element Type:** Alpha
   - **Canonical Name:** Platform
   - **Alias Name:** Cloud Infrastructure
   - **Rationale:** Source uses "Cloud Infrastructure" for baseline "Platform" concept

2. **Element Type:** Activity
   - **Canonical Name:** Architect and Build the Foundation
   - **Alias Name:** Build & Deploy
   - **Rationale:** Source uses shorter "Build & Deploy" term

[Aliases only if needed - many practices won't need any]

---

## Practice 2: [If Method with Multiple Practices]

[Repeat all mapping sections for second practice]

---

## Validation Checklist

- [ ] All new alphas have contributesTo
- [ ] All baseline references use exact canonical names
- [ ] Competency names are exact baseline names (not descriptions)
- [ ] Tags use orthogonal structure {domainTags, lifecycleTags, organizationalTags}
- [ ] Descriptions are single sentences (max 20 words for elements, 12 for states/LODs)
- [ ] Activity names differ from Activity Space names
- [ ] Work product LOD names have NO "Level X:" prefix
- [ ] All LODs have contributesTo array
- [ ] Narrative contexts are 1-3 sentences (not paragraphs)
- [ ] Citations have NO narratives property
- [ ] Checklists are 5-7 items per state, 3-5 per LOD, one sentence each
- [ ] Practice narrative uses baseline narrative type
- [ ] All symbolic references are exact string matches
```

## Quality Standards

### Exact Name Matching
- **CRITICAL:** All baseline references MUST be exact, case-sensitive matches
- Use CANONICAL names in all structural references (NOT aliases)
- Competency names are exact baseline names (not descriptions)

### Redeclaration vs Specialization
- **Test:** Is this generally applicable or practice-specific?
- **Generally applicable** → Redeclaration (preserve baseline structure exactly)
- **Practice-specific** → Specialization (new alpha with contributesTo)
- **When in doubt** → Default to specialization

### Tagging Consistency
- Always use orthogonal structure: {domainTags, lifecycleTags, organizationalTags}
- Each dimension is independent
- Empty arrays are valid `[]`
- Tags enable multi-dimensional filtering

### Narrative Conciseness
- Contexts: 1-3 sentences per element (not paragraphs)
- Focus on key insights, not comprehensive essays
- Use citations for further reading

## Execution Notes

1. **Read semantics.md THOROUGHLY** - Understand all mapping rules before starting
2. **Load baseline practice completely** - Build mental index of all elements
3. **Work systematically** - Metadata → Citations → Alphas → Work Products → Personas → Activities → Patterns → Aliases
4. **Validate continuously** - Check each mapping against semantics rules
5. **Preserve source terminology** - Use aliases for different terms, not structural name changes
6. **Document rationale** - When making mapping decisions, note reasoning
7. **Cross-reference Phase 1** - Ensure all Phase 1 content is mapped (no omissions)

## Output Location

Write to: `practices/<practice-name>/02-mapping-guide.md`

## Success Criteria

- ✓ All Phase 1 concerns mapped to alphas (redeclaration or specialization)
- ✓ All Phase 1 work products mapped with LODs and contributesTo
- ✓ All Phase 1 activities mapped with complete references
- ✓ All Phase 1 competencies mapped to exact baseline names
- ✓ All Phase 1 personas and teams mapped
- ✓ All Phase 1 patterns mapped to baseline pattern structure
- ✓ All baseline references are exact canonical names
- ✓ No floating alphas (all new alphas have contributesTo)
- ✓ Tags use orthogonal structure throughout
- ✓ Validation checklist completely satisfied

This mapping guide will be used as input for Phase 3 (JSON Generation).
