"""Shared utilities for Practice Language JSON tools.

Internal module — not a CLI tool. Import from individual scripts:
    from utils._shared import load_json, merge_by_name, MERGEABLE_ARRAYS
"""

import copy
import json
import os
import shutil
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path

# Google Workspace CLI. Resolved from PATH so non-Homebrew installs (npm, for
# example) work; the Homebrew location is only a last-resort fallback.
GWS = shutil.which("gws") or "/opt/homebrew/bin/gws"


# discover-dependencies.py reports documents that live inside a package as
# "bundles/<name>.keleo::documents/<doc>.json". Resolving that form here means
# every consumer of a resolved path can open it, rather than each one learning
# to read archives separately.
PACKAGE_SEPARATOR = "::"


def split_package_path(file_path):
    """Split "package.keleo::member/path.json" into (archive, member).

    Returns (file_path, None) for an ordinary filesystem path.
    """
    text = str(file_path)
    if PACKAGE_SEPARATOR not in text:
        return text, None
    archive, _, member = text.partition(PACKAGE_SEPARATOR)
    return archive, member or None


def read_package_member(archive_path, member_path):
    """Read one member out of a .keleo archive as text.

    Returns (text, None) on success or (None, error_string) on failure. A bare
    document filename is accepted as well as a full member path, provided it
    matches exactly one member.
    """
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if member_path not in names:
                leaf = member_path.rsplit("/", 1)[-1]
                matches = [n for n in names if n.rsplit("/", 1)[-1] == leaf]
                if len(matches) != 1:
                    detail = "not found" if not matches else f"matches {len(matches)} members"
                    return None, f"Member '{member_path}' {detail} in {archive_path}"
                member_path = matches[0]
            return zf.read(member_path).decode("utf-8"), None
    except FileNotFoundError:
        return None, f"File not found: {archive_path}"
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {archive_path}"


def read_document_text(file_path):
    """Read a document as text from a path or a "package::member" reference.

    Returns (text, None) on success or (None, error_string) on failure.
    """
    archive, member = split_package_path(file_path)
    if member is None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read(), None
        except FileNotFoundError:
            return None, f"File not found: {file_path}"
    return read_package_member(archive, member)


def load_json(file_path, exit_on_error=True):
    """Load and parse a JSON file, or a document inside a .keleo package.

    Args:
        file_path: Path to JSON file, or "package.keleo::member.json" (str or Path).
        exit_on_error: If True, print error JSON and sys.exit(1) on failure.
                       If False, raise the underlying exception.

    Returns:
        Parsed JSON as dict/list.
    """
    text, err = read_document_text(file_path)
    if err:
        if exit_on_error:
            print(json.dumps({"error": err}))
            sys.exit(1)
        raise FileNotFoundError(err)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if exit_on_error:
            print(json.dumps({"error": f"Invalid JSON in {file_path}: {e}"}))
            sys.exit(1)
        raise


def version_sort_key(version_str):
    """Parse a semver-ish string into a comparable tuple. Unparsable sorts lowest.

    Tolerant by design: documents carry shortened forms ("1.0") and the odd
    prerelease suffix, and a version that cannot be read should lose a
    "which is newest" comparison rather than crash it.
    """
    if not version_str:
        return (-1,)
    parts = []
    for chunk in str(version_str).split("-")[0].split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            return (-1,)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def load_json_pair(file_path):
    """Load JSON returning (data, error_string) tuple. Never exits.

    Accepts a filesystem path or a "package.keleo::member.json" reference.
    """
    text, err = read_document_text(file_path)
    if err:
        return None, err
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {file_path}: {e}"


def resolve_reference_context(practice_path, baseline_data):
    """Return the vocabulary source for name-validation checks.

    Narrative types and competencies are inherited down the whole baseline
    chain, so a leaf baseline sees only its own. Validating against the leaf
    makes every inherited value look invalid, and "fixing" it rewrites valid
    names to bad fuzzy matches.

    `_effective-context.json` already holds the merged vocabulary from every
    baseline and dependency practice, so prefer it whenever it sits beside the
    practice being fixed. Falls back to the supplied baseline when absent.
    """
    if practice_path:
        candidate = os.path.join(os.path.dirname(os.path.abspath(practice_path)),
                                 "_effective-context.json")
        if os.path.exists(candidate):
            data, err = load_json_pair(candidate)
            if data and not err:
                return data, candidate
    return baseline_data, None


