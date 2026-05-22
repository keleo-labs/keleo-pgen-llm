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

### Redeclarations (Baseline Enrichment)

**When:** Source enhances baseline alpha with additional verification criteria

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
- Technology/infrastructure alphas (e.g., "Automation Platform", "CI/CD Pipeline") → contribute to "Platform"
- Content/artifacts alphas (e.g., "Automation Content", "Playbook", "Model") → contribute to "Platform Asset"
- Process/workflow alphas (e.g., "Job Template", "Workflow") → contribute to "Work"
- Governance alphas (e.g., "Policy Enforcement") → contribute to "Platform Governance"
- Risk/compliance alphas → contribute to "Platform Risk And Compliance"
- Value/economics alphas → contribute to "Platform Value And Economics"

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

**Type:** Redeclaration | New Alpha (Specialization) | [If New: Contributes To: [Parent Alpha Name]]

**Focus:** Value

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

**Narrative 1: Research and Standards**

**Narrative Type:** Essay Narrative

**Narrative Contexts:**

**Introduction:**

[What industry research, authoritative sources, or standards support this alpha concept. 2-4 sentences establishing the foundation.]

**Body:**

[How this alpha fits into broader practice frameworks, alignment with industry patterns. 3-5 sentences expanding on the evidence and connections.]

**Conclusion:**

[Why this alpha is essential for practice success. 2-3 sentences summarizing the imperative.]

**Citations Referenced:** [List citation names from Module 02 - e.g., "AWS Well-Architected Framework", "TOGAF 9.2"]

---

**Narrative 2: Application Guidance**

**Narrative Type:** The STAR Format

**Narrative Contexts:**

**Situation:**

[Context where teams encounter this alpha in practice. 2-3 sentences describing the typical scenario.]

**Task:**

[What teams need to accomplish related to this alpha. 2-3 sentences defining the objectives.]

**Action:**

[Common approaches, patterns, success factors. 3-5 sentences describing effective practices.]

**Result:**

[Expected outcomes when alpha is well-managed. 2-3 sentences showing the benefits.]

**Citations Referenced:** [List citation names if applicable, or omit if based on general practice]

---

**Narrative 3: Common Challenges** [OPTIONAL]

**Narrative Type:** Case Study

**Narrative Contexts:**

**Background:**

[Typical obstacles or anti-patterns related to this alpha. 2-3 sentences setting up the challenge context.]

**Challenge:**

[Specific problem that commonly arises. 2-4 sentences describing the issue in detail.]

**Resolution:**

[How successful teams address this challenge. 3-5 sentences explaining effective solutions.]

**Lessons Learned:**

[Key takeaways and preventive measures. 2-3 sentences distilling the wisdom.]

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

## Critical Writing Principle: Descriptive Discipline

**ALL descriptions across all elements must follow this pattern:**

1. **Descriptions = Essence Only**
   - Single SHORT sentence (8-15 words typical, max 20 words)
   - Captures WHAT the element is, not HOW, WHY, or comprehensive details
   - No lists, no "and also", no feature enumeration
   - Direct, declarative language

2. **Elaboration = Narratives + Citations**
   - Additional context, rationale, guidance → narratives
   - Industry research, standards, best practices → narratives with citations
   - Application scenarios, challenges, patterns → narratives with citations
   - Users access detailed information through narratives and external citations

3. **Quality Check Before Writing**
   - Can I remove words without losing the essence? → Remove them
   - Am I explaining HOW or WHY? → Move to narrative
   - Is this over 20 words? → Too long, cut to essence
   - Does this list multiple concepts? → Choose the core concept

**This applies to:**
- Alpha descriptions (max 20 words)
- State descriptions (max 12 words - even shorter!)
- Checklist criteria descriptions (NO limit - detail needed for verification)
- Alpha instance descriptions (max 20 words)

**Exception:** Checklist criteria descriptions should remain detailed enough for verification.

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
