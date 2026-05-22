# Phase 1 Module 05: Activities, Personas, and Teams

**Execution Context:** This module generates activities (the work performed), personas (individual roles), and persona groups (teams). Activities include rich technique narratives describing HOW to perform the work.

**Size Estimate:** ~15,000-20,000 words (largest module due to technique narratives).

**Note:** If content is excessive, can be split into 05a-activities.md and 05b-personas-teams.md.

---

## Role and Objective

You are a **Practice Research Analyst** defining the WHO and HOW of the practice: who does the work, and how they do it.

**Input:**
- Module 00 analysis-plan.md (activity derivation plan)
- Module 03 alphas.md (alpha states to progress)
- Module 04 workproducts.md (work products to create)
- Module 02 citations.md (for technique references)
- Source methodology materials
- Baseline framework

**Output:** Activities and roles document (~15,000-20,000 words) containing activities with technique narratives, personas, and persona groups.

---

## Required Resources

1. **Read Module 00** - `report-elements/00-analysis-plan.md`
   - Review activity derivation plan
   
2. **Read Module 03** - `report-elements/03-alphas.md`
   - Extract alpha names and states for contributesTo
   
3. **Read Module 04** - `report-elements/04-workproducts.md`
   - Extract work product names and LODs for worksOn
   
4. **Read Module 02** - `report-elements/02-citations.md`
   - Reference citations in technique narratives
   
5. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract exact ActivitySpace names, Competency names, CompetencyLevel names
   
6. **Source Materials** - User-provided methodology documentation

---

## Size Management

**Target:** 3,000-20,000 words per file
**Warning Threshold:** 23,000 words
**Maximum:** 25,000 words

**Note:** This module has a higher threshold (25,000 words) because technique narratives are inherently lengthy and detailed.

**If content exceeds 23,000 words:**

This module may need to be split by content type:

1. **STOP** before completing the full module if it appears content will exceed 23,000 words
2. **SPLIT** into two files:
   - `05a-activities.md` - All activity definitions with technique narratives
   - `05b-personas-teams.md` - All persona and persona group definitions
3. **CREATE** each file independently
4. **CROSS-REFERENCE:** 05b should reference activities from 05a when defining persona responsibilities

Alternative split strategy (if activities alone exceed 20,000 words):
   - `05a-activities-by-focus.md` - Split activities by Value/Solution/Endeavor focus
   - `05b-personas-teams.md` - All personas and teams

The skill will monitor output size and recommend splits if needed. After generating, the word count will be checked using `python -m utils.module_validator`.

**Decision Point:** If the source methodology defines 20+ activities with rich technique narratives, or 15+ personas, plan to split during generation.

---

## Component Overview

### Activities

Activities are **specific types of work** that:
- Progress alphas toward states
- Create or refine work products
- Require specific competencies
- Are performed by personas/teams
- Have technique narratives explaining HOW to do the work

### Personas

Personas are **individual roles** that:
- Have specific responsibilities
- Require specific competency levels
- May belong to one or more persona groups
- Are described narratively (not just competency lists)

### Persona Groups

Persona groups are **teams** that:
- Combine multiple personas
- Perform activities collaboratively
- Have collective capabilities
- Represent organizational structures

---

## Output Structure

---

## Activities

[Organized by focus area]

### Value Focus Activities

*Activities that advance business value, economics, and stakeholder engagement alphas.*

#### Activity: [Specific Activity Name]

**ActivitySpace:** [Exact Baseline ActivitySpace Name]

**Focus:** Value

**Description:**

Write a single SHORT sentence (8-15 words, max 20 words) that captures what this activity accomplishes.

**Guidelines:**
- **The outcome:** What gets accomplished, not how or why
- **Brevity:** Aim for 8-15 words, absolute maximum 20 words
- **No elaboration:** Save techniques, timing, success criteria for narratives below
- **Active voice:** Focus on the action and result

**Examples:**
- ❌ BAD (41 words): "Design Platform Architecture is a critical activity where platform architects work collaboratively with stakeholders to create comprehensive architectural blueprints that define the technical design, component relationships, and deployment patterns while ensuring alignment with organizational standards and industry best practices."
- ✅ GOOD (9 words): "Create architectural blueprints defining platform design and components."

- ❌ BAD (38 words): "Develop Automation Content involves platform engineers creating reusable automation artifacts including playbooks, roles, and modules that encode operational knowledge and enable consistent, repeatable infrastructure management across diverse environments and use cases."
- ✅ GOOD (10 words): "Create reusable automation artifacts encoding operational knowledge and procedures."

**For detailed guidance:** Use Technique narratives (How to Perform section below) to elaborate on methods, timing, collaboration patterns with citations.

**Outcomes and Alpha Progression:**

This activity advances the following areas of concern:

- Progresses **[Alpha Name]** toward the **[State Name]** state
- Progresses **[Alpha Name]** toward the **[State Name]** state