MERGEABLE_ARRAYS = [
    "focuses", "alphas", "activitySpaces", "competencies",
    "narrativeTypes", "narratives", "citations", "assets",
    "workProducts", "patterns", "personas", "personaGroups",
    "alphaInstances", "workProductInstances",
    "patternGroups", "patternOrchestrations", "outcomes",
    "acknowledgements", "references",
]

# Object-valued properties that merge as scalars rather than recursing. A loop
# edge is one statement about the shape of a cycle (merge.md §6.5); half of one
# author's loop spliced onto half of another's describes a cycle neither of them
# modelled, so the overlay replaces the whole object.
ATOMIC_OBJECT_KEYS = {"loopsBackTo"}

# Annotations this module writes for the post-merge passes in resolve-context.py.
# Stripped from the output once those passes have consumed them.
TRACKING_KEYS = ("_layers", "_suppressedByLayers", "_specificityContributions")

# Annotations the merge owns. An overlay never overwrites them — they are
# accumulated by the merge itself, and a document that happens to carry them
# (an effective context fed back in, say) must not reset the accumulation.
_MERGE_OWNED_KEYS = set(TRACKING_KEYS) | {
    "_contributingPracticeName", "_contributingPracticeNames",
}


def _is_named_object_list(value):
    """True when `value` is a non-empty list whose every item is a named object."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(i, dict) and isinstance(i.get("name"), str) and i["name"] for i in value)
    )


def _track_layer(entry, item, source, tracking):
    """Record which layer declared `item`, and what it declared about it.

    Only runs when a composition actually uses `specificityName` or `suppressed`
    — see `scan_tracking_needs`. Every part type extends PracticeElement, so
    tracking unconditionally would stamp provenance onto every checklist item in
    the corpus to serve two constructs almost nothing uses yet.
    """
    if not tracking or source is None:
        return
    if tracking.get("suppression"):
        layers = entry.get("_layers") or []
        if source not in layers:
            entry["_layers"] = layers + [source]
        if item.get("suppressed") is True:
            suppressors = entry.get("_suppressedByLayers") or []
            if source not in suppressors:
                entry["_suppressedByLayers"] = suppressors + [source]
    if tracking.get("specificity"):
        name = item.get("specificityName")
        if isinstance(name, str) and name.strip():
            contributions = entry.get("_specificityContributions") or []
            pair = {"layer": source, "specificityName": name.strip()}
            if pair not in contributions:
                entry["_specificityContributions"] = contributions + [pair]


def _track_subtree(node, source, tracking):
    """Stamp layer tracking on a newly introduced element and all of its parts.

    An element arriving for the first time is deep-copied rather than merged,
    so nothing walks its states, checklists or views. Without this they would
    carry no record of who declared them, and a later suppression of one of
    those parts would have no originator to compare precedence against.
    """
    if not tracking or source is None:
        return
    if isinstance(node, dict):
        if isinstance(node.get("name"), str) and node["name"]:
            _track_layer(node, node, source, tracking)
        for value in node.values():
            _track_subtree(value, source, tracking)
    elif isinstance(node, list):
        for item in node:
            _track_subtree(item, source, tracking)


def merge_element(base, overlay, overlay_source=None, tracking=None):
    """Recursive record merge of two practice element records (merge.md §4.1, §5.1).

    Named-object arrays merge by name so that a redeclaration adds to what it
    inherits rather than replacing it; nested objects recurse; everything else
    is last-writer-wins, which is this resolver's long-standing scalar rule.
    """
    result = copy.deepcopy(base)
    for key, overlay_value in overlay.items():
        if key in _MERGE_OWNED_KEYS:
            continue
        base_value = result.get(key)
        if key in ATOMIC_OBJECT_KEYS:
            result[key] = copy.deepcopy(overlay_value)
        elif _is_named_object_list(base_value) and _is_named_object_list(overlay_value):
            result[key] = merge_by_name(
                base_value, overlay_value, None, overlay_source,
                tracking=tracking, stamp_contributors=False,
            )
        elif isinstance(base_value, dict) and isinstance(overlay_value, dict):
            result[key] = merge_element(base_value, overlay_value, overlay_source, tracking)
        else:
            result[key] = copy.deepcopy(overlay_value)
    return result


def _stamp_contributor(entry, source):
    """Record `source` as a contributor of `entry`, preserving earlier contributors.

    Sets `_contributingPracticeName` to the most recent contributor (last writer
    wins) and appends to the ordered `_contributingPracticeNames` list. When the
    same element name is declared by several documents, the scalar alone loses
    every contributor but the last — consumers deciding practiceDependencyNames
    must read the list.
    """
    if source is None:
        return
    entry["_contributingPracticeName"] = source
    contributors = entry.get("_contributingPracticeNames") or []
    if source not in contributors:
        contributors = contributors + [source]
    entry["_contributingPracticeNames"] = contributors


def merge_by_name(base_list, overlay_list, base_source=None, overlay_source=None,
                  tracking=None, stamp_contributors=True):
    """Merge two lists of objects by 'name' key. Overlay overrides base.

    Same-named records merge recursively (merge.md §5.1) so that a practice
    redeclaring an inherited element adds to its states, checklists and views
    rather than replacing them wholesale.

    When source names are provided and `stamp_contributors` is set, stamps
    _contributingPracticeName (last writer) and _contributingPracticeNames (all
    contributors, in merge order) on each element. Nested parts are merged with
    it unset — provenance belongs on the element, not on every checklist item.
    """
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if stamp_contributors and base_source is not None \
                    and "_contributingPracticeName" not in entry:
                _stamp_contributor(entry, base_source)
            # No layer tracking here: base items are already-accumulated
            # elements carrying the record of who actually declared them.
            # Re-stamping with the previous layer's name would credit a
            # declaration to a document that never made one.
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                combined = merge_element(existing, item, overlay_source, tracking)
                if stamp_contributors:
                    _stamp_contributor(combined, overlay_source)
                _track_layer(combined, item, overlay_source, tracking)
                merged[item["name"]] = combined
            else:
                entry = copy.deepcopy(item)
                if stamp_contributors:
                    _stamp_contributor(entry, overlay_source)
                _track_subtree(entry, overlay_source, tracking)
                merged[item["name"]] = entry
    return list(merged.values())


def merge_pattern_groups(base_list, overlay_list, base_source=None, overlay_source=None):
    """Merge PatternGroup lists with entry-level merge by patternName.

    Groups merge by canonical name per merge spec §6.15. Within same-name
    groups, entries merge by patternName with overlay seq taking precedence.
    Unique groups from either side are preserved as-is.
    """
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if base_source is not None and "_contributingPracticeName" not in entry:
                entry["_contributingPracticeName"] = base_source
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                base_entries = OrderedDict()
                for e in existing.get("entries", []):
                    pn = e.get("patternName")
                    if pn:
                        base_entries[pn] = e
                for e in (item.get("entries") or []):
                    pn = e.get("patternName")
                    if pn:
                        base_entries[pn] = copy.deepcopy(e)

                combined = copy.deepcopy(existing)
                overlay_copy = copy.deepcopy(item)
                overlay_copy.pop("entries", None)
                combined.update(overlay_copy)
                combined["entries"] = list(base_entries.values())

                if overlay_source is not None:
                    combined["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = combined
            else:
                entry = copy.deepcopy(item)
                if overlay_source is not None:
                    entry["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = entry
    return list(merged.values())


def _stage_key(stage):
    """Composite key for an orchestration stage (merge.md §6.15a).

    Keyed on placement, not on pattern name alone: one pattern may legitimately
    appear twice in an orchestration — nested inside a plan and also available
    on demand — and keying on the name would collapse the two into one.
    """
    relative = stage.get("relativeTo") or {}
    return "::".join([
        stage.get("patternName", ""),
        stage.get("relationship", ""),
        relative.get("patternName", ""),
    ])


def _merge_narrative_contexts(base_list, overlay_list):
    """Merge narrativeContexts by the composite key narrativeElementName::seq."""
    merged = OrderedDict()
    for entry in (base_list or []):
        merged[f"{entry.get('narrativeElementName', '')}::{entry.get('seq', '')}"] = \
            copy.deepcopy(entry)
    for entry in (overlay_list or []):
        key = f"{entry.get('narrativeElementName', '')}::{entry.get('seq', '')}"
        if key in merged:
            merged[key] = merge_element(merged[key], entry)
        else:
            merged[key] = copy.deepcopy(entry)
    return list(merged.values())


def _merge_stage(base, overlay):
    """Merge two orchestration stages sharing a composite key (merge.md §6.15a)."""
    combined = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in ("entryCriteria", "exitCriteria"):
            # Placement criteria are first-writer-wins: the author who put the
            # stage here owns the terms on which it is entered and left.
            if not combined.get(key):
                combined[key] = copy.deepcopy(value)
        elif key == "narrativeContexts":
            combined[key] = _merge_narrative_contexts(combined.get(key), value)
        else:
            # seq, relationship, recurrence, relativeTo, trigger: each describes
            # placement rather than content, and a stage merged halfway would
            # describe a shape neither author intended.
            combined[key] = copy.deepcopy(value)
    return combined


def merge_pattern_orchestrations(base_list, overlay_list, base_source=None,
                                 overlay_source=None):
    """Merge PatternOrchestration lists per merge.md §6.15a.

    Orchestrations merge by canonical name so a practice can refine one it
    inherits — unlike a PatternGroup, which merges by name as a way of
    collecting contributions from many authors. Two unrelated practices naming
    an orchestration the same thing is a collision, not a contribution.
    """
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if base_source is not None and "_contributingPracticeName" not in entry:
                _stamp_contributor(entry, base_source)
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" not in item:
            continue
        if item["name"] not in merged:
            entry = copy.deepcopy(item)
            _stamp_contributor(entry, overlay_source)
            merged[item["name"]] = entry
            continue

        existing = merged[item["name"]]
        stages = OrderedDict()
        for stage in existing.get("stages", []):
            stages[_stage_key(stage)] = copy.deepcopy(stage)
        for stage in (item.get("stages") or []):
            key = _stage_key(stage)
            stages[key] = _merge_stage(stages[key], stage) if key in stages \
                else copy.deepcopy(stage)

        overlay_copy = {k: v for k, v in item.items()
                        if k not in ("stages", "narrativeTypeName")}
        combined = merge_element(existing, overlay_copy, overlay_source)
        if not combined.get("narrativeTypeName") and item.get("narrativeTypeName"):
            combined["narrativeTypeName"] = item["narrativeTypeName"]
        # seq is unique only among sequential stages, so this is not a total
        # order; a stable sort leaves stages that share a seq in merge order.
        combined["stages"] = sorted(stages.values(), key=lambda s: s.get("seq", 0))
        _stamp_contributor(combined, overlay_source)
        merged[item["name"]] = combined
    return list(merged.values())


def scan_tracking_needs(documents):
    """Report which post-merge passes a composition actually needs.

    `specificityName` and `suppressed` sit on PracticeElement, so they reach
    every element and every part of one. Tracking them unconditionally would
    stamp provenance onto every checklist item in the corpus to serve two
    constructs no loaded document may use, so the merge asks first.

    `documents` is an iterable of (name, data) pairs.
    """
    needs = {"specificity": False, "suppression": False}

    def walk(node):
        if needs["specificity"] and needs["suppression"]:
            return
        if isinstance(node, dict):
            name = node.get("specificityName")
            if isinstance(name, str) and name.strip():
                needs["specificity"] = True
            if node.get("suppressed") is True:
                needs["suppression"] = True
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for _name, data in documents:
        walk(data)
        if needs["specificity"] and needs["suppression"]:
            break
    return needs


def finalize_variants(effective):
    """Post-merge variant aggregation per merge.md §7.2a (alphas) and §7.2b (work products).

    Walks alphas and work products with mapsTo, appends the full variant object
    to the target element's variants array. Variants remain in the top-level
    array as authored elements; the variants array on the parent is additive
    for UI rendering and taxonomy discovery.
    """
    for array_key in ("alphas", "workProducts"):
        items = effective.get(array_key, [])
        if not items:
            continue
        by_name = {item["name"]: item for item in items if "name" in item}
        for item in items:
            target_name = item.get("mapsTo")
            if target_name and target_name in by_name:
                target = by_name[target_name]
                variants = target.setdefault("variants", [])
                if not any(v.get("name") == item["name"] for v in variants):
                    variants.append(copy.deepcopy(item))


def _visit_elements(container, fn, path=""):
    """Call `fn(element, path)` for every object inside the merged element tree."""
    if isinstance(container, dict):
        for key, value in container.items():
            _visit_elements(value, fn, f"{path}/{key}" if path else key)
    elif isinstance(container, list):
        for item in container:
            if isinstance(item, dict):
                name = item.get("name", "")
                item_path = f"{path}/{name}" if name else path
                fn(item, item_path)
                _visit_elements(item, fn, item_path)
            else:
                _visit_elements(item, fn, path)


def finalize_specificity(effective, layer_order):
    """Specificity chain accumulation, merge.md §7.2e.

    Writes the accumulated `specificity` chain most specific first — reverse
    dependency order, so a layer's own contribution precedes those of the
    layers it depends on. `layer_order` is the composition's deterministic
    dependency order, which already carries the topological-then-name tie-break
    that keeps the chain independent of the order documents were loaded in.

    An authored `specificity` is discarded rather than merged: the chain
    depends on which practices are loaded, and a source document cannot know
    that.
    """
    position = {name: i for i, name in enumerate(layer_order)}
    fallback = len(layer_order)

    def apply(element, _path):
        contributions = element.pop("_specificityContributions", None)
        element.pop("specificity", None)
        if not contributions:
            return
        ordered = sorted(
            contributions,
            key=lambda c: -position.get(c["layer"], fallback),
        )
        chain = []
        for contribution in ordered:
            value = contribution["specificityName"]
            if value not in chain:
                chain.append(value)
        if chain:
            element["specificity"] = chain

    for key in MERGEABLE_ARRAYS:
        if key in effective:
            _visit_elements({key: effective[key]}, apply)


def finalize_suppression(effective, layer_order):
    """Suppression resolution, merge.md §7.2f.

    Removes elements carrying `suppressed: true`. Runs after every layer has
    overlaid, so a suppression declared in a dependent practice reaches an
    element contributed by the practice it depends on.

    A layer that redeclares the element without suppressing it requires it; the
    layer that introduced the element does not, or suppressing anything
    inherited would be impossible. Precedence then decides, earliest layer
    winning, and the outcome is recorded rather than applied silently.

    References into a removed element are reported, not repaired: per
    composition.md §4.9.2 they are an error in the composed result, and
    suppressing an element means checking what pointed at it.

    Returns a report dict with `removed`, `overridden` and `danglingReferences`.
    """
    position = {name: i for i, name in enumerate(layer_order)}
    fallback = len(layer_order)
    removed = []
    overridden = []

    def rank(layer):
        return position.get(layer, fallback)

    def decide(element, path):
        """Return True when the element should be dropped from the composition."""
        suppressors = element.get("_suppressedByLayers") or []
        if not suppressors:
            return False
        layers = element.get("_layers") or []
        requirers = [l for l in layers[1:] if l not in suppressors]
        winning_suppressor = min(suppressors, key=rank)
        record = {
            "path": path,
            "name": element.get("name", ""),
            "suppressedBy": winning_suppressor,
        }
        if not requirers:
            removed.append(record)
            return True
        winning_requirer = min(requirers, key=rank)
        if rank(winning_requirer) < rank(winning_suppressor):
            element.pop("suppressed", None)
            element["_suppressionResolution"] = {
                "outcome": "kept",
                "requiredBy": winning_requirer,
                "suppressedBy": winning_suppressor,
            }
            overridden.append({**record, "requiredBy": winning_requirer})
            return False
        record["overrodeRequirementFrom"] = winning_requirer
        removed.append(record)
        return True

    def prune(container, path=""):
        if isinstance(container, dict):
            for key, value in container.items():
                prune(value, f"{path}/{key}" if path else key)
        elif isinstance(container, list):
            kept = []
            for item in container:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    item_path = f"{path}/{name}" if name else path
                    if decide(item, item_path):
                        continue
                    prune(item, item_path)
                kept.append(item)
            container[:] = kept

    for key in MERGEABLE_ARRAYS:
        if key in effective:
            prune(effective[key], key)

    dangling = _find_dangling_references(effective, removed)
    return {"removed": removed, "overridden": overridden, "danglingReferences": dangling}


def _find_dangling_references(effective, removed):
    """Report symbolic references left pointing at a suppressed element."""
    targets = {entry["name"] for entry in removed if entry.get("name")}
    if not targets:
        return []
    findings = []

    def scan(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "name":
                    continue
                if isinstance(value, str) and value in targets:
                    findings.append({"path": path, "property": key, "target": value})
                else:
                    scan(value, f"{path}/{key}" if path else key)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, str) and item in targets:
                    findings.append({"path": path, "property": "", "target": item})
                else:
                    name = item.get("name") if isinstance(item, dict) else None
                    scan(item, f"{path}/{name}" if name else path)

    for key in MERGEABLE_ARRAYS:
        if key in effective:
            scan(effective[key], key)
    return findings


def strip_merge_tracking(effective):
    """Remove the bookkeeping annotations the merge passes leave behind."""
    def clear(node):
        if isinstance(node, dict):
            for key in TRACKING_KEYS:
                node.pop(key, None)
            for value in node.values():
                clear(value)
        elif isinstance(node, list):
            for item in node:
                clear(item)

    clear(effective)


def load_json_from_keleo(keleo_path, document_name=None, document_type=None):
    """Load a JSON document from a .keleo ZIP archive.

    Returns (data, None) on success or (None, error_string) on failure.
    If document_name is provided, matches against manifest documentName.
    If document_type is provided, filters by documentType.
    If neither is provided, returns the entry-point document.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            target = None
            for doc in documents:
                if document_name and doc.get("documentName") == document_name:
                    if document_type is None or doc.get("documentType") == document_type:
                        target = doc
                        break
                elif document_type and doc.get("documentType") == document_type:
                    target = doc
                    break

            if target is None:
                for doc in documents:
                    if doc.get("entryPoint"):
                        target = doc
                        break

            if target is None:
                target = documents[0]

            zip_path = target.get("path", "")
            if zip_path not in zf.namelist():
                return None, f"Document path {zip_path} not found in {keleo_path}"

            data = json.loads(zf.read(zip_path))
            return data, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"


