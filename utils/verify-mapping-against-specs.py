#!/usr/bin/env python3
"""Verify Phase 2 mapping guide against Gherkin specs before JSON generation.

Extracts structured mapping decisions from Phase 2 markdown and checks them
against spec rules, catching errors before Phase 3.

Usage:
    # Basic verification
    python3 utils/verify-mapping-against-specs.py practices/<name>/02-mapping-guide.md

    # With baseline for reference checking
    python3 utils/verify-mapping-against-specs.py practices/<name>/02-mapping-guide.md \
      --baseline deps/platform-adoption-kernel.json

    # With parent practice for cross-practice reference resolution
    python3 utils/verify-mapping-against-specs.py practices/<name>/02-mapping-guide.md \
      --baseline <baseline.json> --parent <parent-practice.json>

    # Baseline mapping guide (skips extension-only checks)
    python3 utils/verify-mapping-against-specs.py baselines/<name>/02-mapping-guide.md --kind baseline

    # Compact output
    python3 utils/verify-mapping-against-specs.py <mapping.md> --baseline <b.json> --summary
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


# --- Extractors ---

def extract_delineation(text):
    """Extract delineation analysis section."""
    result = {"primaryAlpha": None, "alphaCount": None, "decision": None}

    m = re.search(
        r'\*\*Primary Alpha\*\*[:\s]+(.+?)(?:\s*[—\-]|$)',
        text, re.MULTILINE,
    )
    if m:
        result["primaryAlpha"] = m.group(1).strip().rstrip("*")

    m = re.search(r'\*\*Alpha Coverage Count\*\*[:\s]+(\d+)', text)
    if m:
        result["alphaCount"] = int(m.group(1))

    m = re.search(r'\*\*Decision\*\*[:\s]+(Single Practice|Method)', text)
    if m:
        result["decision"] = m.group(1)

    return result


ALPHA_BOLD_RE = re.compile(
    r'^\*\*Alpha:\s+(.+?)\*\*\s+\(([^)]+)\)',
    re.MULTILINE,
)

ALPHA_HEADING_RE = re.compile(
    r'^###\s+Alpha:\s+(.+?)(?:\s+\(([^)]+)\))?\s*$',
    re.MULTILINE,
)


def _parse_alpha_block(name, alpha_type, block):
    """Parse a single alpha block into a structured dict."""
    ct = re.search(r'\*{0,2}contributesTo:?\*{0,2}\s*(.+)', block)
    mt = re.search(r'\*{0,2}mapsTo:?\*{0,2}\s*(.+)', block)
    focus = re.search(r'\*{0,2}Focus Name:?\*{0,2}\s*(.+)', block)
    desc = re.search(r'\*{0,2}Description:?\*{0,2}\s*(.+)', block)

    if not alpha_type or alpha_type == "?":
        md = re.search(r'\*\*Mapping Decision:\*\*\s*(SPECIALIZATION|REDECLARATION|VARIANT)', block)
        if md:
            alpha_type = md.group(1).capitalize()
        elif re.search(r'\bRedeclaration\b', block[:200], re.IGNORECASE):
            alpha_type = "Redeclaration"
        else:
            alpha_type = "Specialization"

    states = re.findall(r'\*\*State:\s+(.+?)\*\*', block)
    if not states:
        states = re.findall(r'^\s*\d+\.\s+\*\*(.+?)\*\*', block, re.MULTILINE)
    if not states:
        state_list = re.search(r'New alpha states:\s*(.+)', block)
        if state_list:
            states = [s.strip() for s in state_list.group(1).split(",")]

    relates_to = []
    has_directions = False
    for rt in re.finditer(r'alphaName:\s*"?([^"\n]+)"?', block):
        relates_to.append(rt.group(1).strip())
    if relates_to:
        has_directions = bool(re.search(r'direction:\s*(outgoing|incoming|mutual)', block))
    if not relates_to:
        for rt in re.finditer(r'\*\*\s*\w[\w\s]*\|\s*([^|]+?)\s*\|', block):
            relates_to.append(rt.group(1).strip())
        if relates_to:
            has_directions = True

    normalized_type = (alpha_type or "Specialization").split("-")[0].strip().capitalize()
    if "redecl" in (alpha_type or "").lower():
        normalized_type = "Redeclaration"

    return {
        "name": name,
        "type": normalized_type,
        "contributesTo": ct.group(1).strip() if ct else None,
        "mapsTo": mt.group(1).strip() if mt else None,
        "focusName": focus.group(1).strip() if focus else None,
        "description": desc.group(1).strip() if desc else None,
        "stateCount": len(states),
        "states": states,
        "relatesTo": relates_to,
        "relatesTo_directions": has_directions,
    }


def _find_alpha_blocks(text):
    """Find all alpha blocks in the text, handling both bold and heading formats."""
    entries = []

    for m in ALPHA_BOLD_RE.finditer(text):
        entries.append((m.start(), m.end(), m.group(1).strip(), m.group(2).strip()))

    for m in ALPHA_HEADING_RE.finditer(text):
        atype = m.group(2).strip() if m.group(2) else "?"
        entries.append((m.start(), m.end(), m.group(1).strip(), atype))

    entries.sort(key=lambda e: e[0])

    seen_positions = set()
    unique = []
    for start, end, name, atype in entries:
        if start not in seen_positions:
            seen_positions.add(start)
            unique.append((start, end, name, atype))

    return unique


def extract_alphas(text):
    """Extract alpha definitions from mapping guide."""
    alphas = []
    entries = _find_alpha_blocks(text)

    for i, (start, end, name, atype) in enumerate(entries):
        block_start = end
        if i + 1 < len(entries):
            block_end = entries[i + 1][0]
        else:
            next_h = re.search(r'^#{2,3}\s+(?!.*Alpha)', text[block_start:], re.MULTILINE)
            block_end = block_start + next_h.start() if next_h else len(text)

        block = text[block_start:block_end]
        alpha = _parse_alpha_block(name, atype, block)
        alphas.append(alpha)

    return alphas


def extract_aliases(text):
    """Extract alias mappings."""
    aliases = []
    pattern = re.compile(
        r'\*\*Element Type:\*\*\s*(\w+)\s*\n'
        r'\s*-\s*\*\*Canonical Name:\*\*\s*(.+?)\n'
        r'\s*-\s*\*\*Alias Name:\*\*\s*(.+?)\n',
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        aliases.append({
            "elementType": m.group(1).strip(),
            "canonicalName": m.group(2).strip(),
            "aliasName": m.group(3).strip(),
        })
    return aliases


ACTIVITY_HEADER_RE = re.compile(
    r'^\*\*Activity:\s+(.+?)\*\*',
    re.MULTILINE,
)


def extract_activities(text):
    """Extract activity mappings."""
    activities = []
    matches = list(ACTIVITY_HEADER_RE.finditer(text))

    for i, match in enumerate(matches):
        start = match.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            next_h = re.search(r'^#{2,3}\s+', text[start:], re.MULTILINE)
            end = start + next_h.start() if next_h else len(text)

        block = text[start:end]

        as_match = re.search(r'\*\*Activity Space Name:\*\*\s*(.+)', block)
        ct_alphas = re.findall(r'Alpha Name:\s*(.+?)$', block, re.MULTILINE)

        comp_match = re.search(r'\*\*Required Competencies:\*\*\s*\n((?:\s*-\s*.+\n)*)', block)
        comps = []
        if comp_match:
            comps = [c.strip().lstrip("- ") for c in comp_match.group(1).strip().split("\n")]

        level_refs = re.findall(
            r'Competency Level Name:\s*(.+)',
            block,
        )

        activities.append({
            "name": match.group(1).strip(),
            "activitySpaceName": as_match.group(1).strip() if as_match else None,
            "contributesToAlphas": [a.strip() for a in ct_alphas],
            "competencies": comps,
            "competencyLevels": [l.strip() for l in level_refs],
        })

    return activities


def extract_keywords(text):
    """Extract keywords from mapping guide."""
    m = re.search(r'\*\*Keywords?:?\*\*\s*:?\s*(.+)', text)
    if m:
        return [k.strip() for k in m.group(1).split(",") if k.strip()]
    m = re.search(r'^##\s+Keywords?\s*\n(.+)', text, re.MULTILINE)
    if m:
        return [k.strip() for k in m.group(1).split(",") if k.strip()]
    return []


def extract_competency_refs(text):
    """Extract all competency name and level references."""
    names = set()
    levels = set()

    for m in re.finditer(r'Competency Name:\s*(.+)', text):
        val = m.group(1).strip()
        if not val.startswith("*"):
            names.add(val)
    for m in re.finditer(r'Competency Level Name:\s*(.+)', text):
        val = m.group(1).strip()
        if not val.startswith("*"):
            levels.add(val)
    for m in re.finditer(r'\*\*Required Competencies:\*\*\s*\n((?:\s*-\s*[A-Z].+\n)*)', text):
        for line in m.group(1).strip().split("\n"):
            val = line.strip().lstrip("- ")
            if val and not val.startswith("*") and not val.startswith("Competency"):
                names.add(val)

    return {"names": sorted(n for n in names if n), "levels": sorted(l for l in levels if l)}


def extract_mapping_data(text):
    """Extract all structured data from Phase 2 mapping guide."""
    return {
        "delineation": extract_delineation(text),
        "alphas": extract_alphas(text),
        "aliases": extract_aliases(text),
        "activities": extract_activities(text),
        "keywords": extract_keywords(text),
        "competencyRefs": extract_competency_refs(text),
    }


# --- Checkers ---

def _finding(rule_id, severity, message, evidence=None):
    f = {"rule": rule_id, "severity": severity, "message": message}
    if evidence:
        f["evidence"] = evidence
    return f


def check_no_floating_alphas(extracted):
    """@rule:semantic-001 — Every new alpha must have contributesTo or mapsTo."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["type"] in ("Redeclaration", "Redeclaration - Enrichment", "Redeclaration"):
            continue
        if not alpha["contributesTo"] and not alpha["mapsTo"]:
            findings.append(_finding(
                "semantic-001", "error",
                f"Alpha '{alpha['name']}' has no contributesTo or mapsTo — floating alpha",
                evidence=f"Type: {alpha['type']}",
            ))
    return findings


