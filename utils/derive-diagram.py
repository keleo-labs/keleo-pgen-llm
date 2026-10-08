#!/usr/bin/env python3
"""Derive diagram specs from the semantic graph a practice already carries.

A resolved effective context is a graph nobody draws. Alphas carry `relatesTo`
edges labelled with domain verbs ("governed by", "mitigates", "enables access
to"); `contributesTo` and `mapsTo` form a specialisation tree; a pattern's
`patternViews` are an ordered phase model with alpha/state targets per phase;
work products declare the concerns they serve. Hand-transcribing any of that
into a diagram spec is slow and gets names wrong.

This emits the spec. It never renders — `render-diagram.py` does that, and the
spec is the artifact worth keeping, because it is what lets a diagram be
corrected later without redrawing it.

Specs carry content and structure only. Colour, type and spacing belong to the
engine's THEME, never to a spec.

Start with --list, which reports what this context can yield: the focuses, the
alphas ranked by relationship count, the patterns and their phase sequence, and
the work products. Then derive a view and edit it — a derived spec is a
starting point, not an output.

Usage:
    python3 utils/derive-diagram.py <context>.json --list
    python3 utils/derive-diagram.py <context>.json --view concern-hub \\
        --seed "VM Resilience" --out-dir reports/<slug>/assets/ --name resilience
    python3 utils/derive-diagram.py <context>.json --view journey \\
        --pattern "Platform Bootstrap Journey" --stdout
    python3 utils/derive-diagram.py --help          # the view list

Then render them all in one call:
    python3 utils/render-diagram.py --dir reports/<slug>/assets/
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json  # noqa: E402

# The engine's own guidance: below three a diagram is worse than prose, above
# nine it is a hairball. Scoping flags exist to get under this, not to raise it.
DEFAULT_MAX_NODES = 9

VIEWS = {
    "concern-map": "flow — alphas and their relatesTo verbs, grouped by focus",
    "concern-hub": "hub — one seed alpha surrounded by what it relates to",
    "capability-tree": "flow — contributesTo / mapsTo specialisation rollup",
    "journey": "timeline — one pattern's views in sequence",
    "maturity": "stack — one alpha's states, most mature on top",
    "evidence-map": "flow — work products and the concerns they serve",
    "pattern-matrix": "matrix — alphas by pattern view, cell is the target state",
    "outcome-chain": "flow — what evidences an outcome, and where it counts",
    "role-map": "flow — persona groups and the roles within them",
    "competency-matrix": "matrix — competencies by level, cell is the rubric",
}


# --------------------------------------------------------------------------
# Reading the context
# --------------------------------------------------------------------------

def slug(text, taken=None):
    """A stable node id from an element name."""
    base = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "n"
    if taken is None:
        return base
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}-{n}", n + 1
    taken.add(candidate)
    return candidate


def flatten_alphas(data):
    """Every alpha in the document, including merged variants and supporters.

    A resolved context usually has them flat, but a practice read directly can
    nest specialisations under their parent.
    """
    out, seen = [], set()

    def walk(alpha):
        name = alpha.get("name")
        if not name or name in seen:
            return
        seen.add(name)
        out.append(alpha)
        for nested in alpha.get("supportingAlphas", []) + alpha.get("variants", []):
            walk(nested)

    for alpha in data.get("alphas", []) or []:
        walk(alpha)
    return out


def alpha_states(view):
    """A pattern view's alpha/state targets as (alpha, state) pairs.

    Canonical form is an AlphaContribution object; legacy interchange is a
    string token, "Alpha→State" or "Alpha->State".
    """
    pairs = []
    for entry in view.get("alphaStates", []) or []:
        if isinstance(entry, dict):
            if entry.get("alphaName"):
                pairs.append((entry["alphaName"], entry.get("stateName", "")))
        elif isinstance(entry, str):
            parts = re.split(r"→|->", entry, maxsplit=1)
            pairs.append((parts[0].strip(),
                          parts[1].strip() if len(parts) > 1 else ""))
    return pairs


def find_by_name(items, name, what):
    """Exact match first, then unique case-insensitive, else a helpful exit."""
    for item in items:
        if item.get("name") == name:
            return item
    lowered = [i for i in items if str(i.get("name", "")).lower() == name.lower()]
    if len(lowered) == 1:
        return lowered[0]
    partial = [i for i in items if name.lower() in str(i.get("name", "")).lower()]
    if len(partial) == 1:
        return partial[0]
    die(f"no {what} named {name!r}.",
        hint="Candidates: " + ", ".join(sorted(
            str(i.get("name")) for i in (partial or items))[:12]))


def die(message, hint=None, code=1):
    print(f"Error: {message}", file=sys.stderr)
    if hint:
        print(hint, file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------
# The relationship graph
# --------------------------------------------------------------------------

def build_edges(alphas):
    """Canonical edge list from every alpha's relatesTo array.

    A relationship verb is phrased from the alpha that declares it, so it
    always reads as a sentence along declaring → target: "Platform governed by
    Platform Governance", "VM Data Protection produces Virtual Machine
    Workload". Every edge therefore runs declaring → target with the verb
    verbatim, and never gets inverted — verbs cannot be inverted mechanically,
    and an inverted one reads as nonsense on the page.

    `direction` is used to choose between phrasings rather than to orient the
    line. One pair of alphas usually declares the relationship twice, once
    from each side — Platform says "governed by" (incoming), Platform
    Governance says "governs" (outgoing). Both read correctly, but only the
    active one also puts the arrow head on the thing being acted upon, so the
    outgoing phrasing wins and the other is dropped. Where only a passive
    phrasing exists the sentence still reads correctly and the arrow head
    merely overstates; the spec is editable, which is where that gets fixed.

    `relationshipKind` would carry the actor unambiguously, but no real
    document sets it, so direction plus the verb is all there is to work with.
    """
    rank_of = {"outgoing": 3, "mutual": 2, "incoming": 1}
    best = {}
    for alpha in alphas:
        source = alpha.get("name")
        for rel in alpha.get("relatesTo", []) or []:
            target, verb = rel.get("alphaName"), rel.get("relationship", "")
            if not target or target == source:
                continue
            direction = rel.get("direction", "outgoing")
            edge = {"from": source, "to": target, "label": verb}
            if direction == "mutual":
                edge["arrow"] = "none"
            pair = frozenset((source, target))
            rank = rank_of.get(direction, 3)
            # Higher rank wins; ties break on source name so runs are stable.
            if pair not in best or (rank, source) > best[pair][0]:
                best[pair] = ((rank, source), edge)
    return [edge for _, edge in sorted(best.values(), key=lambda v: v[0][1])]


def neighbourhood(names, edges, seeds, depth):
    """Alpha names within `depth` hops of any seed, over the undirected graph."""
    adjacency = defaultdict(set)
    for edge in edges:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    reached, queue = set(seeds), deque((s, 0) for s in seeds)
    while queue:
        node, hops = queue.popleft()
        if hops >= depth:
            continue
        for peer in adjacency[node]:
            if peer not in reached and peer in names:
                reached.add(peer)
                queue.append((peer, hops + 1))
    return reached


def degree_ranking(alphas, edges):
    """Alpha names by relationship count — the best seeds, busiest first."""
    counts = Counter()
    for edge in edges:
        counts[edge["from"]] += 1
        counts[edge["to"]] += 1
    return sorted(((counts.get(a["name"], 0), a["name"]) for a in alphas),
                  key=lambda row: (-row[0], row[1]))


def scope_alphas(alphas, edges, args):
    """Apply --focus, --practice, --seed/--depth in that order."""
    pool = alphas
    if args.focus:
        wanted = {f.lower() for f in args.focus}
        pool = [a for a in pool if str(a.get("focusName", "")).lower() in wanted]
        if not pool:
            die(f"no alphas in focus(es) {', '.join(args.focus)}.",
                hint="Available: " + ", ".join(sorted(
                    {str(a.get("focusName")) for a in alphas})))
    if args.practice:
        wanted = {p.lower() for p in args.practice}
        pool = [a for a in pool
                if str(a.get("_contributingPracticeName", "")).lower() in wanted]
        if not pool:
            die(f"no alphas contributed by {', '.join(args.practice)}.",
                hint="Available: " + ", ".join(sorted(
                    {str(a.get("_contributingPracticeName")) for a in alphas
                     if a.get("_contributingPracticeName")})))
    if args.seed:
        names = {a["name"] for a in pool}
        seeds = [find_by_name(alphas, s, "alpha")["name"] for s in args.seed]
        names |= set(seeds)
        keep = neighbourhood(names, edges, seeds, args.depth)
        pool = [a for a in alphas if a["name"] in keep]
    return pool


def instance_delta(args):
    """Extra nodes --instance will add, so the budget counts the real total."""
    return sum(len(names) - 1 for names in args.instance.values())


# Measured against this repository's contexts. A focus-scoped concern map runs
# about 0.9 edges per node and lays out cleanly; a seeded neighbourhood runs
# about 1.2 and is legible but tall; a practice-scoped slice of a virtualisation
# stack runs 2.4, and at that ratio the layered layout collapses the graph into
# a single spine and silently drops most of the edges — a wrong diagram, not
# merely a crowded one.
DENSITY_WARN = 1.3
DENSITY_STOP = 1.8


def check_density(nodes, edges, allow_dense):
    """A flow layout tangles, then fails, well before it runs out of nodes.

    The node budget assumes something pipeline-shaped. A relationship graph is
    cyclic and densely connected, so the ratio is what matters: edge labels
    crowd first, and past that the ranking strings everything into one column
    and the edges stop being drawn where they belong.
    """
    if len(nodes) < 4:
        return
    ratio = len(edges) / len(nodes)
    shape = f"{len(edges)} edges across {len(nodes)} nodes"
    if ratio > DENSITY_STOP and not allow_dense:
        die(f"{shape} is too dense for a layered flow — it will collapse into "
            f"a single column and most of those edges will not be drawn where "
            f"they belong.",
            hint="Use --view concern-hub, which draws a star as a star; "
                 "narrow --focus/--practice or --depth; or pass --allow-dense "
                 "if you intend to rewrite the spec by hand.")
    if ratio > DENSITY_WARN:
        print(f"Note: {shape} is dense for a flow layout, and the edge labels "
              f"will crowd. Consider --view concern-hub, a tighter "
              f"--focus/--practice, or --no-edge-labels.", file=sys.stderr)
        return
    # Overall density is not the only way labels collide. Several edges meeting
    # at one node run between the same pair of ranks, and their labels sit side
    # by side on one line with nothing to separate them. Two is a nudge the
    # raster check will catch; three reliably overlaps.
    fan = Counter(end for e in edges if e.get("label")
                  for end in (e["from"], e["to"]))
    if fan and max(fan.values()) >= 3:
        node, count = fan.most_common(1)[0]
        label = next((n["label"] for n in nodes if n["id"] == node), node)
        print(f"Note: {count} labelled edges meet at {label!r}, so those "
              f"labels will overlap. Drop them with --no-edge-labels, or "
              f"narrow the scope.", file=sys.stderr)


def enforce_budget(count, limit, alphas, edges, what="node", hint=None):
    if count <= limit:
        return
    if hint is None:
        ranked = degree_ranking(alphas, edges)[:15]
        hint = ("Busiest alphas (best seeds):\n"
                + "\n".join(f"  {deg:>3} edges  {name}"
                            for deg, name in ranked))
    die(f"{count} {what}s exceeds the {limit}-{what} budget — that is a "
        f"hairball, not a diagram.",
        hint="Scope it with --seed/--depth, --focus or --practice, or raise "
             f"--max-nodes deliberately.\n{hint}")


def expand_instances(nodes, edges, mapping):
    """Split a node into several named instances, each inheriting its edges.

    A practice names Platform once; a deployment with disaster recovery has two
    of them. The instance nodes come out of here; the edge *between* them —
    "replicates to", "fails over to" — is not in the practice, so an author
    adds it to the emitted spec by hand.
    """
    by_id = {n["id"]: n for n in nodes}
    label_to_id = {n["label"]: n["id"] for n in nodes}
    for target, instance_names in mapping.items():
        node_id = target if target in by_id else label_to_id.get(target)
        if not node_id:
            die(f"--instance target {target!r} is not in this diagram.",
                hint="In scope: " + ", ".join(sorted(label_to_id)))
        original = by_id[node_id]
        taken = {n["id"] for n in nodes}
        replacements = []
        for instance in instance_names:
            clone = dict(original)
            clone["id"] = slug(instance, taken)
            clone["label"] = instance
            clone["sublabel"] = original["label"]
            replacements.append(clone)
        index = nodes.index(original)
        nodes[index:index + 1] = replacements
        fanned = []
        for edge in edges:
            if node_id not in (edge["from"], edge["to"]):
                fanned.append(edge)
                continue
            for clone in replacements:
                copy = dict(edge)
                if copy["from"] == node_id:
                    copy["from"] = clone["id"]
                if copy["to"] == node_id:
                    copy["to"] = clone["id"]
                fanned.append(copy)
        edges[:] = fanned
        by_id = {n["id"]: n for n in nodes}
        label_to_id = {n["label"]: n["id"] for n in nodes}
    return nodes, edges


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------

def trim(text, limit=70):
    """A description shortened to a sublabel, or nothing if it will not fit."""
    if not text:
        return None
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return f"{cut}…" if len(cut) > 20 else None


def view_concern_map(data, alphas, all_edges, args):
    if len(args.seed or []) == 1:
        # A seeded neighbourhood is a star, and relationship graphs are often
        # cyclic, so ranking strings it into a tall chain. The hub layout draws
        # the same information as a star, which is what it actually is.
        print(f"Note: for one concern in context, --view concern-hub usually "
              f"reads better than a seeded concern-map.", file=sys.stderr)
    scoped = scope_alphas(alphas, all_edges, args)
    enforce_budget(len(scoped) + instance_delta(args), args.max_nodes,
                   alphas, all_edges)
    names = {a["name"] for a in scoped}
    seeds = {find_by_name(alphas, s, "alpha")["name"] for s in args.seed or []}

    taken, ids, nodes = set(), {}, []
    focuses = []
    for alpha in scoped:
        node_id = slug(alpha["name"], taken)
        ids[alpha["name"]] = node_id
        node = {"id": node_id, "label": alpha["name"]}
        if args.sublabels:
            sub = trim(alpha.get("description"))
            if sub:
                node["sublabel"] = sub
        focus = alpha.get("focusName")
        if focus:
            node["group"] = slug(focus)
            if focus not in focuses:
                focuses.append(focus)
        if alpha["name"] in seeds:
            node["emphasis"] = "accent"
        nodes.append(node)

    edges = []
    for edge in all_edges:
        if edge["from"] in names and edge["to"] in names:
            drawn = {"from": ids[edge["from"]], "to": ids[edge["to"]]}
            if edge.get("label") and not args.no_edge_labels:
                drawn["label"] = edge["label"]
            if edge.get("arrow"):
                drawn["arrow"] = edge["arrow"]
            edges.append(drawn)

    nodes, edges = expand_instances(nodes, edges, args.instance)
    check_density(nodes, edges, args.allow_dense)
    spec = {"layout": "flow", "direction": args.direction,
            "title": args.title or title_for(data, "concerns", args),
            "description": args.description or
            "How the concerns in scope relate to one another.",
            "nodes": nodes, "edges": edges}
    # Only group when more than one focus is present; a single cluster rect
    # around everything is a frame, not information.
    if len(focuses) > 1:
        spec["groups"] = [{"id": slug(f), "label": f} for f in focuses]
    else:
        for node in nodes:
            node.pop("group", None)
    return spec


def view_concern_hub(data, alphas, all_edges, args):
    if len(args.seed or []) != 1:
        die("concern-hub needs exactly one --seed alpha to sit at the centre.",
            code=2)
    centre = find_by_name(alphas, args.seed[0], "alpha")
    satellites = []
    for rel in centre.get("relatesTo", []) or []:
        target = rel.get("alphaName")
        if not target or target == centre["name"]:
            continue
        satellite = {"label": target}
        if rel.get("relationship") and not args.no_edge_labels:
            satellite["edgeLabel"] = rel["relationship"]
        satellites.append(satellite)
    # Everything pointing back at the centre from elsewhere in the graph.
    known = {s["label"] for s in satellites}
    for alpha in alphas:
        if alpha["name"] in known or alpha["name"] == centre["name"]:
            continue
        for rel in alpha.get("relatesTo", []) or []:
            if rel.get("alphaName") == centre["name"]:
                satellite = {"label": alpha["name"]}
                if rel.get("relationship") and not args.no_edge_labels:
                    satellite["edgeLabel"] = rel["relationship"]
                satellites.append(satellite)
                known.add(alpha["name"])
                break
    if not satellites:
        die(f"{centre['name']!r} declares no relationships, and nothing "
            f"relates to it — there is no hub to draw.")
    # A hub takes every relationship the centre declares, so the scoping flags
    # do not thin it — only a different centre or a deliberate budget does.
    if len(satellites) + 1 > args.max_nodes:
        die(f"{centre['name']!r} has {len(satellites)} relationships, over the "
            f"{args.max_nodes}-node budget.",
            hint="A hub draws all of them, so --focus and --depth will not "
                 "thin it. Either centre on a less connected concern, raise "
                 "--max-nodes if the reader can carry it, or use --view "
                 "concern-map with a tight --focus to show one slice.")

    hub = {"label": centre["name"], "emphasis": "accent"}
    sub = trim(centre.get("description"))
    if args.sublabels and sub:
        hub["sublabel"] = sub
    return {"layout": "hub",
            "title": args.title or f"{centre['name']} in context",
            "description": args.description or
            f"What {centre['name']} depends on, shapes, and is shaped by.",
            "centre": hub, "satellites": satellites}


def view_capability_tree(data, alphas, all_edges, args):
    by_name = {a["name"]: a for a in alphas}

    # The specialisation graph is its own graph. Scoping it over relatesTo
    # neighbourhoods, as the other flow views do, pulls in peers that have no
    # place in a tree — so --seed names a root here and --depth counts
    # generations below it.
    all_links, children = [], defaultdict(list)
    for alpha in alphas:
        for field, verb in (("contributesTo", "contributes to"),
                            ("mapsTo", "is a")):
            parent = alpha.get(field)
            if parent and parent in by_name:
                all_links.append((alpha["name"], parent, verb))
                children[parent].append((alpha["name"], verb))
    if not all_links:
        die("no alpha in this context declares contributesTo or mapsTo — "
            "there is no specialisation tree here.",
            hint="Try --view concern-map, which draws relatesTo instead.")

    def matches(name):
        alpha = by_name.get(name, {})
        if args.focus and str(alpha.get("focusName", "")).lower() not in {
                f.lower() for f in args.focus}:
            return False
        if args.practice and str(
                alpha.get("_contributingPracticeName", "")).lower() not in {
                p.lower() for p in args.practice}:
            return False
        return True

    if args.seed:
        roots = [find_by_name(alphas, s, "alpha")["name"] for s in args.seed]
        keep, queue = set(roots), deque((r, 0) for r in roots)
        # --depth 1 means direct children; 0 would draw a root and nothing else.
        generations = max(args.depth, 1)
        while queue:
            name, level = queue.popleft()
            if level >= generations:
                continue
            for child, _ in children.get(name, []):
                if child not in keep and matches(child):
                    keep.add(child)
                    queue.append((child, level + 1))
        links = [l for l in all_links if l[0] in keep and l[1] in keep]
    else:
        keep = {n for link in all_links for n in (link[0], link[1])
                if matches(n) or n in {l[1] for l in all_links}}
        links = [l for l in all_links if l[0] in keep and l[1] in keep]

    if not links:
        die("nothing in scope declares contributesTo or mapsTo.",
            hint="Roots by number of specialisations:\n" + "\n".join(
                f"  {len(v):>3} children  {k}" for k, v in
                sorted(children.items(), key=lambda kv: -len(kv[1]))[:12]))

    names = {n for link in links for n in (link[0], link[1])}
    enforce_budget(len(names) + instance_delta(args), args.max_nodes,
                   alphas, all_edges,
                   hint="Roots by number of specialisations (best --seed):\n"
                        + "\n".join(f"  {len(v):>3} children  {k}" for k, v in
                                    sorted(children.items(),
                                           key=lambda kv: -len(kv[1]))[:12]))

    taken, ids, nodes = set(), {}, []
    parents = {parent for _, parent, _ in links}
    for name in sorted(names):
        node_id = slug(name, taken)
        ids[name] = node_id
        node = {"id": node_id, "label": name}
        if args.sublabels:
            sub = trim((by_name.get(name) or {}).get("description"))
            if sub:
                node["sublabel"] = sub
        if name in parents:
            node["emphasis"] = "accent"
        nodes.append(node)

    # The verb only earns its place when the tree mixes both kinds. A rollup
    # that is contributesTo throughout would print "contributes to" on all five
    # edges converging on one parent, where they overlap each other and say
    # nothing the arrows do not.
    mixed = len({verb for _, _, verb in links}) > 1
    edges = []
    for child, parent, verb in links:
        edge = {"from": ids[child], "to": ids[parent]}
        if mixed and not args.no_edge_labels:
            edge["label"] = verb
        edges.append(edge)

    nodes, edges = expand_instances(nodes, edges, args.instance)
    check_density(nodes, edges, args.allow_dense)
    return {"layout": "flow", "direction": args.direction,
            "title": args.title or title_for(data, "capability rollup", args),
            "description": args.description or
            "Specialised concerns and the broader concerns they roll up into.",
            "nodes": nodes, "edges": edges}


def view_journey(data, alphas, all_edges, args):
    patterns = data.get("patterns", []) or []
    if not patterns:
        die("this context declares no patterns, so there is no journey to draw.")
    pattern = (find_by_name(patterns, args.pattern, "pattern") if args.pattern
               else max(patterns, key=lambda p: len(p.get("patternViews", []))))
    views = sorted(pattern.get("patternViews", []) or [],
                   key=lambda v: v.get("seq", 0))
    if not views:
        die(f"pattern {pattern['name']!r} has no views.")

    phases = []
    for view in views:
        phase = {"label": view.get("name", f"Phase {view.get('seq', '?')}")}
        if args.sublabels:
            sub = trim(view.get("description"), 60)
            if sub:
                phase["sublabel"] = sub
        if args.items == "activities":
            items = list(view.get("activities", []) or [])
        elif args.items == "alphaStates":
            items = [f"{a} → {s}" if s else a for a, s in alpha_states(view)]
        elif args.items == "none":
            items = []
        else:
            # State names alone. A phase band is narrow, and "HA Configured"
            # survives where "VM Resilience → HA Configured" is clipped to an
            # ellipsis. --view pattern-matrix is where the pairing belongs.
            items = [s or a for a, s in alpha_states(view)]
        if items:
            phase["items"] = items[:args.max_items]
        phases.append(phase)
    if phases:
        phases[-1]["emphasis"] = "accent"

    return {"layout": "timeline",
            "title": args.title or pattern["name"],
            "description": args.description or
            trim(pattern.get("description"), 200) or
            f"The phases of {pattern['name']}, in order.",
            "phases": phases}


def view_maturity(data, alphas, all_edges, args):
    if not args.alpha:
        die("maturity needs --alpha to name the concern whose states to draw.",
            code=2)
    alpha = find_by_name(alphas, args.alpha, "alpha")
    states = alpha.get("states", []) or []
    if not states:
        die(f"{alpha['name']!r} declares no states.")
    enforce_budget(len(states), args.max_nodes, alphas, all_edges, what="tier")

    tiers = []
    # Most mature on top: a stack reads downward, a progression reads upward.
    for state in reversed(states):
        tier = {"label": state.get("name", "")}
        if args.sublabels:
            sub = trim(state.get("description"), 80)
            if sub:
                tier["sublabel"] = sub
        checklists = [c.get("name") for c in state.get("checklists", []) or []
                      if c.get("name")]
        if checklists and args.items == "checklists":
            tier["items"] = checklists[:args.max_items]
        tiers.append(tier)
    tiers[0]["emphasis"] = "accent"

    return {"layout": "stack",
            "title": args.title or f"{alpha['name']} maturity",
            "description": args.description or
            f"How {alpha['name']} progresses, least mature at the bottom.",
            "tiers": tiers}


def view_evidence_map(data, alphas, all_edges, args):
    scoped = scope_alphas(alphas, all_edges, args)
    in_scope = {a["name"] for a in scoped}
    products = [w for w in data.get("workProducts", []) or []
                if set(w.get("contributesToAlphaNames", []) or []) & in_scope]
    if not products:
        die("no work product in this context serves any alpha in scope.",
            hint="Widen the scope, or drop --seed/--focus.")

    served = {name for product in products
              for name in product.get("contributesToAlphaNames", []) or []
              if name in in_scope}
    enforce_budget(len(products) + len(served) + instance_delta(args),
                   args.max_nodes, alphas, all_edges,
                   hint="An evidence map counts artifacts and concerns "
                        "together, so --depth 0 (the seeds alone) is usually "
                        "the right scope here.")

    taken, ids, nodes, groups = set(), {}, [], []
    for product in products:
        node_id = slug(product["name"], taken)
        ids[("wp", product["name"])] = node_id
        node = {"id": node_id, "label": product["name"], "shape": "note"}
        if args.sublabels:
            sub = trim(product.get("description"))
            if sub:
                node["sublabel"] = sub
        parent = product.get("partOf")
        if parent:
            node["group"] = slug(parent)
            if parent not in groups:
                groups.append(parent)
        nodes.append(node)
    for name in sorted(served):
        node_id = slug(name, taken)
        ids[("alpha", name)] = node_id
        nodes.append({"id": node_id, "label": name, "emphasis": "accent"})

    # Deliberately unlabelled. Every edge here says the same thing, and the
    # engine's rule is that an edge label has to carry meaning — repeating
    # "evidences" eight times collides with itself and adds nothing the note
    # shape and the arrow do not already say.
    edges = [{"from": ids[("wp", product["name"])], "to": ids[("alpha", name)]}
             for product in products
             for name in product.get("contributesToAlphaNames", []) or []
             if name in served]

    nodes, edges = expand_instances(nodes, edges, args.instance)
    check_density(nodes, edges, args.allow_dense)
    spec = {"layout": "flow", "direction": args.direction or "LR",
            "title": args.title or title_for(data, "evidence", args),
            "description": args.description or
            "Which artifacts evidence which concerns.",
            "nodes": nodes, "edges": edges}
    if groups:
        spec["groups"] = [{"id": slug(g), "label": g} for g in groups]
    return spec


def view_pattern_matrix(data, alphas, all_edges, args):
    patterns = data.get("patterns", []) or []
    if not patterns:
        die("this context declares no patterns, so there is no matrix to draw.")
    pattern = (find_by_name(patterns, args.pattern, "pattern") if args.pattern
               else max(patterns, key=lambda p: len(p.get("patternViews", []))))
    views = sorted(pattern.get("patternViews", []) or [],
                   key=lambda v: v.get("seq", 0))
    if not views:
        die(f"pattern {pattern['name']!r} has no views.")

    scoped = {a["name"] for a in scope_alphas(alphas, all_edges, args)}
    targets = defaultdict(dict)
    order = []
    for index, view in enumerate(views):
        for name, state in alpha_states(view):
            if scoped and name not in scoped:
                continue
            targets[name][index] = state
            if name not in order:
                order.append(name)
    if not order:
        die(f"no alpha in scope appears in {pattern['name']!r}.")
    enforce_budget(len(order), args.max_nodes, alphas, all_edges, what="row")

    rows = []
    for name in order:
        cells = [{"label": targets[name][i]} if i in targets[name] else None
                 for i in range(len(views))]
        rows.append({"label": name, "cells": cells})

    return {"layout": "matrix",
            "title": args.title or f"{pattern['name']} — state targets by phase",
            "description": args.description or
            "Which concerns each phase advances, and to what state. An empty "
            "cell is a phase that sets no target for that concern.",
            "columns": [{"label": v.get("name", f"Phase {i}")}
                        for i, v in enumerate(views)],
            "rows": rows}


def view_outcome_chain(data, alphas, all_edges, args):
    """How measurable value is produced, as the language models it.

    An Outcome does not stand alone: a MetricContribution says which work
    product carries the number, which concern it belongs to, and the state at
    which it counts; an ObjectiveContribution says which phase of which pattern
    recognises it. That is a contribution chain, and drawing it is how a report
    shows that a recommendation leads somewhere measurable.
    """
    outcomes = data.get("outcomes", []) or []
    if not outcomes:
        die("this context declares no outcomes, so there is no value chain "
            "to draw.")
    if args.outcome:
        chosen = [find_by_name(outcomes, args.outcome, "outcome")]
    else:
        chosen = [max(outcomes, key=lambda o: len(o.get("metricContributions",
                                                        []) or []))]

    taken, ids, nodes, edges = set(), {}, [], []

    def node(key, label, **extra):
        if key not in ids:
            ids[key] = slug(label, taken)
            nodes.append({"id": ids[key], "label": label, **extra})
        return ids[key]

    for outcome in chosen:
        target = node(("outcome", outcome["name"]), outcome["name"],
                      emphasis="accent",
                      **({"sublabel": trim(outcome.get("measureDescription"))}
                         if args.sublabels and outcome.get("measureDescription")
                         else {}))
        for contribution in outcome.get("metricContributions", []) or []:
            concern, product = (contribution.get("alphaName"),
                                contribution.get("workProductName"))
            state = contribution.get("recognizedAtStateName")
            if not concern:
                continue
            via = node(("alpha", concern), concern,
                       **({"sublabel": state} if state else {}))
            if product:
                source = node(("wp", product), product, shape="note")
                edge = {"from": source, "to": via}
                if contribution.get("metricName") and not args.no_edge_labels:
                    edge["label"] = contribution["metricName"]
                edges.append(edge)
            edges.append({"from": via, "to": target})
        for contribution in outcome.get("objectiveContributions", []) or []:
            view = contribution.get("recognizedAtPatternViewName")
            if not view:
                continue
            phase = node(("view", view), view,
                         **({"sublabel": contribution.get("patternName")}
                            if contribution.get("patternName") else {}))
            edges.append({"from": phase, "to": target})

    # The same concern can feed one outcome from several work products.
    seen, unique = set(), []
    for edge in edges:
        key = (edge["from"], edge["to"], edge.get("label"))
        if key not in seen:
            seen.add(key)
            unique.append(edge)
    edges = unique

    enforce_budget(len(nodes) + instance_delta(args), args.max_nodes,
                   alphas, all_edges,
                   hint="Name one outcome with --outcome, or raise "
                        "--max-nodes.")
    nodes, edges = expand_instances(nodes, edges, args.instance)
    check_density(nodes, edges, args.allow_dense)
    return {"layout": "flow", "direction": args.direction or "LR",
            "title": args.title or f"{chosen[0]['name']} — contribution chain",
            "description": args.description or
            "What produces the evidence for this outcome, and where it counts.",
            "nodes": nodes, "edges": edges}


def view_role_map(data, alphas, all_edges, args):
    """Who is involved, from the persona and persona-group graph."""
    groups = data.get("personaGroups", []) or []
    if not groups:
        die("this context declares no persona groups, so there is no role "
            "map to draw.",
            hint="Personas without groups are a list, not a diagram.")
    if args.group:
        chosen = [find_by_name(groups, g, "persona group") for g in args.group]
    else:
        chosen = groups
    by_name = {g["name"]: g for g in groups}

    taken, ids, nodes, edges = set(), {}, [], []

    def node(label, **extra):
        if label not in ids:
            ids[label] = slug(label, taken)
            nodes.append({"id": ids[label], "label": label, **extra})
        return ids[label]

    pending, seen = deque(g["name"] for g in chosen), set()
    while pending:
        name = pending.popleft()
        if name in seen or name not in by_name:
            continue
        seen.add(name)
        group = by_name[name]
        parent = node(name, emphasis="accent")
        for child in group.get("personaGroupNames", []) or []:
            edges.append({"from": parent, "to": node(child, emphasis="accent")})
            pending.append(child)
        for persona in group.get("personaNames", []) or []:
            edges.append({"from": parent, "to": node(persona, shape="person")})

    enforce_budget(len(nodes) + instance_delta(args), args.max_nodes,
                   alphas, all_edges,
                   hint="Name the groups you want with --group:\n" + "\n".join(
                       f"  {len(g.get('personaNames', []) or []):>3} members  "
                       f"{g['name']}" for g in groups[:12]))
    nodes, edges = expand_instances(nodes, edges, args.instance)
    check_density(nodes, edges, args.allow_dense)
    return {"layout": "flow", "direction": args.direction,
            "title": args.title or title_for(data, "roles", args),
            "description": args.description or
            "The teams involved and the roles within them.",
            "nodes": nodes, "edges": edges}


def view_competency_matrix(data, alphas, all_edges, args):
    """The capability rubric: competencies against their level progressions."""
    competencies = data.get("competencies", []) or []
    if not competencies:
        die("this context declares no competencies.")
    if args.competency:
        chosen = [find_by_name(competencies, c, "competency")
                  for c in args.competency]
    else:
        chosen = competencies
    enforce_budget(len(chosen), args.max_nodes, alphas, all_edges, what="row",
                   hint="Name the ones you want with --competency:\n  "
                        + "\n  ".join(c["name"] for c in competencies))

    # Level names are shared across competencies, so they are the columns; what
    # differs per competency is the description, which is the cell.
    columns = []
    for competency in chosen:
        for level in sorted(competency.get("levels", []) or [],
                            key=lambda l: l.get("level", 0)):
            if level.get("name") and level["name"] not in columns:
                columns.append(level["name"])
    if not columns:
        die("no competency in scope declares levels.")

    rows = []
    for competency in chosen:
        levels = {l.get("name"): l for l in competency.get("levels", []) or []}
        rows.append({"label": competency["name"],
                     "cells": [{"label": trim(levels[c].get("description"), 80)
                                or levels[c].get("name", "")}
                               if c in levels else None for c in columns]})

    return {"layout": "matrix",
            "title": args.title or title_for(data, "capability rubric", args),
            "description": args.description or
            "What each capability looks like at each level of maturity.",
            "columns": [{"label": c} for c in columns],
            "rows": rows, "cellWidth": 180}


BUILDERS = {
    "concern-map": view_concern_map,
    "concern-hub": view_concern_hub,
    "capability-tree": view_capability_tree,
    "journey": view_journey,
    "maturity": view_maturity,
    "evidence-map": view_evidence_map,
    "pattern-matrix": view_pattern_matrix,
    "outcome-chain": view_outcome_chain,
    "role-map": view_role_map,
    "competency-matrix": view_competency_matrix,
}


def title_for(data, suffix, args):
    if args.seed:
        return f"{args.seed[0]} — {suffix}"
    if args.practice:
        return f"{', '.join(args.practice)} — {suffix}"
    if args.focus:
        return f"{', '.join(args.focus)} — {suffix}"
    # A merged effective context names itself by concatenating every document
    # that went into it, which is unusable as a title. Say nothing rather than
    # printing a paragraph — the author sets --title, or edits the spec.
    name = data.get("name", "")
    return (f"{name} — {suffix}" if name and len(name) <= 60
            else suffix.capitalize())


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

def report_list(data, alphas, edges):
    out = []
    out.append(f"{data.get('name', '(unnamed)')} "
               f"[{data.get('kind', 'unknown')} {data.get('version', '')}]".strip())
    out.append("")

    focuses = Counter(a.get("focusName", "(none)") for a in alphas)
    out.append(f"Focuses ({len(focuses)}) — scope with --focus")
    for name, count in focuses.most_common():
        out.append(f"  {count:>3} alphas  {name}")
    out.append("")

    contributors = Counter(a["_contributingPracticeName"] for a in alphas
                           if a.get("_contributingPracticeName"))
    if contributors:
        out.append(f"Contributing practices ({len(contributors)}) — scope with "
                   f"--practice")
        for name, count in contributors.most_common():
            out.append(f"  {count:>3} alphas  {name}")
        out.append("")

    ranked = degree_ranking(alphas, edges)
    out.append(f"Alphas by relationship count ({len(alphas)}) — the busiest "
               f"make the best --seed")
    for degree, name in ranked[:20]:
        out.append(f"  {degree:>3} edges   {name}")
    if len(ranked) > 20:
        out.append(f"  … {len(ranked) - 20} more")
    out.append("")

    # Only links whose parent is in this document — a contributesTo pointing
    # at an alpha from a baseline that was not resolved in is not drawable,
    # so advertising it here would promise a view that then fails.
    present = {a["name"] for a in alphas}
    specialised = [(a["name"],
                    "contributes to" if a.get("contributesTo") else "is a",
                    a.get("contributesTo") or a.get("mapsTo"))
                   for a in alphas
                   if (a.get("contributesTo") or a.get("mapsTo")) in present]
    out.append(f"Specialisations ({len(specialised)}) — feeds --view "
               f"capability-tree")
    for name, verb, parent in specialised[:12]:
        out.append(f"      {name} {verb} {parent}")
    if len(specialised) > 12:
        out.append(f"      … {len(specialised) - 12} more")
    out.append("")

    patterns = data.get("patterns", []) or []
    out.append(f"Patterns ({len(patterns)}) — feeds --view journey and "
               f"--view pattern-matrix")
    for pattern in patterns:
        views = sorted(pattern.get("patternViews", []) or [],
                       key=lambda v: v.get("seq", 0))
        names = " → ".join(v.get("name", "?") for v in views)
        out.append(f"  {len(views):>3} views   {pattern.get('name')}")
        if names:
            out.append(f"               {names}")
    out.append("")

    products = data.get("workProducts", []) or []
    out.append(f"Work products ({len(products)}) — feeds --view evidence-map")
    for product in products[:12]:
        serves = product.get("contributesToAlphaNames", []) or []
        out.append(f"  {len(serves):>3} serves  {product.get('name')}")
    if len(products) > 12:
        out.append(f"      … {len(products) - 12} more")
    out.append("")

    outcomes = data.get("outcomes", []) or []
    out.append(f"Outcomes ({len(outcomes)}) — feeds --view outcome-chain")
    for outcome in sorted(outcomes, key=lambda o: -(
            len(o.get("metricContributions", []) or [])
            + len(o.get("objectiveContributions", []) or [])))[:8]:
        links = (len(outcome.get("metricContributions", []) or [])
                 + len(outcome.get("objectiveContributions", []) or []))
        out.append(f"  {links:>3} links   {outcome.get('name')}")
    out.append("")

    groups = data.get("personaGroups", []) or []
    out.append(f"Persona groups ({len(groups)}) — feeds --view role-map")
    for group in groups[:10]:
        members = (len(group.get("personaNames", []) or [])
                   + len(group.get("personaGroupNames", []) or []))
        out.append(f"  {members:>3} members {group.get('name')}")
    out.append("")

    competencies = data.get("competencies", []) or []
    out.append(f"Competencies ({len(competencies)}) — feeds --view "
               f"competency-matrix")
    out.append("      " + ", ".join(c.get("name", "?")
                                    for c in competencies[:12]))
    out.append("")

    deepest = max(alphas, key=lambda a: len(a.get("states", [])), default=None)
    if deepest:
        out.append(f"Deepest state progression — feeds --view maturity")
        out.append(f"  {len(deepest.get('states', [])):>3} states  "
                   f"{deepest['name']}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_instances(values):
    mapping = {}
    for value in values or []:
        if "=" not in value:
            die(f"--instance needs Alpha=Name,Name — got {value!r}", code=2)
        target, names = value.split("=", 1)
        instances = [n.strip() for n in names.split(",") if n.strip()]
        if len(instances) < 2:
            die(f"--instance {target.strip()!r} needs at least two instance "
                f"names, otherwise there is nothing to split.", code=2)
        mapping[target.strip()] = instances
    return mapping


def main():
    parser = argparse.ArgumentParser(
        description="Derive diagram specs from a practice's semantic graph.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Views:\n" + "\n".join(f"  {k:<19}{v}" for k, v in VIEWS.items()))
    parser.add_argument("context", nargs="?",
                        help="Effective context, practice, baseline or method JSON")
    parser.add_argument("--list", action="store_true",
                        help="Print what is derivable from this context and exit")
    parser.add_argument("--view", choices=sorted(VIEWS),
                        help="Which spec to derive")

    scope = parser.add_argument_group("scoping")
    scope.add_argument("--seed", action="append", metavar="ALPHA",
                       help="Centre the view on this alpha (repeatable)")
    scope.add_argument("--depth", type=int, default=1,
                       help="Hops from each seed (default 1)")
    scope.add_argument("--focus", nargs="+", metavar="FOCUS",
                       help="Restrict to these focuses")
    scope.add_argument("--practice", nargs="+", metavar="NAME",
                       help="Restrict to alphas contributed by these practices")
    scope.add_argument("--alpha", metavar="ALPHA",
                       help="The alpha to draw (maturity)")
    scope.add_argument("--pattern", metavar="PATTERN",
                       help="The pattern to draw (journey, pattern-matrix)")
    scope.add_argument("--outcome", metavar="OUTCOME",
                       help="The outcome to draw (outcome-chain)")
    scope.add_argument("--group", action="append", metavar="GROUP",
                       help="Persona group to draw, repeatable (role-map)")
    scope.add_argument("--competency", action="append", metavar="NAME",
                       help="Competency to draw, repeatable "
                            "(competency-matrix)")
    scope.add_argument("--max-nodes", type=int, default=DEFAULT_MAX_NODES,
                       help=f"Node budget (default {DEFAULT_MAX_NODES})")

    shape = parser.add_argument_group("shaping")
    shape.add_argument("--instance", action="append", default=[],
                       metavar="ALPHA=A,B",
                       help="Split one node into named instances, each "
                            "inheriting its edges (repeatable)")
    shape.add_argument("--direction", default="TB", choices=["TB", "LR"],
                       help="Flow direction (default TB)")
    shape.add_argument("--sublabels", action="store_true",
                       help="Add a trimmed description under each label")
    shape.add_argument("--no-edge-labels", action="store_true",
                       help="Drop relationship verbs from edges")
    shape.add_argument("--allow-dense", action="store_true",
                       help="Emit a flow spec too dense to lay out, to be "
                            "rewritten by hand")
    shape.add_argument("--items", choices=["states", "alphaStates",
                                           "activities", "checklists", "none"],
                       default="states",
                       help="What to list inside a timeline phase or stack "
                            "tier (default: state names alone)")
    shape.add_argument("--max-items", type=int, default=3,
                       help="Items listed per phase or tier (default 3)")
    shape.add_argument("--title", help="Override the derived title")
    shape.add_argument("--description", help="Override the derived description")

    out = parser.add_argument_group("output")
    out.add_argument("-o", "--output", help="Write the spec to this path")
    out.add_argument("--out-dir", help="Directory to write <name>.json into")
    out.add_argument("--name", help="Spec filename stem, with --out-dir")
    out.add_argument("--stdout", action="store_true", help="Print the spec")

    args = parser.parse_args()

    if not args.context:
        parser.error("a context JSON path is required")
    if not args.list and not args.view:
        parser.error("one of --list or --view is required")

    data = load_json(args.context)
    alphas = flatten_alphas(data)
    if not alphas:
        die(f"{args.context} declares no alphas.",
            hint="Resolve an effective context first: "
                 "python3 utils/resolve-context.py --by-name \"<Practice>\" "
                 "--transitive -o /tmp/context.json")
    edges = build_edges(alphas)

    if args.list:
        print(report_list(data, alphas, edges))
        return

    args.instance = parse_instances(args.instance)
    spec = BUILDERS[args.view](data, alphas, edges, args)

    text = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    if args.stdout or not (args.output or args.out_dir):
        sys.stdout.write(text)
        return

    if args.out_dir:
        stem = args.name or args.view
        path = Path(args.out_dir) / f"{stem}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}", file=sys.stderr)
    print(f"Render it:  python3 utils/render-diagram.py --dir {path.parent}/",
          file=sys.stderr)


if __name__ == "__main__":
    main()