def load_all_from_keleo(keleo_path):
    """Load all JSON documents from a .keleo ZIP archive.

    Returns (list_of_dicts, None) on success or (None, error_string) on failure.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            result = []
            for doc_entry in documents:
                zip_path = doc_entry.get("path", "")
                if zip_path not in zf.namelist():
                    continue
                data = json.loads(zf.read(zip_path))
                result.append(data)
            return result, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"



def detect_kind(data):
    """Classify JSON by schema discrimination rules."""
    kind = data.get("kind", "")
    if kind in ("practice", "method", "practiceBaseline"):
        return kind
    if any(key in data for key in ("practices", "practiceNames", "baselinePractice")):
        return "method"
    if "baselinePracticeName" in data:
        return "practice"
    return "practiceBaseline"


def get_project_root():
    """Find the project root directory (containing .claude/ or CLAUDE.md)."""
    current = Path(__file__).resolve().parent.parent
    for ancestor in [current] + list(current.parents):
        if (ancestor / ".claude").is_dir() or (ancestor / "CLAUDE.md").is_file():
            return ancestor
    return current


def load_user_config():
    """Load user config from .claude/user-config.json. Returns dict (empty if missing)."""
    config_path = get_project_root() / ".claude" / "user-config.json"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_user_config(config):
    """Save user config to .claude/user-config.json."""
    config_path = get_project_root() / ".claude" / "user-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def get_schema_version(schema_path=None):
    """Extract schemaVersion from the schema's $comment field.

    Returns the version string (e.g. '1.0.0') or None if not found.
    """
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent.parent / "deps" / "language.schema.json"
    try:
        data = load_json(schema_path, exit_on_error=False)
        comment = data.get("$comment", "")
        if comment.startswith("schemaVersion:"):
            return comment.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def increment_version(version_str, bump="patch"):
    """Increment a semver version string.

    Args:
        version_str: Current version (e.g. '1.0.0', '1.0', '2').
        bump: 'patch', 'minor', or 'major'.

    Returns:
        Incremented three-part semver string.
    """
    parts = (version_str or "1.0.0").split(".")
    while len(parts) < 3:
        parts.append("0")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


def build_dependency_versions(data):
    """Build dependencyVersions array from a document's declared dependencies.

    Scans the document's dependency declarations (baselinePracticeName,
    practiceDependencyNames, practiceNames) and builds version constraint
    entries using caret ranges from resolved dependency versions.

    Args:
        data: The document dict.

    Returns:
        List of DocumentVersionConstraint dicts, or empty list.
    """
    constraints = []
    seen = set()

    dep_names = []
    bpn = data.get("baselinePracticeName")
    if bpn:
        dep_names.append(bpn)
    dep_names.extend(data.get("practiceDependencyNames", []))
    dep_names.extend(data.get("practiceNames", []))
    for bpn_entry in data.get("baselinePracticeNames", []):
        dep_names.append(bpn_entry)

    for name in dep_names:
        if name and name not in seen:
            seen.add(name)
            constraints.append({
                "documentName": name,
                "versionRange": "",
            })

    return constraints
