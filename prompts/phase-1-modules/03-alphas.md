# Phase 1 Module 03: Alphas and Alpha Instances

**Execution Context:** This module generates all alpha definitions including redeclarations, new alphas, and alpha instance declarations. This may be one of the larger modules (potentially 15,000-20,000 words).

**Note:** If the source methodology has extensive alpha content across all three focuses, this module may need to be split into 03a-alphas-value.md, 03b-alphas-solution.md, 03c-alphas-endeavor.md to keep each file under 15,000 words.

---

## Role and Objective

You are a **Practice Research Analyst** defining alphas (areas of concern) that track progress through the practice.

**Input:**
- Module 00 analysis-plan.md (alpha extension strategy)
- Module 01 practice-details.md (practice context)
- Module 02 citations.md (for references)
- Source methodology materials
- Baseline framework

**Output:** Alphas document (potentially 15,000-20,000 words) containing all alpha definitions organized by focus.

---

## Required Resources

1. **Read Module 00** - `report-elements/00-analysis-plan.md`
   - Review alpha extension plan (redeclarations, new alphas, instances)
   
2. **Read Module 01** - `report-elements/01-practice-details.md`
   - Understand practice context
   
3. **Read Module 02** - `report-elements/02-citations.md`
   - Reference citations when supporting alpha definitions
   
4. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract exact baseline alpha names, state names, descriptions
   - For redeclarations: copy baseline structure EXACTLY
   
5. **Maturity Rubric** - `references/workproduct-assessment-rubric.csv`
   - Use to inform state progression (states should reflect maturity levels)
   
6. **Source Materials** - User-provided methodology documentation

---

## Size Management

**Target:** 3,000-15,000 words per file
**Warning Threshold:** 18,000 words
**Maximum:** 20,000 words

**If content exceeds 18,000 words:**

This module may need to be split by focus to maintain manageable file sizes:

1. **STOP** before completing the full module if it appears content will exceed 18,000 words
2. **SPLIT** by focus into separate files:
   - `03a-alphas-value.md` - Value focus alphas only
   - `03b-alphas-solution.md` - Solution focus alphas only
   - `03c-alphas-endeavor.md` - Endeavor focus alphas only
3. **CREATE** each file independently with its own focus section
4. **INCLUDE** common sections (Alpha Types and Rules, Writing Guidelines) in each file

The skill will monitor output size and recommend splits if needed. After generating, the word count will be checked using `python -m utils.module_validator`.

**Decision Point:** If the source methodology has extensive alpha content across all three focuses (10+ alphas total, detailed state checklists), plan to split during generation.

---

## Alpha Types and Rules

## ⚠️ CRITICAL FIRST STEP: Baseline Alpha Check

**BEFORE classifying ANY alpha as NEW or REDECLARATION, you MUST perform this check:**

### Step 1: Read Baseline Practice Completely

Use the Read tool to read `deps/platform-adoption-kernel.json` (or user-specified baseline file) completely. Extract ALL baseline alpha names.

**Baseline alphas typically include:**
- Platform
- Platform Consumption Interface
- Platform Asset
- Platform Capability
- Requirements
- Stakeholders
- Work
- Team
- Way Of Working
- Platform Governance
- Platform Risk And Compliance
- Platform Value And Economics
- Organizational Change

(The exact list depends on the baseline file - ALWAYS read it completely.)

### Step 2: For EACH Alpha Identified from Source

For every alpha concept you identified in Module 00 or from source materials:

1. **Check exact name match (case-sensitive):**
   - Does `alpha.name` EXACTLY match a baseline alpha name?
   - Even one character difference (case, space, punctuation) = NO match

2. **Read baseline alpha description:**
   - Understand the FULL scope of the baseline alpha
   - Baseline descriptions define semantic boundaries

3. **Read baseline alpha states:**
   - Understand the baseline progression model
   - State names reveal what the alpha tracks

### Step 3: Apply Classification Rules