def check_mutual_exclusivity(extracted):
    """@rule:semantic-002 — contributesTo and mapsTo are mutually exclusive."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["contributesTo"] and alpha["mapsTo"]:
            findings.append(_finding(
                "semantic-002", "error",
                f"Alpha '{alpha['name']}' has both contributesTo ('{alpha['contributesTo']}') "
                f"and mapsTo ('{alpha['mapsTo']}') — must be one or the other",
            ))
    return findings


def check_mapsto_naming(extracted, baseline=None):
    """@rule:semantic-010 — mapsTo variant names must not repeat parent type name."""
    findings = []
    all_alpha_names = {a["name"] for a in extracted["alphas"]}
    baseline_names = set()
    if baseline:
        baseline_names = {a["name"] for a in baseline.get("alphas", [])}

    for alpha in extracted["alphas"]:
        if not alpha["mapsTo"]:
            continue
        parent_name = alpha["mapsTo"]
        if parent_name.lower() in alpha["name"].lower():
            findings.append(_finding(
                "semantic-010", "warning",
                f"mapsTo variant '{alpha['name']}' contains parent type name '{parent_name}' — "
                f"mapsTo reads as 'is a type of', so redundant",
            ))
    return findings


def check_relatesto_present(extracted):
    """@rule:semantic-004 — New alphas should have relatesTo relationships."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["type"].startswith("Redeclaration"):
            continue
        if not alpha["relatesTo"]:
            findings.append(_finding(
                "semantic-004", "warning",
                f"Alpha '{alpha['name']}' has no relatesTo relationships",
            ))
    return findings


