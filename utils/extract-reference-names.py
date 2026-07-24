#!/usr/bin/env python3
"""
Extract reference names and structural details from baseline, practice, or method JSON.

Replaces ad hoc `python3 -c` scripts that agents use to inspect JSON structure.
Provides consistent, approved output for Phase 3 agents.

Usage:
    # Extract all reference names from a baseline
    python3 utils/extract-reference-names.py baseline.json

    # Extract specific sections
    python3 utils/extract-reference-names.py baseline.json --sections focuses alphas competencies

    # Show detailed alpha info (states, checklists, relatesTo)
    python3 utils/extract-reference-names.py baseline.json --alpha-details

    # Show detailed alpha info for specific alphas only
    python3 utils/extract-reference-names.py baseline.json --alpha-details --alpha-names "Digital Strategy" "Business Model"

    # Show narrative type structure
    python3 utils/extract-reference-names.py baseline.json --narrative-details

    # Get full JSON definitions for specific narrative types
    python3 utils/extract-reference-names.py baseline.json --sections narrativeTypes --narrative-type-names "STAR" "Technique"

    # Find all references to a named element
    python3 utils/extract-reference-names.py practice.json --find-refs "Platform"

    # List narrative contexts by element name
    python3 utils/extract-reference-names.py practice.json --narrative-contexts

    # Show all "Common Pitfalls" contexts
    python3 utils/extract-reference-names.py practice.json --context-element "Common Pitfalls"

    # Show contexts exceeding 3 sentences
    python3 utils/extract-reference-names.py practice.json --long-contexts

    # Show activity structure
    python3 utils/extract-reference-names.py practice.json --activity-details

    # Show citation names
    python3 utils/extract-reference-names.py practice.json --sections citations

    # Show full citation metadata (description, source, url)
    python3 utils/extract-reference-names.py practice.json --sections citations --citation-details

    # Show asset names and types
    python3 utils/extract-reference-names.py practice.json --sections assets

    # Dump raw JSON of first element from a section (template reference)
    python3 utils/extract-reference-names.py practice.json --sample activities

    # JSON output for programmatic use
    python3 utils/extract-reference-names.py baseline.json --json

    # Inspect a method (iterates practices)
    python3 utils/extract-reference-names.py method.json --sections practices
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


VALID_SECTIONS = [
    "summary", "structure", "focuses", "alphas", "activitySpaces", "competencies",
    "narrativeTypes", "narratives", "citations", "assets", "activities",
    "workProducts", "personas", "personaGroups", "patterns", "aliases",
    "practices",
]


def print_structure(data):
    """Print top-level key overview: type and count/length for each key."""
    print("=== STRUCTURE ===")
    for k, v in data.items():
        if isinstance(v, list):
            print(f"  {k}: list[{len(v)}]")
        elif isinstance(v, dict):
            sub_keys = list(v.keys())[:5]
            suffix = "..." if len(v) > 5 else ""
            print(f"  {k}: dict ({len(v)} keys: {sub_keys}{suffix})")
        elif isinstance(v, str):
            print(f"  {k}: str = {repr(v)[:80]}")
        elif isinstance(v, bool):
            print(f"  {k}: bool = {v}")
        elif isinstance(v, (int, float)):
            print(f"  {k}: {type(v).__name__} = {v}")
        elif v is None:
            print(f"  {k}: null")
        else:
            print(f"  {k}: {type(v).__name__}")


def print_summary(data):
    print(f"=== SUMMARY ===")
    print(f"  kind: {data.get('kind', 'N/A')}")
    print(f"  name: {data.get('name', 'N/A')}")
    print(f"  baselinePracticeName: {data.get('baselinePracticeName', 'N/A')}")
    if data.get("practiceDependencyNames"):
        print(f"  practiceDependencyNames: {data['practiceDependencyNames']}")
    tags = data.get("tags", {})
    if tags:
        for tag_type in ["domainTags", "lifecycleTags", "organizationalTags"]:
            if tags.get(tag_type):
                print(f"  {tag_type}: {tags[tag_type]}")
    counts = {
        "alphas": len(data.get("alphas", [])),
        "activities": len(data.get("activities", [])),
        "workProducts": len(data.get("workProducts", [])),
        "patterns": len(data.get("patterns", [])),
        "citations": len(data.get("citations", [])),
        "assets": len(data.get("assets", [])),
        "personas": len(data.get("personas", [])),
        "personaGroups": len(data.get("personaGroups", [])),
        "narrativeTypes": len(data.get("narrativeTypes", [])),
        "practiceElementAliases": len(data.get("practiceElementAliases", [])),
    }
    if data.get("practices"):
        counts["practices"] = len(data["practices"])
    print(f"  counts: {counts}")


def print_focuses(data):
    focuses = data.get("focuses", [])
    if not focuses:
        print("=== FOCUSES === (none defined)")
        return
    print("=== FOCUSES ===")
    for f in focuses:
        print(f"  {f['name']}")


def _print_alpha_list(alphas, detail=False, alpha_names=None, indent="  "):
    for a in alphas:
        name = a["name"]
        if alpha_names and name not in alpha_names:
            continue
        focus = a.get("focusName", "N/A")
        contrib = a.get("contributesTo", None)
        relates = a.get("relatesTo", [])
        states = a.get("states", [])

        line = f"{indent}{name} (focus: {focus}"
        if contrib:
            line += f", contributesTo: {contrib}"
        line += ")"
        print(line)

        if detail and a.get("description"):
            print(f"{indent}  description: {a['description']}")

        if relates:
            print(f"{indent}  relatesTo: {relates}")

        for s in states:
            if detail:
                desc = s.get("description", "")
                checklists = s.get("checklists", [])
                cl_names = [c["name"] if isinstance(c, dict) else c for c in checklists]
                desc_suffix = f" - {desc}" if desc else ""
                print(f"{indent}  State {s.get('seq', '?')}: {s['name']}{desc_suffix} ({len(checklists)} checklists)")
                for cn in cl_names:
                    print(f"{indent}    - {cn}")
            else:
                print(f"{indent}  State {s.get('seq', '?')}: {s['name']}")


def print_alphas(data, detail=False, alpha_names=None):
    alphas = data.get("alphas", [])
    practices = data.get("practices", [])

    if not alphas and not practices:
        print("=== ALPHAS === (none)")
        return

    if alphas:
        print(f"=== ALPHAS ({len(alphas)}) ===")
        _print_alpha_list(alphas, detail, alpha_names)

    if practices:
        for p in practices:
            p_alphas = p.get("alphas", [])
            if not p_alphas:
                continue
            print(f"=== ALPHAS in {p.get('name', 'unknown')} ({len(p_alphas)}) ===")
            _print_alpha_list(p_alphas, detail, alpha_names)

    if not alphas and not any(p.get("alphas") for p in practices):
        print("=== ALPHAS === (none)")


def print_activity_spaces(data):
    spaces = data.get("activitySpaces", [])
    if not spaces:
        print("=== ACTIVITY SPACES === (none defined)")
        return
    print(f"=== ACTIVITY SPACES ({len(spaces)}) ===")
    for a in spaces:
        focus = a.get("focusName", "N/A")
        contrib = a.get("contributesTo", [])
        print(f"  {a['name']} (focus: {focus})")
        if contrib:
            for c in contrib:
                print(f"    contributesTo: {c.get('alphaName', '?')} -> {c.get('stateName', '?')}")


def print_competencies(data):
    comps = data.get("competencies", [])
    if not comps:
        print("=== COMPETENCIES === (none defined)")
        return
    print(f"=== COMPETENCIES ({len(comps)}) ===")
    for c in comps:
        levels = [l["name"] for l in c.get("levels", [])]
        print(f"  {c['name']}")
        print(f"    Levels: {levels}")


def print_narrative_types(data, detail=False, names=None):
    nts = data.get("narrativeTypes", [])
    if not nts:
        print("=== NARRATIVE TYPES === (none defined)")
        return

    if names:
        matched = [nt for nt in nts if nt["name"] in names]
        print(f"=== NARRATIVE TYPES ({len(matched)}/{len(nts)} matched) ===")
        for nt in matched:
            print(json.dumps(nt, indent=2))
            print("---")
        missing = set(names) - {nt["name"] for nt in matched}
        if missing:
            print(f"  NOT FOUND: {sorted(missing)}")
        return

    print(f"=== NARRATIVE TYPES ({len(nts)}) ===")
    for nt in nts:
        print(f"  {nt['name']}")
        if detail or True:
            for ne in nt.get("narrativeElements", []):
                print(f"    Element: {ne['name']}")
                if detail:
                    print(f"      howToUse: {ne.get('howToUse', 'N/A')[:100]}")


def print_narratives(data):
    narrs = data.get("narratives", [])
    if not narrs:
        print("=== NARRATIVES === (none at top level)")
        return
    print(f"=== NARRATIVES ({len(narrs)}) ===")
    for n in narrs:
        nt = n.get("narrativeTypeName", "?")
        cn = n.get("citationNames", [])
        print(f"  \"{n.get('name', '?')}\" (type: {nt})")
        if cn:
            print(f"    citationNames: {cn}")
        else:
            print(f"    citationNames: NONE")


def _format_narrative_line(element_type, element_name, narrative,
                           sub_element=None, show_content=False):
    n_name = narrative.get("name", "?")
    nt = narrative.get("narrativeTypeName", "?")
    cn = narrative.get("citationNames", [])
    prefix = f'{element_type} "{element_name}"'
    if sub_element:
        prefix += f' > {sub_element}'
    cn_str = f"citationNames: {cn}" if cn else "citationNames: NONE"
    lines = [f'  {prefix}', f'    narrative "{n_name}" (type: {nt}) {cn_str}']
    if show_content:
        desc = narrative.get("description", "")
        if desc:
            lines.append(f'    desc: {desc[:200]}')
        contexts = narrative.get("narrativeContexts", [])
        if contexts:
            first = next(
                (c for c in contexts if c.get("seq") == 1),
                contexts[0]
            )
            elem_name = first.get("narrativeElementName", "?")
            text = first.get("context", "")
            if text:
                lines.append(f'    {elem_name}: {text[:200]}...')
    return "\n".join(lines)


def _collect_narrative_lines(data, show_content=False):
    lines = []
    for n in data.get("narratives", []):
        lines.append(_format_narrative_line(
            "Practice", data.get("name", "?"), n, show_content=show_content))

    for a in data.get("alphas", []):
        for n in a.get("narratives", []):
            lines.append(_format_narrative_line(
                "Alpha", a["name"], n, show_content=show_content))
        for s in a.get("states", []):
            for n in s.get("narratives", []):
                lines.append(_format_narrative_line(
                    "Alpha", a["name"], n,
                    sub_element=f'State "{s["name"]}"',
                    show_content=show_content))

    for act in data.get("activities", []):
        for n in act.get("narratives", []):
            lines.append(_format_narrative_line(
                "Activity", act["name"], n, show_content=show_content))

    for wp in data.get("workProducts", []):
        for n in wp.get("narratives", []):
            lines.append(_format_narrative_line(
                "WorkProduct", wp["name"], n, show_content=show_content))

    for p in data.get("patterns", []):
        for n in p.get("narratives", []):
            lines.append(_format_narrative_line(
                "Pattern", p["name"], n, show_content=show_content))

    for pg in data.get("personaGroups", []):
        for n in pg.get("narratives", []):
            lines.append(_format_narrative_line(
                "PersonaGroup", pg["name"], n, show_content=show_content))

    return lines


def _collect_all_contexts(data):
    """Collect all narrative contexts from all elements with location info."""
    contexts = []

    def _walk_narrs(narrs, location_prefix):
        for n in narrs:
            n_name = n.get("name", "?")
            for nc in n.get("narrativeContexts", []):
                contexts.append({
                    "location": f"{location_prefix}: {n_name}",
                    "element": nc.get("narrativeElementName", "?"),
                    "context": nc.get("context", ""),
                    "seq": nc.get("seq", 0),
                })

    _walk_narrs(data.get("narratives", []), "practice")

    for a in data.get("alphas", []):
        _walk_narrs(a.get("narratives", []), f"alpha {a['name']}")
        for s in a.get("states", []):
            _walk_narrs(s.get("narratives", []),
                        f"alpha {a['name']} state {s['name']}")

    for act in data.get("activities", []):
        _walk_narrs(act.get("narratives", []), f"activity {act['name']}")

    for wp in data.get("workProducts", []):
        _walk_narrs(wp.get("narratives", []), f"workProduct {wp['name']}")

    for pat in data.get("patterns", []):
        _walk_narrs(pat.get("narratives", []), f"pattern {pat['name']}")

    for pg in data.get("personaGroups", []):
        _walk_narrs(pg.get("narratives", []), f"personaGroup {pg['name']}")

    return contexts


def _count_sentences(text):
    """Count sentences in a text string."""
    import re as _re
    sentences = _re.split(r'(?<=[.!?])\s+', text.strip())
    return len([s for s in sentences if s.strip()])


def print_narrative_contexts(data, element_filter=None, long_only=False,
                             full_text=False):
    """Print narrative contexts, optionally filtered by element name or length."""
    all_ctx = _collect_all_contexts(data)

    for p in data.get("practices", []):
        all_ctx.extend(_collect_all_contexts(p))

    print(f"Total narrative contexts: {len(all_ctx)}")
    print()

    if long_only:
        long_ones = []
        for c in all_ctx:
            sc = _count_sentences(c["context"])
            if sc > 3:
                long_ones.append((c, sc))
        print(f"Contexts exceeding 3 sentences: {len(long_ones)}")
        print()
        for c, sc in sorted(long_ones, key=lambda x: -x[1]):
            print(f"  [{sc} sentences] {c['element']} @ {c['location']}")
            if full_text:
                print(f"    {c['context']}")
            else:
                print(f"    \"{c['context'][:150]}...\"")
            print()
    elif element_filter:
        filtered = [c for c in all_ctx if c["element"] == element_filter]
        print(f"'{element_filter}' contexts: {len(filtered)}")
        print()
        for i, ctx in enumerate(filtered):
            print(f"--- {i + 1} [{ctx['location']}] ---")
            text = ctx["context"]
            if full_text:
                print(text)
            else:
                print(text[:300])
                if len(text) > 300:
                    print("...")
            print()
    else:
        by_element = {}
        for ctx in all_ctx:
            by_element.setdefault(ctx["element"], []).append(ctx)
        for elem, ctxs in sorted(by_element.items()):
            print(f"  {elem}: {len(ctxs)} context(s)")


def print_narrative_placement(data, show_content=False):
    title = "NARRATIVE CONTENT" if show_content else "NARRATIVE PLACEMENT"
    print(f"=== {title} ===")
    lines = _collect_narrative_lines(data, show_content=show_content)

    if not lines:
        print("  (no narratives found on any element)")
    else:
        print(f"  Total: {len(lines)} narrative(s) across all elements")
        print()
        for line in lines:
            print(line)
            print()


def print_citations(data, detail=False):
    cits = data.get("citations", [])
    if not cits:
        print("=== CITATIONS === (none)")
        return
    print(f"=== CITATIONS ({len(cits)}) ===")
    for i, c in enumerate(cits):
        authors = ", ".join(c.get("authors", ["?"])[:2])
        print(f"  [{i}] \"{c['name']}\" - {c.get('date', '?')} - {authors}")
        if detail:
            print(f"       description: {c.get('description', 'N/A')}")
            print(f"       source: {c.get('source', 'N/A')}")
            if c.get("url"):
                print(f"       url: {c['url']}")


def print_assets(data):
    assets = data.get("assets", [])
    if not assets:
        print("=== ASSETS === (none)")
        return
    print(f"=== ASSETS ({len(assets)}) ===")
    for a in assets:
        atype = a.get("type", "?")
        if atype == "font-character":
            char = a.get("fontCharacter", "?")
            print(f"  {a['name']} ({atype}: {char})")
        else:
            path = a.get("path", a.get("url", "?"))
            print(f"  {a['name']} ({atype}: {path})")


def print_activities(data, detail=False):
    acts = data.get("activities", [])
    if not acts:
        print("=== ACTIVITIES === (none)")
        return
    print(f"=== ACTIVITIES ({len(acts)}) ===")
    for a in acts:
        space = a.get("activitySpaceName", "N/A")
        focus = a.get("focusName", "N/A")
        print(f"  {a['name']} (space: {space}, focus: {focus})")
        if detail:
            if a.get("contributesTo"):
                print(f"    contributesTo: {a['contributesTo']}")
            if a.get("worksOn"):
                print(f"    worksOn: {a['worksOn']}")
            if a.get("requiredCompetencies"):
                print(f"    requiredCompetencies: {a['requiredCompetencies']}")
            if a.get("assetNames"):
                print(f"    assetNames: {a['assetNames']}")
            for n in a.get("narratives", []):
                elements = [c.get("narrativeElementName", "?")
                            for c in n.get("narrativeContexts", [])]
                print(f"    narrative: {n.get('narrativeTypeName', '?')} elements={elements}")


def print_work_products(data):
    wps = data.get("workProducts", [])
    if not wps:
        print("=== WORK PRODUCTS === (none)")
        return
    print(f"=== WORK PRODUCTS ({len(wps)}) ===")
    for wp in wps:
        lods = wp.get("levelsOfDetail", [])
        lod_names = [l["name"] for l in lods]
        print(f"  {wp['name']} (LODs: {lod_names})")


def print_personas(data):
    personas = data.get("personas", [])
    if not personas:
        print("=== PERSONAS === (none)")
        return
    print(f"=== PERSONAS ({len(personas)}) ===")
    for p in personas:
        comps = p.get("competencies", [])
        comp_names = [c.get("competencyName", "?") for c in comps]
        print(f"  {p['name']}")
        if comp_names:
            print(f"    competencies: {comp_names}")

    groups = data.get("personaGroups", [])
    if groups:
        print(f"\n=== PERSONA GROUPS ({len(groups)}) ===")
        for g in groups:
            members = g.get("personaNames", [])
            print(f"  {g['name']} ({members})")


def print_patterns(data):
    patterns = data.get("patterns", [])
    if not patterns:
        print("=== PATTERNS === (none)")
        return
    print(f"=== PATTERNS ({len(patterns)}) ===")
    for p in patterns:
        views = p.get("patternViews", [])
        nt = p.get("narrativeTypeName", "N/A")
        print(f"  {p['name']} (narrativeType: {nt}, views: {len(views)})")
        for v in views:
            states = v.get("alphaStates", [])
            alpha_names = [s.get("alphaName", "?") for s in states]
            print(f"    View {v.get('seq', '?')}: {v.get('name', 'N/A')} ({len(states)} alphaStates)")


def print_aliases(data):
    aliases = data.get("practiceElementAliases", [])
    alias_ctx = data.get("_aliasContext", {})
    if not aliases and not alias_ctx:
        print("=== ALIASES === (none)")
        return
    if aliases:
        print(f"=== ALIASES ({len(aliases)}) ===")
        for a in aliases:
            etype = a.get("practiceElementType", a.get("kind", "?"))
            print(f"  {etype}: {a.get('aliasName', '?')} -> {a.get('practiceElementName', '?')}")
    if alias_ctx:
        ctx_aliases = alias_ctx.get("aliases", [])
        print(f"\n=== ALIAS CONTEXT ({len(ctx_aliases)}) ===")
        for a in ctx_aliases:
            atype = a.get("type", a.get("elementType", "?"))
            canonical = a.get("canonicalName", a.get("name", "?"))
            domain = a.get("domainName", a.get("aliasName", "?"))
            print(f"  {atype}: {canonical} -> {domain}")


def print_practices(data):
    practices = data.get("practices", [])
    if not practices:
        print("=== PRACTICES === (not a method)")
        return
    print(f"=== PRACTICES ({len(practices)}) ===")
    for p in practices:
        deps = p.get("practiceDependencyNames", [])
        counts = {
            "alphas": len(p.get("alphas", [])),
            "activities": len(p.get("activities", [])),
            "workProducts": len(p.get("workProducts", [])),
        }
        print(f"  {p['name']} (baseline: {p.get('baselinePracticeName', 'N/A')})")
        print(f"    counts: {counts}")
        if deps:
            print(f"    dependencies: {deps}")


def find_references(data, target_name):
    """Find all references to a named element across the entire JSON."""
    refs = []

    sources = [("", data)]
    for pi, p in enumerate(data.get("practices", [])):
        sources.append((f"practices[{p.get('name', pi)}].", p))

    for pfx, source in sources:
        for a in source.get("alphas", []):
            if a["name"] == target_name:
                refs.append((f"{pfx}alpha.name", a["name"]))
            if a.get("contributesTo") == target_name:
                refs.append((f"{pfx}alpha.contributesTo", a["name"]))
            for r in a.get("relatesTo", []):
                if r.get("alphaName") == target_name:
                    refs.append((f"{pfx}alpha.relatesTo", a["name"]))
            for s in a.get("states", []):
                for cl in s.get("checklist", []):
                    if isinstance(cl, dict) and cl.get("alphaName") == target_name:
                        refs.append((f"{pfx}alpha.state.checklist", f"{a['name']}/{s['name']}"))
                for ev in s.get("evidencedBy", []):
                    if ev.get("workProductName") == target_name:
                        refs.append((f"{pfx}alpha.state.evidencedBy", f"{a['name']}/{s['name']}"))

        for act in source.get("activities", []):
            if act["name"] == target_name:
                refs.append((f"{pfx}activity.name", act["name"]))
            for ct in act.get("contributesTo", []):
                if ct.get("alphaName") == target_name:
                    refs.append((f"{pfx}activity.contributesTo", act["name"]))
            for wo in act.get("worksOn", []):
                if wo.get("workProductName") == target_name:
                    refs.append((f"{pfx}activity.worksOn", act["name"]))

        for wp in source.get("workProducts", []):
            if wp["name"] == target_name:
                refs.append((f"{pfx}workProduct.name", wp["name"]))
            for lod in wp.get("levelsOfDetail", []):
                for ct in lod.get("contributesTo", []):
                    if ct.get("alphaName") == target_name:
                        refs.append((f"{pfx}workProduct.lod.contributesTo",
                                     f"{wp['name']}/{lod['name']}"))

        for pat in source.get("patterns", []):
            if pat["name"] == target_name:
                refs.append((f"{pfx}pattern.name", pat["name"]))
            for pv in pat.get("patternViews", []):
                for als in pv.get("alphaStates", []):
                    if als.get("alphaName") == target_name:
                        refs.append((f"{pfx}pattern.alphaStates",
                                     f"{pat['name']}/{pv.get('name', '?')}"))
                for ev in pv.get("evidenceBy", []):
                    if ev.get("workProductName") == target_name:
                        refs.append((f"{pfx}pattern.evidenceBy",
                                     f"{pat['name']}/{pv.get('name', '?')}"))

        for alias in source.get("practiceElementAliases", []):
            if alias.get("practiceElementName") == target_name:
                refs.append((f"{pfx}alias.target", alias.get("aliasName", "?")))
            if alias.get("aliasName") == target_name:
                refs.append((f"{pfx}alias.aliasName", alias.get("practiceElementName", "?")))

        for pg in source.get("personaGroups", []):
            for pn in pg.get("personaNames", []):
                if pn == target_name:
                    refs.append((f"{pfx}personaGroup.personaNames", pg.get("name", "?")))

    return refs


def collect_json_output(data, sections, alpha_details=False, alpha_names=None,
                        citation_details=False, narrative_type_names=None):
    result = {}
    for section in sections:
        if section == "summary":
            result["summary"] = {
                "kind": data.get("kind"),
                "name": data.get("name"),
                "baselinePracticeName": data.get("baselinePracticeName"),
            }
        elif section == "structure":
            structure = {}
            for k, v in data.items():
                if isinstance(v, list):
                    structure[k] = {"type": "list", "length": len(v)}
                elif isinstance(v, dict):
                    structure[k] = {"type": "dict", "keys": list(v.keys())[:10]}
                else:
                    structure[k] = {"type": type(v).__name__, "value": repr(v)[:80]}
            result["structure"] = structure
        elif section == "focuses":
            result["focuses"] = [f["name"] for f in data.get("focuses", [])]
        elif section == "alphas":
            def _build_alpha_json(alpha_list):
                out = []
                for a in alpha_list:
                    if alpha_names and a["name"] not in alpha_names:
                        continue
                    info = {
                        "name": a["name"],
                        "focusName": a.get("focusName"),
                        "contributesTo": a.get("contributesTo"),
                        "relatesTo": a.get("relatesTo", []),
                        "states": [{"seq": s.get("seq"), "name": s["name"]} for s in a.get("states", [])],
                    }
                    if alpha_details:
                        info["description"] = a.get("description", "")
                        info["states"] = [{
                            "seq": s.get("seq"),
                            "name": s["name"],
                            "description": s.get("description", ""),
                            "checklists": [c["name"] if isinstance(c, dict) else c for c in s.get("checklists", [])]
                        } for s in a.get("states", [])]
                    out.append(info)
                return out

            top_alphas = _build_alpha_json(data.get("alphas", []))
            practices = data.get("practices", [])
            if practices:
                practice_alphas = {}
                for p in practices:
                    p_alphas = _build_alpha_json(p.get("alphas", []))
                    if p_alphas:
                        practice_alphas[p.get("name", "unknown")] = p_alphas
                if top_alphas:
                    result["alphas"] = top_alphas
                if practice_alphas:
                    result["practiceAlphas"] = practice_alphas
                if not top_alphas and not practice_alphas:
                    result["alphas"] = []
            else:
                result["alphas"] = top_alphas
        elif section == "activitySpaces":
            result["activitySpaces"] = [{
                "name": a["name"],
                "focusName": a.get("focusName"),
            } for a in data.get("activitySpaces", [])]
        elif section == "competencies":
            result["competencies"] = [{
                "name": c["name"],
                "levels": [l["name"] for l in c.get("levels", [])],
            } for c in data.get("competencies", [])]
        elif section == "narrativeTypes":
            nts = data.get("narrativeTypes", [])
            if narrative_type_names:
                matched = [nt for nt in nts if nt["name"] in set(narrative_type_names)]
                result["narrativeTypes"] = matched
            else:
                result["narrativeTypes"] = [{
                    "name": nt["name"],
                    "elements": [ne["name"] for ne in nt.get("narrativeElements", [])],
                } for nt in nts]
        elif section == "narratives":
            result["narratives"] = [{
                "name": n.get("name"),
                "narrativeTypeName": n.get("narrativeTypeName"),
                "citationNames": n.get("citationNames", []),
            } for n in data.get("narratives", [])]
        elif section == "citations":
            if citation_details:
                result["citations"] = [{
                    "index": i,
                    "name": c["name"],
                    "description": c.get("description", ""),
                    "authors": c.get("authors", []),
                    "date": c.get("date", ""),
                    "source": c.get("source", ""),
                    "url": c.get("url", ""),
                } for i, c in enumerate(data.get("citations", []))]
            else:
                result["citations"] = [c["name"] for c in data.get("citations", [])]
        elif section == "assets":
            result["assets"] = [a["name"] for a in data.get("assets", [])]
        elif section == "activities":
            result["activities"] = [{
                "name": a["name"],
                "activitySpaceName": a.get("activitySpaceName"),
                "focusName": a.get("focusName"),
            } for a in data.get("activities", [])]
        elif section == "workProducts":
            result["workProducts"] = [{
                "name": wp["name"],
                "lods": [l["name"] for l in wp.get("levelsOfDetail", [])],
            } for wp in data.get("workProducts", [])]
        elif section == "practices":
            result["practices"] = [{
                "name": p["name"],
                "alphaCount": len(p.get("alphas", [])),
                "activityCount": len(p.get("activities", [])),
                "workProductCount": len(p.get("workProducts", [])),
            } for p in data.get("practices", [])]
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract reference names and structure from practice/baseline/method JSON"
    )
    parser.add_argument("json_file", help="Path to JSON file (baseline, practice, or method)")
    parser.add_argument(
        "--sections", nargs="+", choices=VALID_SECTIONS, default=None,
        help=f"Sections to display (default: all). Choices: {', '.join(VALID_SECTIONS)}"
    )
    parser.add_argument("--alpha-details", action="store_true",
                        help="Show detailed alpha info (checklists per state)")
    parser.add_argument("--alpha-names", nargs="+",
                        help="Filter to specific alpha names (use with --alpha-details)")
    parser.add_argument("--narrative-details", action="store_true",
                        help="Show detailed narrative type info")
    parser.add_argument("--narrative-type-names", nargs="+",
                        help="Filter to specific narrative type names (dumps full JSON definitions)")
    parser.add_argument("--activity-details", action="store_true",
                        help="Show detailed activity info (contributesTo, worksOn, competencies)")
    parser.add_argument("--citation-details", action="store_true",
                        help="Show full citation metadata (description, source, url)")
    parser.add_argument("--narrative-placement", action="store_true",
                        help="Show all narratives across all elements with citationNames")
    parser.add_argument("--narrative-content", action="store_true",
                        help="Show all narratives with descriptions and first context snippet")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of human-readable text")
    parser.add_argument("--sample", metavar="SECTION",
                        help="Dump raw JSON of the first element from SECTION (e.g., activities, alphas)")
    parser.add_argument("--find-refs", metavar="NAME",
                        help="Find all references to a named element across the entire JSON")
    parser.add_argument("--narrative-contexts", action="store_true",
                        help="List all narrative contexts with element name counts")
    parser.add_argument("--context-element", metavar="ELEMENT",
                        help="Filter narrative contexts by element name (e.g., 'Common Pitfalls')")
    parser.add_argument("--long-contexts", action="store_true",
                        help="Show narrative contexts exceeding 3 sentences, sorted by length")
    parser.add_argument("--full-text", action="store_true",
                        help="Show full context text (no truncation) with --long-contexts or --context-element")
    parser.add_argument("--structure", action="store_true",
                        help="Show top-level key overview (type and count/length for each key)")

    args = parser.parse_args()
    data = load_json(args.json_file)

    if args.find_refs:
        refs = find_references(data, args.find_refs)
        if args.json:
            print(json.dumps([{"type": t, "context": c} for t, c in refs], indent=2))
        elif refs:
            print(f"=== References to '{args.find_refs}' ({len(refs)}) ===")
            for ref_type, ref_context in refs:
                print(f"  {ref_type}: {ref_context}")
        else:
            print(f"No references to '{args.find_refs}' found.")
        return

    if args.sample:
        section = args.sample
        items = data.get(section, [])
        if not items and data.get("practices"):
            for p in data["practices"]:
                items = p.get(section, [])
                if items:
                    break
        if items:
            print(json.dumps(items[0], indent=2))
        else:
            print(f"No items found in section '{section}'", file=sys.stderr)
            sys.exit(1)
        return

    if args.narrative_contexts or args.context_element or args.long_contexts:
        print_narrative_contexts(data, args.context_element, args.long_contexts,
                                 args.full_text)
        return

    if args.structure:
        sections = args.sections or ["structure"]
        if "structure" not in sections:
            sections = ["structure"] + sections
    else:
        sections = args.sections or ["summary", "focuses", "alphas", "activitySpaces",
                                      "competencies", "narrativeTypes"]

    if args.json:
        result = collect_json_output(data, sections, args.alpha_details, args.alpha_names,
                                     args.citation_details, args.narrative_type_names)
        print(json.dumps(result, indent=2))
        return

    printers = {
        "summary": lambda: print_summary(data),
        "structure": lambda: print_structure(data),
        "focuses": lambda: print_focuses(data),
        "alphas": lambda: print_alphas(data, args.alpha_details, args.alpha_names),
        "activitySpaces": lambda: print_activity_spaces(data),
        "competencies": lambda: print_competencies(data),
        "narrativeTypes": lambda: print_narrative_types(data, args.narrative_details, args.narrative_type_names),
        "narratives": lambda: print_narratives(data),
        "citations": lambda: print_citations(data, args.citation_details),
        "assets": lambda: print_assets(data),
        "activities": lambda: print_activities(data, args.activity_details),
        "workProducts": lambda: print_work_products(data),
        "personas": lambda: print_personas(data),
        "personaGroups": lambda: print_personas(data),
        "patterns": lambda: print_patterns(data),
        "aliases": lambda: print_aliases(data),
        "practices": lambda: print_practices(data),
    }

    for section in sections:
        if section in printers:
            printers[section]()
            print()

    if args.narrative_content:
        print_narrative_placement(data, show_content=True)
        print()
    elif args.narrative_placement:
        print_narrative_placement(data)
        print()


if __name__ == "__main__":
    main()
