# Translate-Methodology Skill - Workflow Optimization

**Date:** 2026-05-21  
**Purpose:** Maximize concurrent execution and efficiency in the two-phase translation pipeline

---

## Current State Analysis

### Phase 1: Research Generation (Sequential)
**Current workflow:**
```
00-analysis-plan → 01-practice-details → 02-citations → 03-alphas → 
04-workproducts → 05-activities-roles → 06-patterns → 07-aliases
```

**Total time (sequential):** ~60-90 minutes for single practice

**Dependencies:**
- Module 00 → Must run first (creates analysis foundation)
- Module 01 → Depends on 00 (practice structure)
- Module 02-07 → All depend on 01 (need practice context)
- Modules 02-07 → Minimal cross-dependencies between them

### Phase 2: JSON Generation (Documented as Parallel, Not Implemented)
**Current workflow:**
```
Segment 01 → Segment 02 → Segment 03 → ... → Segment 09 → Assemble
```

**Documented potential:**
> "Segment generation can be parallelized: Spawn 9 agents simultaneously, one per segment."

**But:** Workflow instructions don't show HOW to execute in parallel

---

## Optimization Strategy

### Phase 1: Modular Concurrent Generation

**Dependency Graph:**
```
                    ┌─────────────────────┐
                    │ 00-analysis-plan    │ (Must be first)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ 01-practice-details │ (Must be second)
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
    ┌───────────▼──────┐  ┌───▼───────┐  ┌──▼──────────────────┐
    │ 02-citations     │  │ 03-alphas │  │ 04-workproducts     │
    │ (independent)    │  │ (refs 00) │  │ (refs 03 for alphas)│
    └──────────────────┘  └─────┬─────┘  └──────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ 05-activities-roles    │ (refs 03, 04)
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ 06-patterns            │ (refs 03, 04, 05)
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ 07-aliases             │ (optional)
                    └────────────────────────┘
```

**Optimized Execution Waves:**

**Wave 1: Foundation (Sequential)**
1. Module 00: analysis-plan (~5-10 min)
2. Module 01: practice-details (~3-5 min)

**Wave 2: Core Content (Parallel - 3 agents)**
- Agent A: Module 02: citations (~2-3 min)
- Agent B: Module 03: alphas (~15-20 min) **[Critical path]**
- Agent C: Module 04: workproducts (~10-15 min) [depends on 03 light read]

**Wave 3: Activities (Sequential - needs 03, 04)**
3. Module 05: activities-roles (~15-20 min)

**Wave 4: Orchestration (Sequential - needs 03, 04, 05)**
4. Module 06: patterns (~10-15 min)

**Wave 5: Finalization (Optional)**
5. Module 07: aliases (~1-2 min)

**Total time (optimized):** ~35-50 minutes (40% faster)

### Phase 2: Full Concurrent JSON Generation

**Current potential:** 9 segments can be generated in parallel  
**Constraint:** Each segment needs its corresponding Phase 1 module

**Optimized Execution:**

**Wave 1: Generate All Segments Concurrently (9 agents)**
```
Agent 1: 01-practice-skeleton.json  ← 01-practice-details.md   (~3 min)
Agent 2: 02-citations.json          ← 02-citations.md          (~2 min)
Agent 3: 03-alphas.json             ← 03-alphas.md             (~15 min) **[Critical path]**
Agent 4: 04-workproducts.json       ← 04-workproducts.md       (~10 min)
Agent 5: 05-activities.json         ← 05-activities-roles.md   (~10 min)
Agent 6: 05-personas.json           ← 05-activities-roles.md   (~5 min)
Agent 7: 05-teams.json              ← 05-activities-roles.md   (~3 min)
Agent 8: 06-patterns.json           ← 06-patterns.md           (~10 min)
Agent 9: 07-aliases.json            ← 07-aliases.md            (~2 min)
```

**Wave 2: Assembly (Automatic)**
```
Python: assemble-practice-json.py   (~1 min)
Python: rebuild-method-json.py      (~1 min, if method)
```

**Total time (optimized):** ~15-20 minutes (vs 60-90 minutes sequential)

---

## Multi-Practice Method Optimization

For methods with N practices:

### Current Sequential Approach
```
Method Plan → Practice 1 (all modules) → Practice 2 (all modules) → 
... → Practice N (all modules) → Method Assembly
```

**Time:** N × (60-90 min) = 120-450 min for 2-5 practices

### Optimized Parallel Approach

**Wave 1: Method Planning**
- Module 00-method-plan (~5-10 min)