def check_alias_isolation(extracted):
    """@rule:aliasing-002 — Alias names must not appear in structural references."""
    findings = []
    alias_names = {a["aliasName"] for a in extracted["aliases"]}
    if not alias_names:
        return findings

    for alpha in extracted["alphas"]:
        for field in ("contributesTo", "mapsTo"):
            val = alpha.get(field)
            if val and val in alias_names:
                findings.append(_finding(
                    "aliasing-002", "warning",
                    f"Alpha '{alpha['name']}' uses alias name '{val}' in {field} — "
                    f"use canonical baseline name instead",
                ))
        for rt in alpha["relatesTo"]:
            if rt in alias_names:
                findings.append(_finding(
                    "aliasing-002", "warning",
                    f"Alpha '{alpha['name']}' uses alias name '{rt}' in relatesTo",
                ))

    for activity in extracted["activities"]:
        if activity["activitySpaceName"] and activity["activitySpaceName"] in alias_names:
            findings.append(_finding(
                "aliasing-002", "warning",
                f"Activity '{activity['name']}' uses alias name "
                f"'{activity['activitySpaceName']}' in activitySpaceName",
            ))
        for ct_alpha in activity["contributesToAlphas"]:
            if ct_alpha in alias_names:
                findings.append(_finding(
                    "aliasing-002", "warning",
                    f"Activity '{activity['name']}' uses alias name "
                    f"'{ct_alpha}' in contributesTo",
                ))

    return findings


def check_alias_uniqueness(extracted):
    """@rule:aliasing-001 — Max one alias per element."""
    findings = []
    seen = {}
    for alias in extracted["aliases"]:
        key = (alias["canonicalName"], alias["elementType"])
        if key in seen:
            findings.append(_finding(
                "aliasing-001", "warning",
                f"Multiple aliases for {alias['elementType']} '{alias['canonicalName']}': "
                f"'{seen[key]}' and '{alias['aliasName']}'",
            ))
        else:
            seen[key] = alias["aliasName"]
    return findings


