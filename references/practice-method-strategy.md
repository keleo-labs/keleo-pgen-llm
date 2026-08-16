# Practice vs Method Delineation Strategy

Practice delineation is performed in Step 1.5 (Delineation Gate) by the main agent, then each Phase 2 subagent independently validates it via Step 0 of `phase-2-mapping.md`.

Baseline practice context is required to map Phase 1 concerns to baseline alphas, identify primary alphas, use baseline `relatesTo` relationships, and make informed practice boundary decisions.

## When Delineation Happens

| Phase | Action | Scope |
|---|---|---|
| Planning | Preliminary assessment only | Note obvious source separations |
| Phase 1 | Extract concerns without boundaries | No mapping to baseline alphas |
| **Step 1.5** | **DELINEATION DECISION POINT** | Map concerns to alphas, determine practice vs method |
| Phase 2 Step 0 | Validate delineation | Each subagent confirms independently |

## Practice (Single Value Stream)

**When:** Source content maps to 3-7 baseline alphas, ONE clear primary alpha identifiable, related alphas cluster around primary (via relatesTo), cohesive value proposition.

**Structure:** One analysis report, one mapping guide, one Practice JSON.

## Method (Multiple Practices)

**When:** Source content maps to 8+ baseline alphas across multiple focuses, multiple potential primary alphas, natural separation signals (use-cases, value-streams, domains), each practice cluster has 3-7 alphas.

**Structure:** One analysis report, one mapping guide per practice, one Method JSON with embedded practices.

## Primary Alpha Focus Strategy

**Core Principle:** Each practice should focus around ONE primary alpha, with secondary coverage of that alpha's directly related alphas (via `relatesTo` relationships, 1-level deep). This creates focused, coherent practices with broad coverage of loosely related concerns.

**Step 1: Check for natural separation signals**
- Different use-cases, value-streams, stakeholder journeys, or capability domains each indicate separate practices with own primary alpha.

**Step 2: Identify primary alphas from source content**
- What are the main conceptual focuses?
- Which alphas have the most content dedicated to them?
- What are the key outcomes the methodology is trying to achieve?

**For each identified primary alpha:**
1. Read baseline alpha's `relatesTo` array
2. Include directly related alphas (1-level deep): production, enablement, governance, information flow
3. Stop at 1 level -- related alphas' further relationships belong to their own practices
4. Expected coverage: 1 primary + 3-6 related = broad, loosely related coverage

### Example: Platform-Focused Practice

```
Primary Alpha: Platform
Related Alphas (from Platform.relatesTo):
+-- built by -> Team (enablement)
+-- hosts -> Platform Asset (production)
+-- exposes -> Platform Consumption Interface (production)
+-- governed by -> Platform Governance (governance)
+-- requires -> Requirements (OPTIONAL - if source has significant content)

Result: Practice covers 4-6 alphas with Platform as coherent center
```

### Example: Team-Focused Practice

```
Primary Alpha: Team
Related Alphas (from Team.relatesTo):
+-- performs -> Work (production)
+-- applies -> Way Of Working (enablement)
+-- manages -> Platform Risk And Compliance (governance)
+-- built from -> Stakeholders (OPTIONAL - if source covers recruitment)

Result: Practice covers 3-5 alphas with Team as coherent center
```

**Step 3: Validate practice coherence**
- ONE clear primary alpha focus
- 3-7 alphas total (1 primary + 2-6 related)
- Broad coverage of loosely related concerns
- Coherent value proposition centered on primary alpha
- Can be adopted independently
- NOT an "everything else" catch-all

**Step 4: Cross-practice coordination**
- **Method-level patterns** (simple coordination): Define patterns in method JSON referencing multiple practice alphas
- **Orchestration Practice** (complex coordination): Separate practice focused on coordination (see below)

## Orchestration Practice Exception

**When to Create:** Source methodology describes an overarching lifecycle or coordination framework tying together multiple domain practices.

**Structure:**
- **Primary Focus:** Coordination and integration patterns
- **Dependencies:** Lists all coordinated practices via `practiceDependencyNames`
- **Content:** Aliases (unifying terminology), patterns (lifecycle coordination), minimal alphas (only if coordination requires new tracking concepts)
- **NO redeclaration** of alphas from dependent practices

| Aspect | Regular Practice | Orchestration Practice |
|---|---|---|
| Focus | Primary alpha + related alphas | Dependencies + patterns + aliases |
| Content | Domain-specific elements | Coordination elements |
| Alphas | 3-7 from baseline | Minimal (coordination concepts only) |

**Anti-patterns:**
- Orchestration with 20+ alphas and no dependencies (should be regular practices)
- Orchestration duplicating content from dependent practices
- Creating orchestration when simple method-level patterns would suffice

## Cross-Baseline Alpha Bindings

When a method composes practices from different baseline families (e.g., Platform Adoption + Partner Ecosystem), use `bindings.alphaBindings` at the method level.

**When to use:** Method has practices from 2+ baselines with natural contribution relationships.
**When NOT to use:** Single-baseline methods (use `contributesTo` on alphas instead).

## Key Decision Principles

1. **Primary Alpha Focus** -- Every regular practice MUST have ONE identifiable primary alpha
2. **Broad Loosely-Related Coverage** -- Include related alphas (3-7 total) for comprehensive value delivery
3. **1-Level Relationship Depth** -- Use `relatesTo` to determine related alphas, stop at 1 level
4. **Avoid Catch-Alls** -- If you can't identify a primary alpha, the practice needs restructuring
5. **Orchestration Exception** -- Use orchestration practices for cross-practice coordination
6. **Independent Value** -- Each practice should deliver standalone value when adopted

## Worked Examples

### Example 1: Multi-Practice Method (SAFe)

**Source:** SAFe Agile Framework -- broad coverage without single primary alpha focus.
**Decision:** Method with 3 focused practices + 1 orchestration.

| Practice | Primary Alpha | Related Alphas | Focus |
|---|---|---|---|
| Portfolio Management | Opportunity | Platform Value And Economics, Stakeholders, Requirements | Value |
| Solution Delivery | Platform Asset | Requirements, Platform, Platform Consumption Interface | Solution |
| Agile Team Operations | Team | Work, Way Of Working, Organizational Change | Endeavor |
| SAFe Lifecycle Orchestration | (coordination) | Dependencies on above 3 practices | Cross-cutting |

### Example 2: "Everything Else" Anti-Pattern

**Problem:** Practice 3 has NO clear primary alpha -- it's a catch-all for leftover content.
**Fix:** Identify primary alphas for Practice 3 content:
- Significant team/org content? Create "Team & Organization" practice (Team primary)
- Consumption interface content? Merge into Platform practice (Platform.exposes relationship)
- Value/economics content? Merge into Portfolio practice (Opportunity.justifies relationship)