[List all alpha state progressions - minimum 1 required]

**Work Products Created/Refined:**

This activity creates or updates:

- **[Work Product Name]** to the **[Level of Detail Name]** level
- **[Work Product Name]** to the **[Level of Detail Name]** level

[List all work product contributions]

**Required Capabilities:**

This work requires proficiency in:

- **[Competency Name]** at [Level Name] level ([brief explanation of why/how this competency is needed])
- **[Competency Name]** at [Level Name] level

[List all required competencies - minimum 1]

Competency names must be exact baseline names: Analysis, Engineering, Leadership, Management, Test, Usage

Level names must be exact baseline names: Basic, Applies, Masters, Adapts, Innovating

**Team Involvement:**

This activity is typically performed by the **[PersonaGroup Name]** team.

[May reference multiple teams if collaborative]

---

**How to Perform This Activity:**

[CRITICAL: This section contains rich technique narratives extracted from source material]

**[Technique/Approach Title 1]**

**Narrative Type:** [The STAR Format | Lifecycle | Essay Narrative | User story | etc.]

[Write 3-6 paragraphs using the narrative framework to describe HOW to perform this technique]

**For STAR Format:**

**Situation:**
[Paragraph describing the context or problem this technique addresses]

**Task:**
[Paragraph describing what needs to be accomplished]

**Action:**
[Paragraph(s) describing the specific steps, approaches, or methods to use]

**Result:**
[Paragraph describing expected outcomes and success indicators]

**For Lifecycle Format:**

**Prerequisites:**
[What must be in place before starting]

**Step 1: [Action]**
[Detailed guidance for this step]

**Step 2: [Action]**
[Detailed guidance for this step]

**Step 3: [Action]**
[Detailed guidance for this step]

**Completion Criteria:**
[How to know this technique has been successfully applied]

**For Essay Format:**

**Introduction:**
[Set up the concept or principle]

**Key Principles:**
[Describe the core ideas]

**Application:**
[How to apply in practice]

**Conclusion:**
[Summary and success factors]

**Citations Referenced:** [List citation names from Module 02 supporting this technique - e.g., "Ansible Best Practices", "Infrastructure as Code Principles"]

---

**[Technique/Approach Title 2]**

**Narrative Type:** [Choose appropriate framework]

**Narrative Contexts:**

[Repeat narrative framework structure with all elements]

**Citations Referenced:** [List citation names from Module 02]

---

**Note:** Activities MUST have technique narratives. Multiple techniques per activity are encouraged if source material provides different approaches or methods.

---

[Repeat Activity structure for each activity in Value focus]

---

### Solution Focus Activities

*Activities that advance platform architecture, technical implementation, and capability delivery alphas.*

[Same structure as Value activities]

---

### Endeavor Focus Activities

*Activities that advance team organization, work execution, and organizational change alphas.*

[Same structure as Value/Solution activities]

---

## Personas

[Individual role descriptions]

### Persona: [Persona Name]

**Description:**

Write a single SHORT sentence (8-15 words, max 20 words) that captures this persona's primary role.

**Guidelines:**
- **The role:** What they do, not how they do it or why
- **Brevity:** Aim for 8-15 words, absolute maximum 20 words
- **No elaboration:** Save responsibilities, skills, team fit for competencies and optional narratives below
- **Direct language:** Describe the role itself

**Examples:**
- ❌ BAD (47 words): "The Platform Architect is a senior technical leader responsible for designing enterprise platform architecture, making critical technology decisions, ensuring alignment with organizational standards, mentoring engineering teams, and balancing technical excellence with business requirements while maintaining deep expertise in cloud technologies and distributed systems."
- ✅ GOOD (9 words): "Senior technical leader designing and governing platform architecture."

- ❌ BAD (42 words): "The Automation Engineer is a technical specialist who develops, tests, and maintains automation content including playbooks and roles, collaborates with operations teams to understand requirements, and ensures automation artifacts meet quality standards while advancing organizational automation maturity."
- ✅ GOOD (10 words): "Technical specialist developing and maintaining automation content and playbooks."

**For detailed context:** Use Competencies section (MANDATORY below) and optional narratives for career progression, organizational fit with citations.

**Competencies:**

[Explicit competency mapping for Phase 2 extraction]

- **[Competency Name]** at **[Level Name]** level
- **[Competency Name]** at **[Level Name]** level

---

[Repeat for each persona - aim for 3-8 personas]

---

## Persona Groups (Teams)

[Team structure descriptions]

### Persona Group: [Team Name]