def check_state_minimum(extracted):
    """@rule:coverage-001 — Each new alpha needs >= 3 states."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["type"].startswith("Redeclaration"):
            continue
        if alpha["stateCount"] < 3:
            findings.append(_finding(
                "coverage-001", "error",
                f"Alpha '{alpha['name']}' has {alpha['stateCount']} states (minimum 3)",
            ))
    return findings


def check_primary_alpha(extracted):
    """Delineation requires a primary alpha to be documented."""
    findings = []
    delin = extracted["delineation"]
    if not delin.get("primaryAlpha"):
        findings.append(_finding(
            "process-001", "warning",
            "No primary alpha documented in delineation analysis",
        ))
    return findings


def check_keyword_count(extracted):
    """@rule:aliasing-003 — 10-20 keywords per practice."""
    findings = []
    count = len(extracted["keywords"])
    if count < 10:
        findings.append(_finding(
            "aliasing-003", "warning",
            f"Only {count} keywords (expected 10-20)",
        ))
    elif count > 20:
        findings.append(_finding(
            "aliasing-003", "warning",
            f"{count} keywords (expected 10-20)",
        ))
    return findings


def check_competency_levels(extracted, baseline=None):
    """@rule:semantic-006 — Competency level names must match baseline."""
    findings = []
    if not baseline:
        return findings

    baseline_levels = set()
    for comp in baseline.get("competencies", []):
        for level in comp.get("competencyLevels", []):
            baseline_levels.add(level.get("name", ""))

    if not baseline_levels:
        return findings

    for level in extracted["competencyRefs"]["levels"]:
        if level not in baseline_levels:
            findings.append(_finding(
                "semantic-006", "error",
                f"Competency level '{level}' not found in baseline "
                f"(valid: {', '.join(sorted(baseline_levels))})",
            ))
    return findings


def check_competency_names(extracted, baseline=None):
    """@rule:semantic-011 — Competency names should resolve to baseline."""
    findings = []
    if not baseline:
        return findings

    baseline_comps = {c.get("name", "") for c in baseline.get("competencies", [])}
    if not baseline_comps:
        return findings

    for name in extracted["competencyRefs"]["names"]:
        if name and name not in baseline_comps:
            findings.append(_finding(
                "semantic-011", "warning",
                f"Competency '{name}' not found in baseline",
            ))
    return findings


def check_activity_space_names(extracted, baseline=None):
    """@rule:naming-005 — Activity names must differ from ActivitySpace names."""
    findings = []
    baseline_spaces = set()
    if baseline:
        baseline_spaces = {a.get("name", "") for a in baseline.get("activitySpaces", [])}

    for activity in extracted["activities"]:
        if activity["activitySpaceName"] and activity["name"] == activity["activitySpaceName"]:
            findings.append(_finding(
                "naming-005", "error",
                f"Activity '{activity['name']}' has same name as its ActivitySpace",
            ))

        if baseline and activity["activitySpaceName"]:
            if activity["activitySpaceName"] not in baseline_spaces:
                findings.append(_finding(
                    "semantic-011", "warning",
                    f"ActivitySpace '{activity['activitySpaceName']}' not found in baseline",
                ))

    return findings


def check_contributes_to_targets(extracted, baseline=None):
    """Check that contributesTo/mapsTo targets resolve to known alphas."""
    findings = []
    local_names = {a["name"] for a in extracted["alphas"]}
    baseline_names = set()
    if baseline:
        baseline_names = {a.get("name", "") for a in baseline.get("alphas", [])}

    all_known = local_names | baseline_names

    for alpha in extracted["alphas"]:
        target = alpha["contributesTo"] or alpha["mapsTo"]
        if target and target not in all_known:
            findings.append(_finding(
                "semantic-011", "error",
                f"Alpha '{alpha['name']}' references unknown target '{target}' "
                f"in {'contributesTo' if alpha['contributesTo'] else 'mapsTo'}",
            ))
    return findings


def check_relatesto_direction(extracted):
    """@rule:semantic-012 — relatesTo entries must include direction field."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["type"].startswith("Redeclaration"):
            continue
        for rt_name in alpha["relatesTo"]:
            if not alpha.get("relatesTo_directions"):
                findings.append(_finding(
                    "semantic-012", "warning",
                    f"Alpha '{alpha['name']}' relatesTo entries may be missing "
                    f"required 'direction' field (outgoing|incoming|mutual)",
                ))
                break
    return findings


