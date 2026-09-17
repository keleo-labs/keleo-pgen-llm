# Mode 3: Add/Update References

A lightweight mode that adds or updates curated reference content without requiring full remap or reanalysis. References are `AlphaInstance` objects in the `references` array — curated external content (templates, case studies, reference architectures, sample artifacts) that illustrate alphas at specific states.

**When to use:**
- Practice has no `references` array and would benefit from exemplar content
- User wants to add specific references they've found
- Practice has been through initial generation and alpha/state mappings are established
- User explicitly requests "add references" or "find references"

**Prerequisites:** The practice must already have established alpha/state/work-product mappings (i.e., Phase 2 has been completed at some point). This mode uses those mappings as the search framework.

## Step 3A: Load Practice Context

1. **Read the existing practice JSON:**
   ```bash
   python3 utils/extract-reference-names.py <practice>.json --structure
   ```
   Review existing alphas, states, work products, and any existing references.

2. **Read the Phase 2 mapping guide** (if available):
   - `practices/<name>/02-mapping-guide.md` — contains alpha/state/work-product mappings
   - If no mapping guide exists, extract mappings from JSON:
     ```bash
     python3 utils/extract-practice-content.py <practice>.json
     ```

3. **Load baseline and dependencies:**
   ```bash
   python3 utils/discover-dependencies.py --resolve-from <practice>.json --transitive
   ```

4. **Check existing references:**
   ```bash
   python3 utils/extract-reference-names.py <practice>.json --sections references
   ```
   If references already exist, review them for gaps, outdated links, or missing alpha coverage.

## Step 3B: Discover Reference Content

Use the established alpha/state/work-product mappings to guide discovery. Three sources, in order of priority:

1. **User-provided references:**
   - Ask user if they have specific references to add (URLs, documents, templates)
   - Map each to the appropriate alpha/state anchor

2. **Re-examine source materials:**
   - If original source materials are accessible (from citations or user), scan for:
     - Templates, starter documents, sample configurations
     - Reference architectures, design patterns with concrete examples
     - Case studies, exemplary implementations
     - Links to downloadable artifacts (repos, templates, tools)
   - Focus on content that illustrates a specific alpha at a specific state

3. **Secondary research (opt-in):**
   - Ask user whether to conduct secondary research for references
   - If approved, search for:
     - Official templates and starter kits from methodology authors
     - Community tools, reference implementations, open-source exemplars
     - Industry case studies demonstrating the methodology
   - Focus on alphas/states that have no references from other sources
   - Present findings to user for approval before including

## Step 3C: Map References to Anchors

For each discovered reference, map to the Practice Language structure:

1. **Alpha + State anchor:** Which alpha does this reference illustrate, and at what state of maturity?
2. **Evidence (`evidenceBy`):** Map document artifacts to `WorkProductInstance` entries (see guidance below)
3. **Alpha-level links:** Landing pages, introductory or overview resources about the concern
4. **Tags (optional):** Apply domain/lifecycle/organizational tags if applicable
5. **Naming:** Follow the conventions below (concept-oriented names, not content-centric)

**Discovery principle — scope drives search:** The alpha's scope tells you what kind of content is relevant (the concern area at a state), and the work product's scope tells you which specific documents fit as evidence. When browsing a content source, use the alpha scope to identify relevant content at the right maturity level, then examine each document's purpose to determine which work product it evidences. This two-level scoping approach (alpha concern → work product artifact) naturally produces well-structured references.

---

**Reference conventions** — see `references/semantics/alphas.md` §6.6 for full naming rules, instance naming, and merge logic. Key rules:

- **Name pattern:** `"Standard [Qualifier] <AlphaName>"` — concept-centric, not content-centric
- **Description:** Semantic role in terms of alpha state progression, NOT what the linked content contains
- **Instance names scope to the example, NOT the state/LOD** — same real-world instance at different maturity levels shares ONE name
- **Two-level links:** Alpha-level `links` = navigation/overview; `evidenceBy[].links` = specific artifacts
- **Link names:** Use the actual content title, never generic platform labels
- **`evidenceBy` entries:** Each requires `name`, `description`, `workProductName`, `levelOfDetailName`, `links`. Spelled `evidenceBy` (NOT `evidencedBy`).
- **Hub/landing pages:** Alpha-level links only, no `evidenceBy`
- **For methods:** Present one consolidated mapping covering all practices; do NOT prompt per-practice. Wait for user confirmation.

## Step 3D: Update Practice JSON

For a **single practice**, follow steps 1-5 below. For a **method** (multiple practices), see **Step 3E: Method-Level Orchestration** instead.

1. **Backup first:**
   ```bash
   python3 utils/backup-practice.py <directory>/
   ```

2. **Write a compact spec file** and apply with `build-references.py`:
   ```bash
   # Write compact spec (see build-references.py header for format)
   # Then validate + merge into practice in one step:
   python3 utils/build-references.py <practice>.json --spec refs-spec.json --fix
   ```
   The utility validates all anchors (alphaName, stateName, workProductName, levelOfDetailName) against the practice, expands compact shorthand to full AlphaInstance objects, and handles same-name merge automatically (highest state wins, links and evidenceBy aggregated).

   Link shorthand: `"https://url|Label"` expands to `{"name": "Label", "uri": "https://url"}`.

   Alternative: output expanded JSON without applying:
   ```bash
   python3 utils/build-references.py <practice>.json --spec refs-spec.json -o _references.json
   python3 utils/patch-practice-json.py <practice>.json --set-key references --patch-file _references.json
   ```

3. **Validate updated practice:**
   ```bash
   python3 utils/assess-practice.py <practice>.json --baseline <baseline>.json --schema deps/language.schema.json
   ```

5. **Bump version (patch):**
   ```bash
   python3 utils/apply-versioning.py <practice>.json --bump patch --fix
   ```

6. **Re-package into `.keleo`:**
   Follow the standard packaging process from Post-Update Packaging section in SKILL.md.

7. **Report results:**
   ```
   Added N references to "<practice-name>":
   - [Reference 1]: [alphaName] at [stateName] — [link]
   - [Reference 2]: [alphaName] at [stateName] — [link]
   ...
   
   Version bumped: X.Y.Z → X.Y.(Z+1)
   Package updated: bundles/<name>.keleo
   ```

## Step 3E: Method-Level Orchestration (Mode 3)

When adding references to a **method** with multiple constituent practices:

1. **Backup the method directory:**
   ```bash
   python3 utils/backup-practice.py practices/<method-name>/
   ```

2. **Identify all constituent practices** from the method JSON's `practiceNames` array. List them with their alpha structures so content can be mapped accurately.

3. **Batch discovery:** Browse the content source once for all practices, grouping discovered content by practice. Present a single consolidated mapping to the user for approval — do NOT prompt per-practice.

4. **Apply references to each practice** using compact specs:
   ```bash
   # Repeat for each practice with references
   python3 utils/build-references.py <practice>.json --spec <practice>-refs-spec.json --fix
   ```

5. **Batch version bump** all modified practices plus the method JSON in one command:
   ```bash
   python3 utils/apply-versioning.py --dir practices/<method-name>/ --bump patch --fix
   ```

6. **Repackage** the full method into `.keleo`:
   ```bash
   python3 utils/package-keleo.py \
     --documents <baseline>.json <practice1>.json ... <method>.json \
     --name <method-name> --version <new-version> \
     --description "..." -o bundles/<method-name>.keleo --verify
   ```

7. **Report results** with a summary table showing references per practice.

8. **Clean up** any temporary reference JSON files created during patching.
