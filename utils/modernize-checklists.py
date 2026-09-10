#!/usr/bin/env python3
"""Transform checklist items from criteria-style to action-oriented.

Two transformation modes:
  names          Rewrite names from past-participle to imperative verb phrase (default)
  --descriptions Rewrite descriptions from operational truth to instructive purpose

Note: --tests is deprecated. Mechanical test creation produces skeleton tests
that violate the information independence rule (test.then echoes the description
in past tense with empty given/when). Tests require semantic authoring, not
mechanical transformation.

Usage:
    # Preview all changes (dry run)
    python3 utils/modernize-checklists.py <file.json> --descriptions --tests

    # Apply all changes
    python3 utils/modernize-checklists.py <file.json> --fix --descriptions --tests

    # Batch mode (all JSONs in a directory)
    python3 utils/modernize-checklists.py --dir practices/red-hat-sales-plays/ --fix --descriptions --tests
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Verb map: past participle → imperative
# ---------------------------------------------------------------------------

_VERB_MAP = {
    "achieved": "Achieve",
    "acknowledged": "Acknowledge",
    "agreed": "Agree",
    "aligned": "Align",
    "analyzed": "Analyze",
    "approved": "Approve",
    "articulated": "Articulate",
    "assessed": "Assess",
    "assigned": "Assign",
    "bounded": "Bound",
    "captured": "Capture",
    "catalogued": "Catalogue",
    "completed": "Complete",
    "conducted": "Conduct",
    "configured": "Configure",
    "confirmed": "Confirm",
    "connected": "Connect",
    "consolidated": "Consolidate",
    "constructed": "Construct",
    "covered": "Cover",
    "created": "Create",
    "customized": "Customize",
    "defined": "Define",
    "delivered": "Deliver",
    "demonstrated": "Demonstrate",
    "deployed": "Deploy",
    "designed": "Design",
    "determined": "Determine",
    "developed": "Develop",
    "documented": "Document",
    "embedded": "Embed",
    "enabled": "Enable",
    "enforced": "Enforce",
    "engaged": "Engage",
    "established": "Establish",
    "evaluated": "Evaluate",
    "executed": "Execute",
    "explored": "Explore",
    "formalized": "Formalize",
    "framed": "Frame",
    "gathered": "Gather",
    "guided": "Guide",
    "identified": "Identify",
    "implemented": "Implement",
    "initiated": "Initiate",
    "integrated": "Integrate",
    "launched": "Launch",
    "maintained": "Maintain",
    "managed": "Manage",
    "mapped": "Map",
    "measured": "Measure",
    "met": "Meet",
    "migrated": "Migrate",
    "monitored": "Monitor",
    "negotiated": "Negotiate",
    "operationalized": "Operationalize",
    "optimized": "Optimize",
    "organized": "Organize",
    "performed": "Perform",
    "planned": "Plan",
    "positioned": "Position",
    "prepared": "Prepare",
    "presented": "Present",
    "prioritized": "Prioritize",
    "produced": "Produce",
    "provisioned": "Provision",
    "published": "Publish",
    "qualified": "Qualify",
    "quantified": "Quantify",
    "recognized": "Recognize",
    "refined": "Refine",
    "reinforced": "Reinforce",
    "represented": "Represent",
    "requested": "Request",
    "resolved": "Resolve",
    "reviewed": "Review",
    "scheduled": "Schedule",
    "scoped": "Scope",
    "scored": "Score",
    "secured": "Secure",
    "selected": "Select",
    "specified": "Specify",
    "standardized": "Standardize",
    "structured": "Structure",
    "submitted": "Submit",
    "tailored": "Tailor",
    "targeted": "Target",
    "tested": "Test",
    "traced": "Trace",
    "tracked": "Track",
    "trained": "Train",
    "validated": "Validate",
    "verified": "Verify",
}

# Reverse map: imperative → past participle
_IMP_TO_PP = {v.lower(): k for k, v in _VERB_MAP.items()}

_CRITERIA_ENDINGS = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _VERB_MAP) + r')$',
    re.IGNORECASE,
)

# Proper nouns / acronyms to preserve when lowercasing
_PRESERVE_CASE = {
    "Red", "Hat", "RHEL", "OpenShift", "Ansible", "AWS", "Azure", "Google",
    "MEDDPICC", "TOGAF", "SAFe", "CIO", "CTO", "CFO", "VP", "IT", "AI",
    "ML", "SaaS", "PaaS", "IaaS", "TCO", "ROI", "KPI", "SLO", "SLA",
    "GPU", "ACM", "AIOps", "DevOps", "GitOps", "RBAC", "GDPR", "SOC",
    "SOX", "PCI", "TDP", "EKS", "AKS", "GKE", "VMware", "MEDDPICC",
    "EB", "POC", "BANT", "CRM", "ERP", "ISV", "OEM", "MSP",
    "Unix", "Windows", "Linux", "Kubernetes", "Docker", "GitHub", "Slack",
    "SAP", "Salesforce", "ServiceNow", "Jira", "Terraform", "Prometheus",
    "Grafana", "Jenkins", "ArgoCD", "Quay", "Tekton", "Istio", "Knative",
}

# ---------------------------------------------------------------------------
# Title-case helpers
# ---------------------------------------------------------------------------

def _is_kebab_case(name):
    return '-' in name and name == name.lower()


def _kebab_to_words(name):
    return name.replace('-', ' ')


def _title_case_word(w):
    """Title-case a single word, preserving acronyms and hyphenated segments."""
    if w.isupper() and len(w) > 1:
        return w
    if '-' in w:
        parts = w.split('-')
        return '-'.join(_title_case_word(p) for p in parts)
    upper_prefix = re.match(r'^[A-Z]{2,}', w)
    if upper_prefix:
        return w
    return w.capitalize()


def _title_case(text):
    """Title-case with common small words kept lowercase (except at start)."""
    small = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
             'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'vs'}
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in small:
            result.append(_title_case_word(w))
        else:
            result.append(w.lower())
    return ' '.join(result)


def _lower_word(w):
    """Lowercase a single word, preserving acronyms/proper nouns and hyphens."""
    if w in _PRESERVE_CASE:
        return w
    if w.isupper() and len(w) > 1:
        return w
    if re.match(r'^[A-Z]{2,}', w):
        return w
    if '-' in w:
        return '-'.join(_lower_word(p) for p in w.split('-'))
    return w.lower()


def _lower_subject(subject):
    """Lowercase the subject, preserving acronyms and proper nouns."""
    return ' '.join(_lower_word(w) for w in subject.split())


def _fix_compound_verbs(text):
    """Fix remaining PP verbs after conjunctions: 'and prioritized' → 'and prioritize'."""
    pp_alt = '|'.join(re.escape(k) for k in _VERB_MAP)
    pattern = re.compile(
        r'\b(and|or)\s+(' + pp_alt + r')\b', re.IGNORECASE,
    )

    def _replace(m):
        conj = m.group(1)
        pp = m.group(2).lower()
        imp = _VERB_MAP.get(pp)
        return f"{conj} {imp.lower()}" if imp else m.group(0)

    return pattern.sub(_replace, text)


def _finish_desc(text):
    """Ensure description starts uppercase, compound verbs fixed, ends with period."""
    text = text.strip()
    if not text:
        return text
    text = _fix_compound_verbs(text)
    text = text[0].upper() + text[1:]
    if not text.endswith('.'):
        text += '.'
    text = text.replace('..', '.').replace('  ', ' ')
    return text


# ---------------------------------------------------------------------------
# Name transformation
# ---------------------------------------------------------------------------

def transform_checklist_name(name):
    """Transform a criteria-style checklist name to imperative form.

    Returns (new_name, transformed: bool).
    """
    original = name.strip()
    if not original:
        return original, False

    working = _kebab_to_words(original) if _is_kebab_case(original) else original

    m = _CRITERIA_ENDINGS.search(working)
    if not m:
        return original, False

    past_participle = m.group(1).lower()
    imperative = _VERB_MAP.get(past_participle)
    if not imperative:
        return original, False

    subject = working[:m.start()].strip()

    inner_match = _CRITERIA_ENDINGS.search(subject)
    if inner_match:
        inner_pp = inner_match.group(1).lower()
        inner_imp = _VERB_MAP.get(inner_pp)
        if inner_imp:
            real_subject = subject[:inner_match.start()].strip()
            between = subject[inner_match.end():].strip()
            if not between:
                new_name = f"{inner_imp} and {imperative} {real_subject}"
                return _title_case(new_name), True

    if subject:
        new_name = f"{imperative} {subject}"
    else:
        new_name = imperative

    return _title_case(new_name), True


# ---------------------------------------------------------------------------
# Description transformation
# ---------------------------------------------------------------------------

def transform_description(name, desc):
    """Transform a criteria-style description to action-oriented.

    Uses the checklist name's verb context to anchor transformations.
    Returns (new_desc, transformed: bool).
    """
    if not desc or not desc.strip():
        return desc, False

    text = desc.strip()

    # --- Pattern 1: "Subject has/have been PP ..." ---
    m = re.match(
        r'^(.+?)\s+(?:has|have)\s+been\s+(\w+ed)\b(.*)$',
        text, re.IGNORECASE,
    )
    if m:
        subject, pp, rest = m.group(1), m.group(2).lower(), m.group(3)
        imp = _VERB_MAP.get(pp)
        if imp:
            return _finish_desc(f"{imp} {_lower_subject(subject)}{rest}"), True

    # --- Pattern 2: "Subject is/are PP ..." ---
    m = re.match(
        r'^(.+?)\s+(?:is|are)\s+(\w+ed)\b(.*)$',
        text, re.IGNORECASE,
    )
    if m:
        subject, pp, rest = m.group(1), m.group(2).lower(), m.group(3)
        imp = _VERB_MAP.get(pp)
        if imp:
            return _finish_desc(f"{imp} {_lower_subject(subject)}{rest}"), True

    # --- Pattern 3: Use name's verb to anchor the transformation ---
    # The name is already imperative ("Identify Target AI Personas").
    # Find the PP form of the name's verb in the description and restructure.
    name_words = name.split() if name else []
    lead_verb = name_words[0] if name_words else ""
    pp_form = _IMP_TO_PP.get(lead_verb.lower())

    if pp_form:
        pattern = re.compile(r'\b' + re.escape(pp_form) + r'\b', re.IGNORECASE)
        m = pattern.search(text)
        if m:
            before = text[:m.start()].strip()
            after = text[m.end():].strip()
            # Strip trailing auxiliary (+ optional adverb) before PP
            before = re.sub(
                r'\s+(?:is|are|was|were|has been|have been)(?:\s+\w+ly)?\s*$',
                '', before, flags=re.IGNORECASE,
            )
            subj = _lower_subject(before) if before else ""
            new_desc = f"{lead_verb} {subj}" if subj else lead_verb
            if after:
                new_desc += f" {after}"
            return _finish_desc(new_desc), True

    # --- Pattern 4: Standalone "Subject PP rest." (no auxiliary, no name match) ---
    # Conservative: only match PP words followed by a preposition, conjunction,
    # or end-of-text (not followed by a content word, which suggests adjective use).
    _DETERMINERS = {'the', 'a', 'an', 'this', 'that', 'each', 'every',
                    'some', 'any', 'no', 'its', 'their', 'our', 'your',
                    'his', 'her', 'my', 'all', 'most', 'both'}
    _FUNCTION_WORDS = _PREPOSITIONS | {'and', 'or', 'but', 'yet', 'so',
                                        'the', 'a', 'an', 'that', 'which'}
    words = text.split()
    for i, word in enumerate(words):
        clean = re.sub(r'[.,;:!?()\[\]]', '', word).lower()
        if clean not in _VERB_MAP:
            continue
        if i == 0:
            continue
        # Skip adjective position: PP preceded by a determiner
        prev = re.sub(r'[.,;:!?()\[\]]', '', words[i - 1]).lower()
        if prev in _DETERMINERS:
            continue
        # Skip adjective position: PP followed by a content word (noun/adj)
        if i + 1 < len(words):
            next_clean = re.sub(r'[.,;:!?()\[\]]', '', words[i + 1]).lower()
            if next_clean and next_clean not in _FUNCTION_WORDS:
                continue
        imp = _VERB_MAP[clean]
        before = ' '.join(words[:i])
        after = ' '.join(words[i + 1:])
        before = re.sub(
            r'\s+(?:is|are|was|were)\s*$', '', before, flags=re.IGNORECASE,
        )
        new_desc = f"{imp} {_lower_subject(before)}"
        if after:
            new_desc += f" {after}"
        return _finish_desc(new_desc), True

    return desc, False


# ---------------------------------------------------------------------------
# Test creation
# ---------------------------------------------------------------------------

_PREPOSITIONS = {
    'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'across',
    'through', 'using', 'covering', 'including', 'based', 'where',
    'when', 'after', 'before', 'during', 'between', 'within', 'against',
    'over', 'under', 'into', 'upon', 'per', 'via', 'alongside',
}

_STOP_WORDS = frozenset({
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
    'should', 'may', 'might', 'must', 'can', 'could', 'that', 'which',
    'who', 'this', 'these', 'those', 'it', 'its', 'not', 'no', 'as', 'if',
})


def _extract_desc_tokens(text):
    """Extract content tokens for echo detection."""
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    return {w for w in cleaned.split() if w not in _STOP_WORDS and len(w) > 1}


def _to_assertion(text):
    """Convert imperative text to assertion form for test.then clauses.

    'Identify target AI personas in the org' → 'target AI personas identified in the org'
    'Identify X and prioritize' → 'X identified and prioritized'
    """
    words = text.strip().rstrip('.').split()
    if not words:
        return text

    verb = words[0]
    pp = _IMP_TO_PP.get(verb.lower())
    if not pp:
        return text.strip().rstrip('.')

    rest = words[1:]
    if not rest:
        return text.strip().rstrip('.')

    # Check for compound verb: "Verb1 subject and Verb2 [tail]"
    # Only match when the second verb is terminal or followed by a preposition
    # (avoids false positives like "and target measures" where "target" is adjective)
    compound_idx = None
    compound_pp = None
    for i in range(len(rest) - 1):
        if rest[i].lower() in ('and', 'or'):
            next_pp = _IMP_TO_PP.get(rest[i + 1].lower())
            if next_pp:
                after_verb = i + 2
                if after_verb >= len(rest):
                    compound_idx = i
                    compound_pp = next_pp
                    break
                next_after = rest[after_verb].lower().rstrip('.,;:')
                if next_after in _PREPOSITIONS:
                    compound_idx = i
                    compound_pp = next_pp
                    break

    if compound_idx is not None:
        subject = ' '.join(rest[:compound_idx])
        conj = rest[compound_idx]
        tail = ' '.join(rest[compound_idx + 2:])
        if len(subject.split()) >= 2:
            assertion = f"{subject} {pp} {conj} {compound_pp}"
            if tail:
                assertion += f" {tail}"
            return assertion

    # Simple case: find first preposition to locate subject boundary
    subject_end = len(rest)
    for i, w in enumerate(rest):
        if w.lower() in _PREPOSITIONS:
            subject_end = i
            break

    subject = ' '.join(rest[:subject_end])
    tail = ' '.join(rest[subject_end:])

    # Sanity check: subject should be at least 2 words; otherwise the split
    # is likely wrong (e.g., "Deliver what to say..." splits at "to")
    if subject and len(subject.split()) >= 2:
        assertion = f"{subject} {pp}"
        if tail:
            assertion += f" {tail}"
        return assertion

    # Fall back to original text if split looks wrong
    return text.strip().rstrip('.')


def create_test_from_description(name, original_desc):
    """Create a test object from the checklist description.

    If the description is imperative (already transformed), converts then clauses
    to assertion form for proper completion criteria.
    """
    if not original_desc or not original_desc.strip():
        return None

    desc_clean = original_desc.strip().rstrip('.')

    then_clauses = _split_then_clauses(desc_clean)
    then_clauses = [_to_assertion(c) for c in then_clauses]
    test_name = _derive_test_name(name)

    return {
        "name": test_name,
        "description": "Definition of done.",
        "given": [],
        "when": [],
        "then": then_clauses,
    }


def _split_then_clauses(text):
    """Split a description into individual then clauses.

    Only splits when the result produces 2-3 meaningful, complete clauses.
    Otherwise returns the whole text as a single clause.
    """
    # Split on " and " when followed by a capital letter (new clause start)
    # Each clause must be substantial (>30 chars) to avoid fragmenting compound phrases
    parts = re.split(r'\s+and\s+(?=[A-Z])', text)
    if 2 <= len(parts) <= 3 and all(len(p.strip()) > 30 for p in parts):
        return [p.strip() for p in parts]

    # Split on "; "
    parts = text.split('; ')
    if 2 <= len(parts) <= 3 and all(len(p.strip()) > 30 for p in parts):
        return [p.strip() for p in parts]

    return [text]


def _derive_test_name(name):
    """Derive a test name from the imperative checklist name.

    "Assess Customer's AI Maturity Level" → "Customer AI Maturity Level verification"
    """
    words = name.split()
    if not words:
        return "Verification"

    # Handle compound verbs: "Define and Monitor SLOs" → skip verbs + conjunction
    i = 0
    while i < len(words):
        w = words[i]
        if w.lower() in ('and', 'or'):
            i += 1
            continue
        if w.lower() in _IMP_TO_PP:
            i += 1
            continue
        break

    subject = ' '.join(words[i:]) if i < len(words) else ' '.join(words[1:])
    if subject:
        return f"{subject} verification"
    return f"{words[0]} verification"


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process_checklist(checklist, path, do_names=True, do_descriptions=False,
                      do_tests=False):
    """Process a single checklist array. Returns list of changes."""
    changes = []
    for i, item in enumerate(checklist):
        name = item.get("name", "")
        original_desc = item.get("description", "")

        # 1. Name transformation
        if do_names:
            new_name, transformed = transform_checklist_name(name)
            if transformed:
                changes.append({
                    "path": f"{path}[{i}].name",
                    "old": name,
                    "new": new_name,
                    "type": "name",
                })
                item["name"] = new_name

        current_name = item.get("name", "")

        # 2. Description transformation (with echo guard)
        if do_descriptions:
            desc = item.get("description", "")
            new_desc, desc_transformed = transform_description(current_name, desc)
            if desc_transformed:
                # Guard: skip if transformed description echoes the name
                name_toks = _extract_desc_tokens(current_name)
                desc_toks = _extract_desc_tokens(new_desc)
                if name_toks and desc_toks:
                    overlap = len(name_toks & desc_toks) / max(len(name_toks), len(desc_toks))
                    if overlap > 0.85:
                        continue  # would produce echo — skip
                changes.append({
                    "path": f"{path}[{i}].description",
                    "old": desc,
                    "new": new_desc,
                    "type": "description",
                })
                item["description"] = new_desc

        # 3. Test creation — DEPRECATED
        # Mechanical test creation produces skeleton tests that violate
        # information independence (test.then echoes description in past tense
        # with empty given/when). Tests require semantic authoring.
        if do_tests:
            pass  # no-op; deprecation warning emitted in main()

    return changes


def process_file(filepath, fix=False, do_names=True, do_descriptions=False,
                 do_tests=False):
    """Process a single JSON file. Returns (changes, errors)."""
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return [], [str(e)]

    kind = data.get("kind", "")
    if kind not in ("practice", "method", "practiceBaseline"):
        return [], [f"Skipping {filepath}: kind={kind!r}"]

    all_changes = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for alpha in source.get("alphas", []):
            alpha_name = alpha.get("name", "")
            for state in alpha.get("states", []):
                state_name = state.get("name", "")
                path = f"alphas['{alpha_name}'].states['{state_name}'].checklist"
                changes = process_checklist(
                    state.get("checklist", []), path,
                    do_names, do_descriptions, do_tests,
                )
                all_changes.extend(changes)

        for wp in source.get("workProducts", []):
            wp_name = wp.get("name", "")
            for lod in wp.get("levelsOfDetail", []):
                lod_name = lod.get("name", "")
                path = f"workProducts['{wp_name}'].LODs['{lod_name}'].checklist"
                changes = process_checklist(
                    lod.get("checklist", []), path,
                    do_names, do_descriptions, do_tests,
                )
                all_changes.extend(changes)

    if fix and all_changes:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

    return all_changes, []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Transform checklist items from criteria-style to action-oriented",
    )
    parser.add_argument("file", nargs="?", help="JSON file to process")
    parser.add_argument("--dir", help="Process all JSON files in a directory")
    parser.add_argument("--fix", action="store_true",
                        help="Apply changes (default: dry run)")
    parser.add_argument("--descriptions", action="store_true",
                        help="Transform descriptions to action-oriented")
    parser.add_argument("--tests", action="store_true",
                        help="DEPRECATED — mechanical test creation produces skeleton tests")
    parser.add_argument("--no-names", action="store_true",
                        help="Skip name transformation")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.error("Provide either a file or --dir")

    files = []
    if args.dir:
        for f in sorted(os.listdir(args.dir)):
            if (f.endswith('.json') and not f.startswith('_')
                    and not f.startswith('change-request')):
                files.append(os.path.join(args.dir, f))
    elif args.file:
        files = [args.file]

    if args.tests:
        print(
            "WARNING: --tests is deprecated. Mechanical test creation produces "
            "skeleton tests that violate information independence (test.then "
            "echoes description in past tense, empty given/when). Tests require "
            "semantic authoring during practice remap, not mechanical "
            "transformation. Flag is now a no-op.",
            file=sys.stderr,
        )

    do_names = not args.no_names
    total_changes = {"name": 0, "description": 0, "test": 0}
    total_files = 0
    all_results = []

    for filepath in files:
        changes, errors = process_file(
            filepath, args.fix, do_names, args.descriptions, args.tests,
        )
        for err in errors:
            print(f"  {err}", file=sys.stderr)

        if changes:
            total_files += 1
            for c in changes:
                total_changes[c["type"]] = total_changes.get(c["type"], 0) + 1

            if args.json:
                all_results.append({"file": filepath, "changes": changes})
            else:
                by_type = {}
                for c in changes:
                    by_type.setdefault(c["type"], []).append(c)
                counts = ", ".join(f"{len(v)} {k}s" for k, v in by_type.items())
                print(f"\n{filepath}: {counts}")
                for c in changes[:10]:
                    if c["type"] == "test":
                        print(f"  + test for item at {c['path']}: {c['new']}")
                    else:
                        print(f"  [{c['type']}] {c['old']!r} → {c['new']!r}")
                if len(changes) > 10:
                    print(f"  ... and {len(changes) - 10} more")

    if args.json:
        json.dump({"totalFiles": total_files, "totalChanges": total_changes,
                    "results": all_results}, sys.stdout, indent=2)
    else:
        mode = "applied" if args.fix else "would apply (dry run)"
        print(f"\n{'='*60}")
        summary = ", ".join(f"{v} {k}s" for k, v in total_changes.items() if v)
        print(f"Total: {summary or 'no changes'} across {total_files} files {mode}")
        if not args.fix and sum(total_changes.values()) > 0:
            print("Run with --fix to apply changes")


if __name__ == "__main__":
    main()
