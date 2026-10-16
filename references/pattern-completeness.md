# Pattern Completeness Requirements

A pattern MUST show the complete state progression of every alpha it carries. What it carries is the question this document answers first, because getting it wrong manufactures the defects the rest of it tries to prevent.

**Participation Rule:** A pattern carries an alpha when that alpha **changes state** across the pattern's views. An alpha that holds one state throughout is background to the pattern, not a participant, and `semantics/execution-and-patterns.md` §9.2 rule 1 says to remove it from every view rather than restate it. This is decided per pattern: a practice with three patterns will have alphas that participate in one and not the others, and that is correct, not a gap.

**Coverage is satisfied across the practice's patterns, not within each one.** Every practice alpha should appear in some pattern. Requiring every alpha in *every* pattern forces alphas into lifecycles they have no part in, at whatever state is nearest to hand — which is where "an alpha appearing only in the final view, at its opening state" comes from.

**State Compression Rule:** In the JSON output, only include an alpha state in a PatternView when the state CHANGES from the previous view. Unchanged states are implicitly carried forward. The FINAL PatternView is the exception — it restates every alpha **the pattern carries**, each at **the last state it reached in that pattern**, so the closing view reads as a complete end-state snapshot for consumers that do not implement carry-forward. It never introduces an alpha the pattern did not advance, and never restates one at a state earlier than it already reached. Compression keeps patterns from filling with redundant carry-forwards; the exception keeps the end state readable.

**Empty View Elimination:** After compression, any non-final PatternView with zero alpha states should be removed. Merge its activities into the next view and renumber `seq` values. An empty view means no alpha progresses during that phase — the view adds no value to the pattern.

Common anti-pattern: Patterns only include alpha states explicitly mentioned in source content, resulting in sparse/incomplete pattern matrices with missing cells.

## Cyclical Patterns

A lifecycle that recurs is declared, not flattened. `semantics/execution-and-patterns.md` §9.2a gives `PatternView.loopsBackTo` for this: an edge from the view where the cycle closes back to the view it returns to.

```json
{
  "name": "Adapt",
  "seq": 4,
  "alphaStates": [ ],
  "loopsBackTo": {
    "patternViewName": "Plan",
    "description": "Each increment re-plans from what the last one proved.",
    "condition": {
      "name": "More increments remain",
      "given": ["the release objective is not yet met"],
      "when": ["the increment review completes"],
      "then": ["the team re-enters planning for the next increment"]
    }
  }
}
```

**Ask the question whenever the source answers it.** Declare a loop when the source describes the lifecycle as a cycle, an iteration, a cadence, a sprint, or a closing phase that feeds the opening one — including when the pattern's own name says so. Several of the narrative types available for patterns (PDCA, Build-Measure-Learn) *are* cycles, and choosing one of those without a loop edge says the opposite of what the source said. Do not invent a loop the source does not describe: a pattern that runs once needs none.

**What the loop does and does not change:**

- **The work repeats; the maturity does not reset.** A re-entered view's `alphaStates` are the **minimum that must hold on that pass**, not a return to that state. Re-entering "Plan" at `Platform → Identified` does not mean the platform stopped being Available.
- **Progress never drops.** On re-entering an earlier view the achieved forecast is the highest weight reached on any pass, not the weight of the view being worked.
- **The final view is still the terminal objective.** A cycle is how the endeavour reaches it; `loopsBackTo.condition` states when the loop is taken rather than exited.
- **Pruning is suspended inside a loop.** The Sequential View Pruning rule would empty a re-entered view out, hiding what the iteration actually works on. Inside a loop, show what the iteration works on even where the state is unchanged.
- **It is a temporal edge, not a structural one.** A looping pattern still may not declare a cycle in `background.alphaStates`: a prerequisite cycle is unsatisfiable however many times the work goes round (§9.2a.3).

**Without the edge, the loop reads as a defect.** An alpha returning to an earlier state is flagged as a regression by `check-pattern-prerequisites.py`, and a prerequisite met on the previous lap reads as an inversion. Declaring the loop is what makes those `cyclical` instead — the ordering is then explained by the document rather than by a reader's charity.

## Four-Pass Pattern Construction

### Pass 1: Source-Driven Pattern Structure
- Extract pattern structure from source methodology
- Identify phases/stages (PatternViews) from source content
- Map explicitly mentioned alpha states to PatternViews
- Result: Initial pattern structure with explicit source mappings

### Pass 2: Alpha-Driven Completeness (REQUIRED)
- **Decide which alphas the pattern carries** (Participation Rule above). An alpha the pattern never advances belongs to another pattern, or to none — leave it out rather than parking it at a state to fill a cell.
- **For each alpha the pattern does carry:**
  - Review ALL states of the alpha
  - For EACH PatternView, determine appropriate state:
    - **First View (Prerequisites/Initial):** Starting state or "not yet started" state
    - **Middle Views:** Progressive states showing maturation
    - **Last View (Target/Final):** Advanced/optimized state
  - **Backfill missing alpha states** using these heuristics:
    - If the alpha doesn't appear in a view it does participate in, identify which state is appropriate for that lifecycle phase
    - States should progress logically across views (earlier states -> later states)
  - **Apply state compression to the JSON output:**
    - **Non-final views:** Only include alpha states that CHANGE from the previous view. Omit unchanged carry-forward states.
    - **Final view:** restate every alpha the pattern carries, at the last state it reached. Never at an earlier state, and never an alpha the pattern did not advance.

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