**Wave 2: All Practices in Parallel (N agents)**
```
Agent 1: Practice 1 modules (00-07) - can use Wave approach internally
Agent 2: Practice 2 modules (00-07)
...
Agent N: Practice N modules (00-07)
```

**Wave 3: Method Assembly**
- Module 08-method-assembly (~3-5 min)

**Total time (optimized):** ~40-60 minutes (vs 120-450 min)

---

## Implementation Guidelines

### Phase 1 Concurrent Execution

**Wave 2 - Parallel Module Generation:**
```python
# In skill execution:
agents = [
    Agent(description="Generate citations module",
          prompt="""Generate Module 02 (citations) from source materials.
          Read: prompts/phase-1-modules/02-citations.md
          Output: practices/{name}/report-elements/02-citations.md"""),
    
    Agent(description="Generate alphas module", 
          prompt="""Generate Module 03 (alphas) from source materials.
          Read: prompts/phase-1-modules/03-alphas.md
          Read: report-elements/00-analysis-plan.md for alpha decisions
          Output: practices/{name}/report-elements/03-alphas.md"""),
    
    Agent(description="Generate workproducts module",
          prompt="""Generate Module 04 (workproducts) from source materials.
          Read: prompts/phase-1-modules/04-workproducts.md
          Read: report-elements/03-alphas.md for alpha states
          Output: practices/{name}/report-elements/04-workproducts.md""")
]
# All 3 agents run concurrently
```

### Phase 2 Concurrent Execution

**Full Parallel Segment Generation:**
```python
# Spawn all 9 segment generators simultaneously
segment_agents = []
for i, (segment, module, prompt_file) in enumerate(SEGMENTS):
    segment_agents.append(
        Agent(description=f"Generate {segment}",
              prompt=f"""Generate {segment} from {module}.
              Read: {prompt_file}
              Read: report-elements/practice-N/{module}
              Output: json-segments/practice-N/{segment}
              Follow: SEGMENT-SCHEMA-SPECS.md"""))

# Launch all agents at once (they run in parallel)
# Wait for all to complete
# Run assembly script
```

### Method Parallel Practice Generation

**Practice-Level Parallelism:**
```python
# For each practice, spawn complete module generation workflow
practice_agents = []
for i in range(1, num_practices + 1):
    practice_agents.append(
        Agent(description=f"Generate Practice {i} modules",
              subagent_type="general-purpose",
              prompt=f"""Generate all modules (00-07) for Practice {i}.
              Follow optimized wave approach:
              - Sequential: 00, 01
              - Parallel: 02, 03, 04  
              - Sequential: 05, 06, 07
              Output: report-elements/practice-{i}/"""))

# All practices generate in parallel
```

---

## Validation Step Optimization

### Current Validation Steps (Sequential)
```
Phase 2 → Phase 2.5 (schema) → Phase 2.6 (baseline) → Phase 2.7 (integrity) → Phase 2.8 (schema check)
```

**Each step:** ~2-5 minutes

### Optimized Validation (Pipelined)

**Step 2.5: Schema Compliance**
- Run immediately after assembly
- Fix property names in-place

**Step 2.6: Baseline Validation**  
- Run immediately after 2.5
- Fix baseline references in-place

**Step 2.7: Internal Integrity**
- Run immediately after 2.6
- Report issues (manual fixes if needed)

**Step 2.8: Schema Validation**
- Final check after all fixes
- Must pass before delivery

**Pipeline approach:** Run scripts in sequence without user interaction between steps (unless errors need manual fixes)

---

## Expected Performance Improvements

### Single Practice

| Workflow Step | Current Time | Optimized Time | Improvement |
| ------------- | ------------ | -------------- | ----------- |
| Phase 1 (modules) | 60-90 min | 35-50 min | 40% faster |
| Phase 2 (segments) | 60-90 min | 15-20 min | 75% faster |
| Validation | 10-15 min | 8-12 min | 20% faster |
| **Total** | **130-195 min** | **58-82 min** | **55% faster** |

### Multi-Practice Method (3 practices)

| Workflow Step | Current Time | Optimized Time | Improvement |
| ------------- | ------------ | -------------- | ----------- |
| Method planning | 10 min | 10 min | Same |
| Practice modules | 180-270 min | 40-60 min | 75% faster |
| Method assembly | 5 min | 5 min | Same |
| Phase 2 (all practices) | 180-270 min | 20-30 min | 90% faster |
| Validation | 30-45 min | 25-35 min | 20% faster |
| **Total** | **405-600 min** | **100-140 min** | **75% faster** |

---

## Critical Success Factors