**IF exact name match in baseline:**
- → MUST be **REDECLARATION** (enrichment)
- Use baseline name, description, state names EXACTLY
- Only add practice-specific checklists to existing states
- **NO contributesTo property** (baseline alphas don't contribute to anything)
- **NO state modifications** (state names, descriptions, seq must match baseline exactly)

**IF no exact name match in baseline:**
- → NEW alpha (specialization)
- Create new name describing the specialized concept
- Define custom states for specialized progression
- **MUST have contributesTo** pointing to a baseline alpha
- MUST provide justification for contributesTo choice (see below)

### Step 4: Common Mistakes to Avoid

**DANGER:** Do NOT assume governance/risk/compliance/organizational concepts are "new" without checking baseline first.

**Baseline often includes these concepts:**
- Platform Governance ← governance concepts usually REDECLARE this
- Platform Risk And Compliance ← risk/compliance usually REDECLARE this
- Organizational Change ← change management usually REDECLARES this
- Team ← team structures usually REDECLARE this
- Way Of Working ← process/practice usually REDECLARES this
- Stakeholders ← stakeholder management usually REDECLARES this

**Example Error:**
- Source mentions "platform governance policies and procedures"
- ❌ WRONG: Create new alpha "Platform Governance" with contributesTo "Platform"
- ✅ RIGHT: REDECLARE baseline alpha "Platform Governance" with policy/procedure checklists

**Why This Matters:**

Treating a baseline alpha as "new" causes:
1. Duplicate concept definitions (one in baseline, one in practice)
2. Invalid contributesTo relationship (baseline alphas don't contribute to anything)
3. Schema validation errors (baseline alpha appears twice with different structures)
4. Semantic confusion (which "Platform Governance" should consumers use?)

---

## Decision: Redeclaration vs. Specialization

**ONLY applies AFTER you've confirmed the alpha name does NOT match baseline.**

When source material describes enhancements to a baseline alpha concept, determine the correct approach:

### Test: Is this generally applicable or practice-specific?

**Ask:** "Do these additions apply broadly across the domain, or are they specific to this practice's approach?"

**Generally Applicable → Redeclaration**

The additions represent universal verification criteria, industry-standard checklists, or widely-recognized best practices that any practice in this domain would benefit from.

**Examples:**
- Adding NIST security framework checklists to "Platform Governance" states
- Adding financial ROI calculation criteria to "Platform Value And Economics" states  
- Adding team psychological safety checklists to "Team" states

**In these cases:** Redeclare the baseline alpha, preserving exact baseline structure, and add the generally-applicable checklists/narratives.

**Practice-Specific → Specialization**

The additions represent this practice's particular approach, methodology-specific concepts, or specialized techniques that wouldn't necessarily apply to other practices in the domain.

**Examples:**
- Adding "Stream-Aligned Team" vs "Platform Team" distinction to Team → Create "Team Topology" alpha that contributesTo "Team"
- Adding practice-specific automation patterns to "Way of Working" → Create "Automation-First Way of Working" alpha that contributesTo "Way of Working"
- Adding methodology-specific governance workflows → Create specialized governance alpha that contributesTo baseline governance alpha

**In these cases:** Create a new specialized alpha with contributesTo pointing to the baseline alpha. This keeps the baseline alpha reusable across practices.

### Decision Criteria

| Factor | Redeclaration | Specialization |
|:-------|:-------------|:---------------|
| Scope | Universal, industry-standard | Practice-specific, methodology-specific |
| Applicability | Any practice would benefit | Only this practice/methodology |
| Terminology | Uses general domain terms | Uses practice-specific terms |
| Checklist criteria | Widely-recognized best practices | Methodology-specific techniques |
| Reusability | Other practices could adopt verbatim | Meaningful only in this practice context |

### When in Doubt

If uncertain whether additions are generally applicable:
1. Check if other methodologies use similar concepts → Generally applicable
2. Check if terminology is practice-specific → Practice-specific
3. **Default to specialization** to preserve baseline reusability

---

### Redeclarations (Baseline Enrichment)

**When:** Source enhances baseline alpha with additional verification criteria that are generally applicable across the domain

**Before creating a redeclaration:** Apply the Decision Tree above to verify additions are generally applicable, not practice-specific.

**Rules:**
- Name: EXACTLY matches baseline Alpha.name
- Description: EXACTLY matches baseline Alpha.description (copy verbatim)
- States: EXACTLY match baseline State names, descriptions, and seq numbers
- ONLY ADD: checklists and narratives
- DO NOT CHANGE: anything about baseline structure

**Multi-Perspective Merging:**
If Module 00 identified that multiple perspectives (Business, Technology, People, Process) reference the same baseline alpha, create ONE merged redeclaration that combines checklists from all perspectives.

### New Alphas (Specializations)

**When:** Source describes a focused subset that needs its own progression

**CRITICAL RULE - NO FLOATING ALPHAS:**
All new alphas introduced in a Practice MUST logically refine a parent concept by explicitly declaring a `contributesTo` relationship pointing to a baseline Alpha name. Floating alphas (new alphas without `contributesTo`) are **STRICTLY PROHIBITED** by the Practice Language semantics.

**Rules:**
- Name: New, specific name (not in baseline)
- Description: Custom description from source
- States: Minimum 3, reflect specialized progression
- **MANDATORY:** `contributesTo` pointing to a parent baseline Alpha name
- MUST represent reusable specialization, not a specific instance

**Examples of Valid contributesTo Mappings:**
- Infrastructure/substrate alphas (e.g., "Container Platform", "Multi-Cluster Environment", "Storage System", "Network Fabric") → contribute to "Platform"
- Consumption interface alphas (e.g., "Developer Portal", "Service Catalog", "Internal Developer Platform", "Golden Path System", "Self-Service API", "CLI Tool") → contribute to "Platform Consumption Interface"
- Workload/application alphas (e.g., "Application", "Microservice", "Data Pipeline", "ML Model") → contribute to "Platform Asset"
- Process/workflow alphas (e.g., "Job Template", "Workflow", "Sprint") → contribute to "Work"
- Governance alphas (e.g., "Policy Enforcement", "Compliance Framework") → contribute to "Platform Governance"
- Risk/compliance alphas (e.g., "Security Controls", "Audit Trail") → contribute to "Platform Risk And Compliance"
- Value/economics alphas (e.g., "Cost Allocation", "Chargeback Model") → contribute to "Platform Value And Economics"

**Critical Distinctions:**
- **Platform** = Infrastructure substrate (clusters, VMs, storage, networking)
- **Platform Consumption Interface** = How users access platform (portals, catalogs, CLI, API, templates, docs)
- **Platform Asset** = Workloads running on platform (applications, services, databases)

### Alpha Instances

**When:** Source describes specific occurrences or examples

**Rules:**
- Declare as AlphaInstanceName (not full Alpha definition)
- Reference parent Alpha via alphaName
- Will be tracked in patterns, not as separate alpha definitions
- Multiple instances can exist simultaneously

---

## Output Structure

Organize by focus, following Module 00 decisions:

---

## Value Focus Alphas

*This section covers Alphas related to business value, financial management, and stakeholder engagement.*

### Alpha: [Alpha Name]

**Type:** Redeclaration | New Alpha (Specialization)

**Focus:** Value | Solution | Endeavor

**Contributes To:** [Parent Alpha Name] (REQUIRED for new alphas, omit for redeclarations)

**Justification for contributesTo:** (REQUIRED for new alphas)
- **Description alignment:** [Explain how this alpha fits within parent alpha's scope as described in baseline]
- **State alignment:** [List which states align with parent alpha states - aim for ≥50% alignment]
- **Alternative considered:** [Other baseline alpha considered as parent and why rejected]
- **Decision rationale:** [Why this parent alpha is semantically most appropriate]

**Example Justification:**
```
Contributes To: Platform Consumption Interface

Justification:
- Description alignment: IDP (developer portal, catalog, templates) provides the consumption interface through which developers access platform capabilities. Fits Platform Consumption Interface scope: "means by which consumers interact with and consume the platform"
- State alignment: 4/5 states align - "Scoped"="Scoped" (exact), "Catalog Available"~"Available", "Self-Service Functional"~"Self Service", "Optimized"="Optimized" (exact) = 80% alignment
- Alternative considered: Platform (infrastructure) - rejected because Platform focuses on substrate (clusters, VMs, storage) not consumption layer. 0% state alignment with Platform states.
- Decision rationale: IDP abstracts platform complexity and provides developer-friendly consumption experience, which is the definition of Platform Consumption Interface
```

**Description:**

Write a single SHORT sentence (8-15 words, max 20 words) that captures ONLY the essence of what this alpha is.

**Guidelines:**
- **What it is:** Not why it matters, not how to use it, not what it includes
- **Brevity:** Aim for 8-15 words, absolute maximum 20 words
- **No elaboration:** Save research backing, application guidance, and context for narratives below
- **Direct language:** Describe the concept itself, not "this alpha represents..."

**Examples:**
- ❌ BAD (47 words): "The Platform alpha represents the foundational technology infrastructure that enables application delivery by providing consistent deployment patterns, managing security and compliance requirements, and serving as the central integration point for all enterprise workloads while maintaining operational excellence."
- ✅ GOOD (9 words): "Foundational technology infrastructure enabling consistent application deployment and operations."
  - **Then use Context narratives** to elaborate on security, integration, operational excellence with citations

- ❌ BAD (38 words): "The Automation Content alpha tracks the development and maturity of automation artifacts including playbooks, roles, and modules that encode operational knowledge and enable consistent, repeatable infrastructure management across the enterprise."
- ✅ GOOD (10 words): "Reusable automation artifacts encoding operational knowledge for infrastructure management."

**For Redeclarations:** Use the baseline description EXACTLY as written, then add ONE additional SHORT sentence (max 15 words) explaining how this practice enriches it.

**For detailed context:** Use Context and Rationale Narratives section below with citations.

#### Progressive States

[Write states with natural prose descriptions and criteria]

**State 1: [State Name]** (seq: 1)

**Description:**

Single SHORT sentence (8-12 words) describing what characterizes this state.

**Guidelines:**
- **What characterizes it:** Not how to achieve it, not what happens next
- **Brevity:** Aim for 8-12 words, absolute maximum 12 words
- **Direct language:** Describe the state itself

**Examples:**
- ❌ BAD (21 words): "The platform has been identified as needed and initial requirements have been gathered from stakeholders to inform the design process."
- ✅ GOOD (8 words): "Platform need identified with initial requirements gathered."

- ❌ BAD (18 words): "Platform components are deployed, configured, and operational in production with monitoring and support in place."
- ✅ GOOD (8 words): "Platform operational in production with monitoring active."

**For Redeclarations:** Use the baseline state description EXACTLY as written.

**Criteria for achieving this state:**

1. **[Criterion Name]:** [Detailed criterion description - what must be verified, how to verify it, what evidence proves it]

2. **[Criterion Name]:** [Detailed criterion description]

3. **[Criterion Name]:** [Detailed criterion description]

[Continue for all criteria - aim for 3-7 criteria per state]

---

**State 2: [State Name]** (seq: 2)

[Description]

**Criteria for achieving this state:**

[Repeat structure]

---

[Continue for all states - minimum 3 states required]

#### Context and Rationale Narratives

**For new alphas:** MANDATORY - must include at least one narrative providing context.
**For redeclarations:** OPTIONAL but recommended - provides practice-specific elaboration.

**Guidance on Narrative Selection:**

Choose narrative frameworks that best convey the type of context:
- **Essay Narrative** - For conceptual explanations, research backing, theoretical foundations
- **The STAR Format** - For practical application scenarios and guidance
- **Case Study** - For challenges, anti-patterns, real-world examples
- **The StoryBrand** - For value propositions and stakeholder perspectives
- **How-To Guide** - For procedural or methodological context

Refer to baseline framework for complete list of narrative types and their elements.

---

## Narrative Context Writing Guidelines

**CRITICAL:** Narrative contexts are focused points, not comprehensive essays.

**Each context element should be:**
- **1-2 sentences maximum** - Make your point concisely
- **Specific claim or observation** - Not general background
- **Supported by citations** - Reference authoritative sources
- **Bullet-point mentality** - Key insights, not full exposition

**Anti-patterns to avoid:**
- ❌ Multi-paragraph context elements (3+ sentences per element)
- ❌ Comprehensive background exposition
- ❌ Repeating source material verbatim
- ❌ Generic statements without specific claims

**Good pattern:**
- ✅ Specific research finding or principle (1-2 sentences)
- ✅ Practical observation or pattern (1-2 sentences)
- ✅ Clear connection to practice domain (1-2 sentences)
- ✅ Citation for deeper reading

**Remember:** Contexts are signposts pointing to insights. Citations provide the full journey.

---

**Narrative 1: Research and Standards**

**Narrative Type:** Essay Narrative

**Narrative Contexts:**

**Introduction:**

Industry research emphasizes cognitive load management as a key factor in platform team effectiveness, with studies showing teams managing more than 2-3 major domains experience significant productivity degradation.

**Body:**

DORA research correlates team cognitive load reduction with deployment frequency and change failure rate improvements. Teams with well-scoped domains deploy 2-3x more frequently with 50% fewer incidents.

**Conclusion:**

Platform teams operating as cognitive load reducers for stream-aligned teams deliver measurable organizational value through improved delivery metrics and reduced coordination overhead.

**Citations Referenced:** [List citation names from Module 02 - e.g., "Accelerate: Building and scaling high performing technology organizations", "Team topologies: Organizing business and technology teams for fast flow"]

---

**Narrative 2: Application Guidance**

**Narrative Type:** The STAR Format

**Narrative Contexts:**

**Situation:**

Platform teams struggle to balance rapid feature delivery against infrastructure stability and security requirements, often defaulting to overly restrictive processes that slow consumer teams.

**Task:**

Establish clear platform capability boundaries and service-level commitments that enable consumer team autonomy while maintaining operational reliability and security compliance.

**Action:**

Define platform capabilities as self-service APIs with documented SLOs. Implement automated policy enforcement at API boundaries rather than manual approval processes.

**Result:**

Consumer teams gain autonomous platform access with clear reliability expectations, while platform team maintains security and operational control through automated enforcement and comprehensive observability.

**Citations Referenced:** [List citation names if applicable, or omit if based on general practice]

---

**Narrative 3: Common Challenges** [OPTIONAL]

**Narrative Type:** Case Study

**Narrative Contexts:**

**Background:**

Organizations often create platforms without clear ownership models, leading to shared responsibility dilution where "everyone owns it" means no one takes accountability for platform health.

**Challenge:**

Without dedicated platform teams, infrastructure becomes a coordination burden distributed across application teams. Each team makes local optimization decisions that create global complexity.

**Resolution:**

Establish a dedicated platform team with product ownership mindset, treating consuming teams as customers. This team owns platform architecture decisions, performance SLOs, and developer experience outcomes.

**Lessons Learned:**

Platform success requires dedicated ownership. Shared infrastructure cannot be a side responsibility of application teams without degrading both platform quality and application delivery velocity.

**Citations Referenced:** [List citation names if applicable]

---

### Alpha Instances: [Alpha Name]

[If Module 00 identified specific instances of this alpha]

This practice tracks several specific instances of **[Alpha Name]**:

**Instance: [Instance Name]**

[2-3 sentence description of what this specific instance represents, when it applies, how it differs from other instances]

**Instance: [Next Instance Name]**

[Repeat for each instance]

---

[Repeat the Alpha structure for each Value focus alpha]

---

## Solution Focus Alphas

*This section covers Alphas related to platform architecture, technical solution, and hosted workloads.*

[Same structure as Value Focus - repeat for each Solution alpha]

---

## Endeavor Focus Alphas

*This section covers Alphas related to team structure, work coordination, and execution practices.*

[Same structure as Value/Solution - repeat for each Endeavor alpha]

---

## Special Considerations for Redeclarations

When creating a redeclared alpha:

1. **Load baseline alpha** from `deps/platform-adoption-kernel.json`
2. **Copy verbatim:**
   - name
   - description
   - Each state's name, description, seq
3. **Add practice-specific content:**
   - Additional checklist items per state
   - Practice-specific narratives
   - Citations supporting the enhanced criteria

**Example Structure for Redeclaration:**

### Alpha: Platform

**Type:** Redeclaration (enriches baseline)

**Focus:** Solution

The Platform alpha represents the foundation of capabilities...

[Use baseline description EXACTLY, then add practice-specific context in next paragraph]

This practice enriches the baseline Platform alpha with additional verification criteria focused on [specific domain - e.g., security compliance, cost optimization, developer experience]...

#### Progressive States

**State 1: Architecture Selected** (seq: 1)

[Use baseline state description EXACTLY]

**Criteria for achieving this state:**

**[Baseline criteria - if any are listed in baseline, include them verbatim]**

**[Practice-specific criterion 1]:** [New verification criterion added by this practice]

**[Practice-specific criterion 2]:** [New verification criterion added by this practice]

[Continue with practice-specific additions]

---

## Writing Standards

This module follows the centralized writing standards defined in the skill documentation:

**Key Standards for This Module:**
- **Descriptions:** Single-sentence essence only (max 20 words for alphas, max 12 words for states)
- **Narrative contexts:** 1-2 sentences per element (concise, focused points)
- **Checklist criteria:** One sentence per criterion (detailed enough for verification)
- **Citations:** Reference via citationNames; no narratives on Citation objects

**For complete guidelines**, see the skill's "Centralized Writing Standards" section, including:
- Descriptive Discipline (essence vs. elaboration)
- Narrative Context Guidelines (signposts, not essays)
- Checklist Standards (5-7 criteria per state)
- Alpha decision tree (redeclaration vs. specialization)

---

## Writing Guidelines

1. **For redeclarations: Copy baseline exactly** - Names, descriptions, state structures must match
2. **For new alphas: Be specific** - Name should reflect the specialization clearly
3. **State descriptions: Be clear** - Explain what the state means, not just criteria
4. **Checklist criteria: Be verifiable** - Each criterion should be checkable/provable
5. **Use maturity progression** - States should reflect increasing maturity (Basic → Comprehensive)
6. **Reference citations** - When research supports a concept, cite it
7. **Natural prose** - Write as technical documentation, not pseudo-JSON
8. **Comprehensive criteria** - Capture all verification requirements, don't say "etc."

## Checklist Criteria Guidelines

Each checklist criterion should:

1. **Have a clear name** (3-8 words summarizing the criterion)
2. **Have a detailed description** explaining:
   - What must be true/exist/happen
   - How to verify it
   - What evidence proves it
3. **Be independently verifiable** (not dependent on other criteria)
4. **Be specific** (not vague like "appropriate measures taken")

**Good Criterion Example:**

**Platform ROI Model Established:** A quantitative model calculates platform return on investment including developer productivity gains, infrastructure cost savings, and time-to-market improvements. The model is documented, validated by finance stakeholders, and updated quarterly with actual metrics.

**Bad Criterion Example:**

**ROI is good:** Platform provides value ❌ (too vague, not verifiable)

## Alpha Instance Naming

When declaring alpha instances:

- **Use specific, descriptive names**
- **Format:** [Qualifier] + [Base Alpha]
- **Examples:**
  - Security Requirements (instance of Requirements)
  - Platform Team (instance of Team)
  - API Platform (instance of Platform)
  - Cost Optimization Stakeholders (instance of Stakeholders)

## State Progression Tips

States should reflect a maturity journey:

- **Early states:** Concept recognized, initial planning, foundational elements
- **Middle states:** Structure defined, capabilities developed, integration achieved
- **Later states:** Operational maturity, continuous improvement, delivering value

**Example Platform Progression:**
1. Architecture Selected - Decision made, approach defined
2. Baselined - Foundation established, standards set
3. Provisioned - Infrastructure deployed, accessible
4. Ready - Configured for use, integrated with ecosystem
5. Hosting Assets - Actively supporting workloads
6. Evolving - Adapting based on feedback, improving continuously
7. Retiring - Systematic decommissioning underway

## Execution Instructions

1. Read Modules 00, 01, 02 to understand context and decisions
2. Load baseline framework to extract exact alpha names/states
3. For each alpha in Module 00 plan:
   - If redeclaration: Copy baseline structure exactly, add practice-specific checklists
   - If new alpha: Define custom states (minimum 3), establish contributesTo
   - If instances: Declare AlphaInstanceName objects with descriptions
4. Organize by focus (Value, Solution, Endeavor)
5. Write comprehensive alpha descriptions and context
6. Define detailed, verifiable checklist criteria
7. Add narratives where they provide valuable context
8. Reference citations from Module 02 where appropriate
9. Review for completeness and consistency

**Output Size Check:**
- If total output will exceed 20,000 words, consider splitting by focus
- Each focus section becomes a separate file: 03a-alphas-value.md, 03b-alphas-solution.md, 03c-alphas-endeavor.md

**Output:** Save complete alphas document (or split files if needed) to be consumed by Phase 2.