def check_description_length(extracted):
    """@rule:naming-001 — Descriptions should be single sentences, max 20 words."""
    findings = []
    for alpha in extracted["alphas"]:
        if alpha["type"].startswith("Redeclaration"):
            continue
        desc = alpha.get("description", "")
        if desc:
            word_count = len(desc.split())
            if word_count > 25:
                findings.append(_finding(
                    "naming-001", "warning",
                    f"Alpha '{alpha['name']}' description is {word_count} words (guideline: max 20)",
                ))
    return findings


def verify_mapping(extracted, baseline=None, kind="practice"):
    """Run all checks and return findings.

    kind: "practice" for extension practices, "baseline" for baseline practices.
    Baseline mapping guides skip checks that only apply to extensions.
    """
    findings = []

    if kind == "practice":
        findings.extend(check_no_floating_alphas(extracted))
        findings.extend(check_contributes_to_targets(extracted, baseline))
        findings.extend(check_mapsto_naming(extracted, baseline))
        findings.extend(check_primary_alpha(extracted))
        findings.extend(check_competency_levels(extracted, baseline))
        findings.extend(check_competency_names(extracted, baseline))
        findings.extend(check_activity_space_names(extracted, baseline))

    findings.extend(check_mutual_exclusivity(extracted))
    findings.extend(check_relatesto_present(extracted))
    findings.extend(check_relatesto_direction(extracted))
    findings.extend(check_alias_isolation(extracted))
    findings.extend(check_alias_uniqueness(extracted))
    findings.extend(check_state_minimum(extracted))
    findings.extend(check_keyword_count(extracted))
    findings.extend(check_description_length(extracted))
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Verify Phase 2 mapping guide against specs before JSON generation"
    )
    parser.add_argument("mapping_guide", help="Path to 02-mapping-guide.md")
    parser.add_argument("--baseline", help="Baseline practice JSON for reference checking")
    parser.add_argument("--parent", action="append", default=[],
                        help="Parent practice JSON(s) for cross-practice reference resolution")
    parser.add_argument("--specs", help="specs-index.json for rule annotation")
    parser.add_argument("--kind", choices=["practice", "baseline"], default="practice",
                        help="Kind of mapping guide (default: practice)")
    parser.add_argument("--summary", action="store_true", help="Compact output")
    args = parser.parse_args()

    mapping_path = Path(args.mapping_guide)
    if not mapping_path.exists():
        print(json.dumps({"error": f"File not found: {mapping_path}"}))
        sys.exit(1)

    text = mapping_path.read_text(encoding="utf-8")
    extracted = extract_mapping_data(text)

    baseline = None
    if args.baseline:
        baseline = load_json(args.baseline, exit_on_error=False)

    if args.parent and baseline:
        for parent_path in args.parent:
            parent = load_json(parent_path, exit_on_error=False)
            if parent:
                for alpha in parent.get("alphas", []):
                    baseline.setdefault("alphas", []).append(alpha)

    findings = verify_mapping(extracted, baseline, kind=args.kind)

    specs_rules = set()
    if args.specs:
        specs_data = load_json(args.specs, exit_on_error=False)
        if specs_data:
            specs_rules = {s["id"] for s in specs_data.get("scenarios", [])}
            for f in findings:
                if f["rule"] in specs_rules:
                    f["specMatched"] = True

    error_count = sum(1 for f in findings if f["severity"] == "error")
    warning_count = sum(1 for f in findings if f["severity"] == "warning")

    report = {
        "file": str(mapping_path),
        "extracted": {
            "alphaCount": len(extracted["alphas"]),
            "newAlphas": [a["name"] for a in extracted["alphas"]
                         if not a["type"].startswith("Redeclaration")],
            "redeclaredAlphas": [a["name"] for a in extracted["alphas"]
                                if a["type"].startswith("Redeclaration")],
            "aliasCount": len(extracted["aliases"]),
            "activityCount": len(extracted["activities"]),
            "keywordCount": len(extracted["keywords"]),
            "delineation": extracted["delineation"],
        },
        "findings": findings,
        "summary": {
            "total": len(findings),
            "errors": error_count,
            "warnings": warning_count,
            "rules_checked": sorted({f["rule"] for f in findings}),
        },
    }

    if args.summary:
        del report["findings"]
        report["findingSummary"] = {}
        from collections import Counter
        for sev in ("error", "warning"):
            cats = Counter(f["rule"] for f in findings if f["severity"] == sev)
            if cats:
                report["findingSummary"][sev] = dict(cats.most_common())

    print(json.dumps(report, indent=2))
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