### 1. Agent Independence
Each parallel agent must have:
- All required inputs (source materials, prompts, reference docs)
- No shared mutable state
- Clear output location
- Schema compliance requirements

### 2. Error Handling
- If any agent fails in a wave, wave fails
- Failed wave can be restarted without re-running successful agents
- Agent results should be validated before proceeding to next wave

### 3. Resource Management
- Concurrent agents share token budget
- Monitor for API rate limits
- Consider batching parallel work (e.g., 3 at a time vs 9 at once)

### 4. Dependency Management
- Wave boundaries must respect dependencies
- Cannot start Wave 3 until Wave 2 completes
- Clear documentation of what each module needs from previous modules

---

## Implementation Plan

### Phase 1: Update Skill Documentation (SKILL.md)
1. Add "Wave-based Execution" section for Phase 1
2. Update Phase 2 to show explicit parallel execution
3. Add multi-practice method parallelization strategy
4. Update time estimates with optimized figures

### Phase 2: Create Execution Templates
1. Create `parallel-phase-1-waves.md` with agent prompts
2. Create `parallel-phase-2-segments.md` with segment generator prompts
3. Create `parallel-method-practices.md` for method-level parallelism

### Phase 3: Test on Real Practice
1. Run optimized workflow on existing practice (e.g., AWS Well-Architected)
2. Measure actual time savings
3. Validate that concurrent agents produce same quality as sequential
4. Adjust wave boundaries if needed

### Phase 4: Update Skill Code
1. Modify skill to use Agent tool for parallel execution
2. Add wave coordination logic
3. Add error recovery for failed agents in a wave
4. Update user-facing messages to show parallel progress

---

## Example: Optimized Single Practice Translation

**User request:** `/translate-methodology https://aws.amazon.com/architecture/well-architected/`

**Optimized execution:**

```
1. EnterPlanMode (5 min)
   → Determine: Single Practice (AWS Well-Architected Framework)

2. Phase 1 - Wave 1 (Sequential: 8 min)
   Agent: Generate 00-analysis-plan.md (5 min)
   Agent: Generate 01-practice-details.md (3 min)

3. Phase 1 - Wave 2 (Parallel: 20 min)
   Agent A: Generate 02-citations.md (3 min)
   Agent B: Generate 03-alphas.md (20 min) ← critical path
   Agent C: Generate 04-workproducts.md (15 min)

4. Phase 1 - Wave 3 (Sequential: 20 min)
   Agent: Generate 05-activities-roles.md (20 min)

5. Phase 1 - Wave 4 (Sequential: 15 min)
   Agent: Generate 06-patterns.md (15 min)
   Agent: Generate 07-aliases.md (2 min)

6. Phase 1.5 - Assembly (3 min)
   Agent: Assemble research-report.md + cross-reference-index.json

7. Phase 2 - All Segments (Parallel: 20 min)
   Agent 1-9: Generate segments 01-09 simultaneously (20 min) ← critical path: 03-alphas
   Script: Assemble practice JSON (1 min)

8. Validation Pipeline (10 min)
   Script: Phase 2.5 - fix-property-names.py (2 min)
   Script: Phase 2.6 - validate-baseline-references.py (3 min)
   Script: Phase 2.7 - validate-internal-integrity.py (3 min)
   Script: Phase 2.8 - validate-json-schema.js (2 min)

Total: ~101 minutes (vs ~180 minutes sequential)
```

---

## Rollout Strategy

### Immediate (Low Risk)
- ✅ Phase 2 parallel segment generation (already documented, just needs implementation)
- ✅ Validation pipeline automation (combine 2.5, 2.6, 2.7, 2.8 without pauses)

### Short Term (Medium Risk)
- ✅ Phase 1 Wave 2 parallelization (citations + alphas + workproducts)
- ✅ Multi-practice method parallelization (each practice runs independently)

### Future (Higher Risk - needs testing)
- ⚠️ More aggressive Phase 1 parallelization (e.g., 04 parallel with 03)
- ⚠️ Hybrid assembly (start Phase 2 segments as Phase 1 modules complete)

---

## Monitoring and Metrics

Track these metrics to validate optimization:

1. **Total translation time** (planning → validated JSON)
2. **Time per phase** (Phase 1, Phase 2, Validation)
3. **Agent utilization** (how many agents run concurrently)
4. **Error rates** (do parallel agents have more failures?)
5. **Quality metrics** (schema compliance, baseline validation pass rate)

Target:
- **50-75% time reduction** for single practices
- **75%+ time reduction** for multi-practice methods
- **Same or better quality** (validation pass rate ≥ 95%)
