# Pattern Completeness Requirements

Patterns MUST show complete alpha state progressions across all PatternViews.

Common anti-pattern: Patterns only include alpha states explicitly mentioned in source content, resulting in sparse/incomplete pattern matrices with missing cells.

## Four-Pass Pattern Construction

### Pass 1: Source-Driven Pattern Structure
- Extract pattern structure from source methodology
- Identify phases/stages (PatternViews) from source content
- Map explicitly mentioned alpha states to PatternViews
- Result: Initial pattern structure with explicit source mappings

### Pass 2: Alpha-Driven Completeness (REQUIRED)
- **For each alpha in the pattern:**
  - Review ALL states of the alpha
  - For EACH PatternView, determine appropriate state:
    - **First View (Prerequisites/Initial):** Starting state or "not yet started" state
    - **Middle Views:** Progressive states showing maturation
    - **Last View (Target/Final):** Advanced/optimized state
  - **Backfill missing alpha states** using these heuristics:
    - If alpha doesn't appear in a view, identify which state is appropriate for that lifecycle phase
    - States should progress logically across views (earlier states -> later states)
    - **CRITICAL RULE:** If an alpha's state doesn't change from previous view, STILL include it in the final PatternView
    - Only omit unchanged states in non-final views (compression), NEVER in the last view

### Pass 3: Related Alpha Discovery (OPTIONAL but RECOMMENDED)
- **Identify candidate alphas from:**
  - Other alphas in same practice (not yet in pattern)
  - Alphas from practice dependencies (excluding baseline unless explicitly relevant)
  - Alphas related via `relatesTo` relationships
- **For each candidate alpha, evaluate:**
  - Does this alpha's progression support the pattern narrative?
  - Would including this alpha states provide meaningful insights into the lifecycle?
  - Is there a natural state progression across the pattern views?
- **Add relevant alphas** with complete state progressions

### Pass 4: State Distribution Validation (REQUIRED)

**Constraint 1: One Alpha State Per PatternView**
- **Rule:** Each alpha MUST target at most 1 state per PatternView
- **Anti-pattern:** 2+ states for the same alpha in a single view (ambiguous target)
- **Validator enforcement:** `validate-practice-json.py` flags multi-state alpha targets as errors

**When 2+ states appear for an alpha in a PatternView, split into sub-views:**
- **Naming convention:** `Phase: Sub-step` (e.g., "Enable: Train", "Enable: Certify")
- Each sub-view gets its own `seq` number, activities, and narrative context
- Activities are assigned to the sub-view whose alpha state they most directly advance

**Example:**
- **Before:** View 2 "Implement" has Platform states: Architecture Designed, Built, Deployed, Monitored (4 states!)
- **After:** Split into:
  - View 2 "Implement: Design": Architecture Designed
  - View 3 "Implement: Build": Built
  - View 4 "Implement: Deploy": Deployed
  - View 5 "Implement: Operate": Monitored

**Constraint 2: Late-Appearing Alphas with Advanced States**
- **Anti-pattern:** Alpha first appears in PatternView N with state "Achieved" or other advanced state, but was NOT in PatternViews 1 to N-1
- **Problem:** Creates discontinuity -- "How did we get to 'Achieved' when alpha wasn't tracked before?"
- **Fix: Backfill earlier PatternViews with alpha's progression**

**Backfill Heuristics:**
1. Review Alpha X's state sequence: S1, S2, S3, ..., Y
2. Distribute earlier states across PatternViews 1 to N-1
3. Follow natural progression: earlier views get earlier states
4. Validate progression coherence with view narrative

**Example - Late-Appearing Alpha (WRONG):**
```
| View | Platform        | Platform Asset | Platform Capability | Platform Governance |
|------|----------------|----------------|---------------------|---------------------|
| 0    | Conceived      | [none]         | [none]              | [none]             |
| 1    | Architecture   | [none]         | [none]              | [none]             |
| 2    | Development    | [none]         | Identified          | [none]             |
| 3    | Operational    | Available      | Governed            | [SUDDEN: Compliant!]|
| 4    | Optimizing     | Optimized      | Optimized           | Automated          |
```

**Example - Late-Appearing Alpha (FIXED with Backfill):**
```
| View | Platform        | Platform Asset | Platform Capability | Platform Governance |
|------|----------------|----------------|---------------------|---------------------|
| 0    | Conceived      | [none]         | [none]              | Undefined          |
| 1    | Architecture   | [none]         | Identified          | Established        |
| 2    | Development    | [none]         | Governed            | Enforced           |
| 3    | Operational    | Available      | Optimized           | Compliant          |
| 4    | Optimizing     | Optimized      | [same]              | Automated          |
```

## Pattern Completeness Matrix

**BAD (Sparse Pattern - Missing Cells):**
```
| View | Team Topology Design | Cognitive Load | Team Interaction Mode | Organizational Sensing |
|------|---------------------|----------------|----------------------|----------------------|
| 0    | Static Structure    | Unmanaged Load | [MISSING]            | [MISSING]           |
| 1    | Four Types Defined  | Load Awareness | Mode Awareness       | [MISSING]           |
| 2    | Explicit Modes      | [MISSING]      | Explicit Assignment  | Sensors Established |
| 3    | Sensing & Evolving  | [MISSING]      | Strategic Evolution  | Trigger-Based       |
| 4    | Self-Steering Org   | Continuous Opt | [MISSING]            | Cybernetic Steering |
```