### Pass 5: Prerequisite Consistency (REQUIRED)

Alphas are mapped in Step 4 and patterns in Step 8, and nothing between the two checks them against each other. A state may declare `background.alphaStates` — cross-concern conditions that must hold before it is reached — and a pattern view may then assert that state several views before the pattern gets anywhere near them.

**For each alpha state placed in a view**, read that state's `background.alphaStates` and confirm the pattern reaches each prerequisite at that view or an earlier one. Three things count as reaching it:

- the prerequisite state is declared at that view or earlier
- a **later** state of the same alpha is, since passing it implies the earlier one
- the prerequisite sits inside a `loopsBackTo` span with the asserting view, so it was met on an earlier lap

The first view is exempt: it states the conditions holding before the pattern begins, so its prerequisites were met outside it.

**Where a prerequisite is not reached in time, resolve down this ladder and record the choice in the mapping guide.** The order matters: the cheap resolutions are at the top and the expensive one is at the bottom, and an alpha change is expensive because it reaches every document that depends on that alpha.

1. **Declare a loop.** If the source describes the lifecycle as recurring, the prerequisite is met on the previous lap. See Cyclical Patterns above.
2. **Move the state to a later view.** The commonest case: the pattern claimed the state too early.
3. **Bring the prerequisite alpha's progression earlier.** The dependency is real and the supporting alpha was placed too late.
4. **Weaken the prerequisite.** Check what the source actually requires. A prerequisite naming a *late* state of another alpha where the source supports an early one is an over-claim, and over-claiming is common — across the corpus, more than half of unmet prerequisites name a late or final state of their alpha.
5. **Change the alpha.** Only when its state array is genuinely in the wrong order, or its states turn out to be variants rather than stages. Size the blast radius with `check-downstream-impact.py` before doing it, and treat it as its own change rather than a detail of this one.

`check-pattern-prerequisites.py` reports what remains, and names which of these cases it thinks each finding is.

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
5b. **Prerequisite consistency (Pass 5):** walk each placed state's `background.alphaStates` against the view order and resolve any shortfall down the ladder
6. **Validate completeness:**
   - Every alpha the pattern carries appears in its first view AND its final view
   - Alphas the pattern never advances appear in none of its views
   - Non-final views only include alpha states that CHANGE (compression)
   - States progress logically from early to late
   - The final PatternView restates every carried alpha at the last state it reached
   - No alpha has more than 2 states in a single view
   - No alpha suddenly appears late with advanced state (backfill complete)

## Pattern Completeness Checklist (Phase 2 Mapping)

- [ ] Pattern identifies its participating alphas upfront — the ones whose state it changes
- [ ] Alphas the pattern never advances are absent from it, not parked at a state
- [ ] Every practice alpha participates in at least one of the practice's patterns
- [ ] Each carried alpha has state progression documented across the views it participates in
- [ ] Missing cells backfilled using state sequence analysis
- [ ] Related alphas from dependencies considered for inclusion
- [ ] Pattern narrative explains lifecycle progression coherently
- [ ] **State compression (JSON output):**
  - [ ] Non-final views include ONLY alpha states that change from the previous view
  - [ ] No redundant carry-forward states in non-final views
  - [ ] Final view restates every carried alpha at the last state it reached
- [ ] **State distribution quality (Pass 4):**
  - [ ] No alpha has more than 2 states in a single PatternView (prefer 1)
  - [ ] If 3+ states detected, pattern views subdivided into finer granularity
  - [ ] All alphas appearing in pattern are present from View 0 OR have clear justification
  - [ ] No alphas suddenly appear in late views with advanced states (backfill complete)
- [ ] **Prerequisite consistency (Pass 5):**
  - [ ] Every placed state's `background.alphaStates` are reached at that view or earlier
  - [ ] A recurring lifecycle declares `loopsBackTo` rather than relying on the reader
  - [ ] Any shortfall resolved down the ladder, with the choice recorded in the guide

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
- FINAL VIEW RULE: restated at the last state it reached, even if unchanged
- View 4: "Optimized Interaction Patterns" (final state)

Result: Complete 4x5 matrix (20 alphaState entries)

Note this practice has a **single** pattern and all four alphas transition across it, so every alpha participates and the matrix is genuinely complete. A practice with several patterns distributes its alphas between them; a 4x5 matrix in each would mean alphas carried by patterns that never move them.

**Pass 3 (Related Alpha Discovery):**
- Review practice alphas: Team, Work, Way of Working
- Evaluate: Would "Team" alpha state progression add value? No -- focus is on topology/interaction patterns, not team lifecycle. SKIP.
- Decision: Keep pattern focused on 4 topology-specific alphas

**Pass 4 (State Distribution Validation):**
- All alphas have exactly 1 state per view (IDEAL)
- All alphas present from View 0 (after Pass 2 backfill)
- 4 alphas x 5 views = 20 alphaState entries
- PASS - Pattern is complete and well-distributed
