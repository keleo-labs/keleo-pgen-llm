# Narrative Structure Guide

How to select, compose, and map narrative types from the baseline into report sections. Read this when choosing narrative structures during planning (Step 0) or when mapping elements to sections (Step 2).

---

## Purpose-to-Narrative Mapping

Select narrative structures from the baseline's `narrativeTypes` to organise the report. The selection should match the report's purpose:

| Report Purpose | Recommended Primary Structure | Good Secondary Structures |
|---|---|---|
| Formal assessment or analysis | Report Narrative | STAR (for examples), Crawl-Walk-Run (for maturity) |
| Thought leadership or position paper | Essay Narrative | Three-Act/StoryBrand (for framing) |
| Implementation guide or roadmap | Design-Build-Run-Optimize or SDLC | Crawl-Walk-Run (for phasing) |
| Case study or success story | STAR or Three-Act/StoryBrand | Hero's Journey (for transformation arc) |
| Maturity assessment | Crawl-Walk-Run | Report Narrative (for formal structure) |
| Innovation or experimentation | Build-Measure-Learn | PDCA (for iteration cycles) |
| Continuous improvement review | PDCA | Report Narrative (for findings) |
| Architecture evaluation | Report Narrative | SDLC or DBRO (for implementation phases) |
| Project planning | SDLC or DBRO | Crawl-Walk-Run (for phased rollout) |
| Trade-off analysis | Essay Narrative or Report Narrative | STAR (for evidence), PDCA (for evaluation) |
| Document review | Report Narrative | Crawl-Walk-Run (for prioritising improvements) |

---

## Composing Primary + Secondary Structures

A report typically uses **one primary structure** for its top-level organisation, with **secondary structures** shaping individual sections. For example, a Report Narrative overall structure might use STAR for case study sections and Crawl-Walk-Run to frame maturity recommendations.

Rules:
- The primary structure determines the top-level `##` headings
- Secondary structures organise content within those sections (subsections, paragraphs, or lists)
- Do not nest more than two levels of narrative structure — it becomes confusing
- Not every section needs a secondary structure — use them where they add clarity

---

## Narrative Element → Section Heading Mappings

For each narrative type selected, map its `narrativeElements` to natural section headings. Section headings should be plain English — do NOT use the narrative element names as headings unless they happen to be natural (e.g., "Recommendations" is fine; "Act II: The Guide and the Plan" is not).

### Report Narrative

| Narrative Element | Plain Heading Options |
|---|---|
| Executive Summary | "Executive Summary" (natural as-is) |
| Introduction | "Introduction" or a subject-specific heading |
| Methods | "Approach", "How We Assessed This", "Methodology" |
| Results and Findings | "Key Findings", "What We Found", "Assessment Results" |
| Discussion | "Analysis", "What This Means", "Implications" |
| Recommendations | "Recommendations", "Next Steps", "Priority Actions" |

### Essay Narrative

| Narrative Element | Plain Heading Options |
|---|---|
| Introduction | Subject-specific opening heading |
| Defining Key Concepts | "Core Concepts", "Key Principles", domain-specific heading |
| Presenting Evidence | "Evidence and Analysis", "The Case For...", domain-specific |
| Conclusion | "Conclusion", "The Way Forward", "Looking Ahead" |

### STAR

Best used for subsections rather than full report structure:

| Narrative Element | Plain Heading Options |
|---|---|
| Situation | "Background", "The Challenge", "Context" |
| Task | "Objectives", "What Was Needed", "The Goal" |
| Action | "What Was Done", "Approach", domain-specific |
| Result | "Outcomes", "Impact", "Results" |

### SDLC

| Narrative Element | Plain Heading Options |
|---|---|
| Plan | "Planning", "Scope and Objectives", "Requirements" |
| Design | "Design", "Architecture", "Solution Design" |
| Build | "Implementation", "Build", "Development" |
| Test | "Validation", "Testing", "Quality Assurance" |
| Deploy | "Deployment", "Rollout", "Go-Live" |
| Maintain | "Operations", "Ongoing Support", "Sustainment" |

### Design-Build-Run-Optimize (DBRO)

| Narrative Element | Plain Heading Options |
|---|---|
| Design | "Design Phase", "Architecture and Planning" |
| Build | "Build Phase", "Implementation" |
| Run | "Operations", "Day-2 Operations", "Steady State" |
| Optimize | "Optimisation", "Continuous Improvement", "Refinement" |

### Crawl-Walk-Run

| Narrative Element | Plain Heading Options |
|---|---|
| Crawl | "Getting Started", "Foundation", "Phase 1: Establish" |
| Walk | "Building Capability", "Expansion", "Phase 2: Scale" |
| Run | "Full Maturity", "Optimised Operations", "Phase 3: Excel" |

### Hero's Journey

Best used for transformation narratives at section level:

| Narrative Element | Plain Heading Options |
|---|---|
| The Ordinary World | "Where We Are Today", "Current State" |
| The Call to Adventure | "The Catalyst", "Why Change Is Needed" |
| The Ordeal | "The Hard Part", "Key Challenges", "The Transformation" |
| The Return | "The New Normal", "What Changed", "Outcomes" |

### Three-Act / StoryBrand

| Narrative Element | Plain Heading Options |
|---|---|
| Act I: The Hero and the Problem | "The Challenge", "What [Customer] Faces" |
| Act II: The Guide and the Plan | "The Approach", "How [Solution] Helps" |
| Act III: Call to Action and Success | "Getting Started", "The Path Forward", "Expected Outcomes" |

### Build-Measure-Learn

| Narrative Element | Plain Heading Options |
|---|---|
| Build | "Hypothesis and Prototype", "What We Built" |
| Measure | "Measurement and Data", "What We Observed" |
| Learn | "Insights and Pivots", "What We Learned" |

### PDCA

| Narrative Element | Plain Heading Options |
|---|---|
| Plan | "Plan: Defining the Improvement", "Identifying the Gap" |
| Do | "Do: Running the Experiment", "Implementing Changes" |
| Check | "Check: Evaluating Results", "Measuring Impact" |
| Act | "Act: Standardising or Adjusting", "Next Iteration" |

### Domain-Specific Journey Types

When the baseline provides domain-specific narrative types (Partner Ecosystem Journey, Sales Engagement Journey, Digital Transformation Journey, Platform Maturity Journey, etc.), map their elements to headings that describe the journey phase in the reader's language, not the framework's structural labels.