**GOOD (Complete Pattern - Full Coverage):**
```
| View | Team Topology Design | Cognitive Load | Team Interaction Mode | Organizational Sensing |
|------|---------------------|----------------|----------------------|----------------------|
| 0    | Static Structure    | Unmanaged Load | Undefined Interact.  | Static Organization |
| 1    | Four Types Defined  | Load Awareness | Mode Awareness       | Ad Hoc Adjustments  |
| 2    | Explicit Modes      | Domain Bounds  | Explicit Assignment  | Sensors Established |
| 3    | Sensing & Evolving  | Active Reduction| Strategic Evolution | Trigger-Based Evol. |
| 4    | Self-Steering Org   | Continuous Opt | Optimized Patterns   | Cybernetic Steering |
```

## Pattern Construction Workflow

1. **Extract from source:** Identify pattern name, description, phases
2. **Map explicit references:** Add alpha states mentioned in source
3. **Alpha completeness pass:** List all alphas in ANY PatternView, create state progression table, backfill missing cells
4. **Related alpha discovery:** Review practice/dependency alphas, add those with meaningful progressions
5. **State distribution validation (CRITICAL):**
   - Count states per alpha per PatternView (max 2, prefer 1)
   - If 3+ states in any view, subdivide pattern into finer views
   - Identify late-appearing alphas with advanced states
   - Backfill earlier views with progressive states for late alphas
6. **Validate completeness:**
   - Every alpha has entry in every PatternView (no missing cells)
   - States progress logically from early to late
   - Final PatternView includes ALL alphas (even if state unchanged from previous view)
   - No alpha has more than 2 states in a single view
   - No alpha suddenly appears late with advanced state (backfill complete)

## Pattern Completeness Checklist (Phase 2 Mapping)

- [ ] Pattern identifies all participating alphas upfront
- [ ] Each alpha has state progression documented across all views
- [ ] Missing cells backfilled using state sequence analysis
- [ ] Final PatternView includes ALL alphas (mandatory completeness rule)
- [ ] Related alphas from dependencies considered for inclusion
- [ ] Pattern narrative explains lifecycle progression coherently
- [ ] **State distribution quality (Pass 4):**
  - [ ] No alpha has more than 2 states in a single PatternView (prefer 1)
  - [ ] If 3+ states detected, pattern views subdivided into finer granularity
  - [ ] All alphas appearing in pattern are present from View 0 OR have clear justification
  - [ ] No alphas suddenly appear in late views with advanced states (backfill complete)

## Worked Example: Team Topology Evolution Journey

**Pass 1 (Source-Driven):** Extract from Team Topologies book
- Pattern Name: "Team Topology Evolution Journey"
- 5 Views: Prerequisites, Crawl, Walk, Run, Fly
- Explicitly mentioned states:
  - View 0: Team Topology Design (Static), Cognitive Load (Unmanaged)
  - View 1: Team Topology Design (Four Types), Cognitive Load (Awareness), Team Interaction Mode (Awareness)
  - View 2: Team Topology Design (Explicit), Team Interaction Mode (Explicit Assignment), Org Sensing (Sensors)
  - View 3: Team Topology Design (Sensing), Org Sensing (Trigger-Based), Team Interaction Mode (Strategic)
  - View 4: Team Topology Design (Self-Steering), Org Sensing (Cybernetic), Cognitive Load (Continuous)

Identified Alphas: Team Topology Design, Cognitive Load, Team Interaction Mode, Organizational Sensing

**Pass 2 (Backfill Missing States):**

*Team Interaction Mode - Missing in View 0:*
- Review states: Undefined Interactions, Mode Awareness, Explicit Mode Assignment, Strategic Mode Evolution, Optimized Interaction Patterns
- View 0 (Prerequisites): "Undefined Interactions" (before awareness exists)

*Organizational Sensing - Missing in View 0 and View 1:*
- View 0: "Static Organization" (traditional hierarchy)
- View 1: "Ad Hoc Adjustments" (starting to respond but not systematic)

*Cognitive Load - Missing in View 2 and View 3:*
- View 2: "Domain Boundaries Established" (aligns with "Explicit Interaction Modes")
- View 3: "Active Load Reduction" (proactive management)

*Team Interaction Mode - Missing in View 4:*
- FINAL VIEW RULE: Must include even if state unchanged
- View 4: "Optimized Interaction Patterns" (final state)

Result: Complete 4x5 matrix (20 alphaState entries)

**Pass 3 (Related Alpha Discovery):**
- Review practice alphas: Team, Work, Way of Working
- Evaluate: Would "Team" alpha state progression add value? No -- focus is on topology/interaction patterns, not team lifecycle. SKIP.
- Decision: Keep pattern focused on 4 topology-specific alphas

**Pass 4 (State Distribution Validation):**
- All alphas have exactly 1 state per view (IDEAL)
- All alphas present from View 0 (after Pass 2 backfill)
- 4 alphas x 5 views = 20 alphaState entries
- PASS - Pattern is complete and well-distributed