**Description:** [Single sentence describing the team's primary purpose]

**Responsibilities:**

[2-3 paragraphs describing team responsibilities, purpose, and ways of working]

**Team Composition:**

[1 paragraph describing typical team size, structure, and organizational context]

**Team Members:**

**CRITICAL - REQUIRED FORMAT FOR PHASE 2 PARSING:**

This team consists of:
- **[Persona Name]** (must match exactly a Persona name defined in ## Personas section above)
- **[Persona Name]**
- **[Persona Name]**

[List ALL personas that are part of this team. Each name must EXACTLY match a persona name from the Personas section above. This explicit list is required for Phase 2 JSON translation.]

**Key Activities:**

[List of activity names this team performs - no narrative, just names separated by commas]

---

[Repeat for each persona group - aim for 2-5 teams]

---

## Critical Writing Principle: Descriptive Discipline

**ALL descriptions across all elements must follow this pattern:**

1. **Descriptions = Essence Only**
   - Single SHORT sentence (8-15 words typical, max 20 words)
   - Captures WHAT the element is or does, not HOW, WHY, or comprehensive details
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
- Activity descriptions (max 20 words)
- Persona descriptions (max 20 words)
- PersonaGroup/Team descriptions (max 20 words)

**Exception:** Technique narratives should be comprehensive and detailed - they are the primary mechanism for capturing HOW to perform work.

---

## Writing Guidelines

1. **Activity naming:** MUST be specific (verb + specific subject), MUST NOT duplicate ActivitySpace name
2. **Rich technique narratives:** Extract detailed HOW-TO guidance from source materials
3. **Multiple techniques per activity:** If source describes several approaches, create multiple narrative sections
4. **Exact baseline references:** ActivitySpace names, Competency names, CompetencyLevel names must match baseline exactly
5. **Verifiable contributions:** Alpha progressions and work product creations must be specific and checkable
6. **Natural competency weaving:** In persona descriptions, naturally mention required skills before listing them explicitly
7. **Realistic team composition:** Persona groups should reflect actual team structures, not arbitrary groupings

## Activity Naming Anti-Patterns

**WRONG:**
- ActivitySpace: "Architect and Build the Foundation" → Activity: "Architect and Build the Foundation" ❌

**CORRECT:**
- ActivitySpace: "Architect and Build the Foundation" → Activity: "Design Infrastructure Architecture" ✓
- ActivitySpace: "Define Platform Capabilities" → Activity: "Identify Consumer Requirements" ✓
- ActivitySpace: "Assess Business Value" → Activity: "Analyze Platform ROI Metrics" ✓

## Technique Narrative Guidelines

**Extract from source material:**
- Step-by-step procedures
- Best practices and principles
- Problem-solution approaches
- Worked examples and scenarios
- Tools, frameworks, and technologies mentioned
- Common pitfalls and how to avoid them
- Success criteria and validation approaches

**Structure using appropriate narrative types:**
- **STAR:** Problem-solution techniques
- **Lifecycle:** Sequential procedures
- **Essay:** Conceptual principles and best practices
- **User Story:** Persona-specific approaches
- **ABT:** Quick, persuasive techniques

**Be comprehensive:**
- Don't summarize as "follow best practices" - describe WHAT those practices are
- Don't say "use appropriate tools" - name WHICH tools
- Don't write "ensure quality" - explain HOW to ensure quality

## Competency Level Mapping

When extracting competency requirements from source materials:

**Basic:** Awareness, basic understanding, can follow guidance
**Applies:** Working knowledge, can perform independently with supervision
**Masters:** Expert proficiency, can perform without supervision, can mentor others
**Adapts:** Can adapt techniques to new contexts, handles complexity
**Innovating:** Creates new approaches, leads organizational capability

**Language cues in source materials:**
- "requires expert" → Masters or Adapts
- "strong/deep knowledge" → Masters
- "familiar with" → Basic or Applies
- "leads" → Adapts or Innovating
- "basic understanding" → Basic

## Execution Instructions

1. Read Modules 00, 02, 03, 04 to understand context, alphas, work products, citations
2. Load baseline to extract exact ActivitySpace, Competency, and CompetencyLevel names
3. For each activity in Module 00 plan:
   - Define activity with specific name (not duplicating ActivitySpace)
   - Map to baseline ActivitySpace exactly
   - Identify alpha state progressions (from Module 03)
   - Identify work product contributions (from Module 04)
   - Determine required competencies and levels
   - Identify performing persona group
   - **CRITICAL:** Extract rich technique narratives from source materials (this is the most important and time-consuming part)
4. For each persona:
   - Describe role responsibilities and context
   - Weave competency requirements into narrative
   - Explicitly list competencies for extraction
5. For each persona group:
   - Describe team composition (list constituent personas)
   - Explain team purpose and dynamics
   - Explicitly list persona members for extraction
6. Review for completeness:
   - [ ] Every activity has at least one technique narrative
   - [ ] Technique narratives are detailed and actionable (not vague)
   - [ ] All ActivitySpace, Competency, and CompetencyLevel references are exact matches
   - [ ] Every activity contributes to at least one alpha state
   - [ ] Every persona is referenced in at least one persona group
   - [ ] Every persona group is referenced in at least one activity

**Output:** Save complete activities and roles document to be consumed by Phase 2.
