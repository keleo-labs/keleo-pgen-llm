"""Render Practice Language records and resolved references for notebook retrieval."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import quote


LABELS = {
    "alphas": "Alphas", "levelOfDetailName": "Level of detail",
    "levelsOfDetail": "Levels of detail", "practiceNames": "Member practices",
    "practices": "Embedded member practices", "patternOrchestrations": "Orchestrations",
    "checklist": "Checklist", "seq": "Sequence", "narrativeContexts": "Narrative guidance",
}
TARGETS = {
    "alphaName": "alphas", "stateName": "states", "workProductName": "workProducts",
    "levelOfDetailName": "levelsOfDetail", "activitySpaceName": "activitySpaces",
    "activityName": "activities", "patternName": "patterns", "patternViewName": "patternViews",
    "orchestrationName": "patternOrchestrations", "patternOrchestrationName": "patternOrchestrations",
    "competencyName": "competencies", "competencyLevelName": "levels", "focusName": "focuses",
    "personaName": "personas", "personaGroupName": "personaGroups", "outcomeName": "outcomes",
    "narrativeTypeName": "narrativeTypes", "narrativeName": "narratives",
    "narrativeElementName": "narrativeElements", "assetName": "assets", "citationName": "citations",
    "alphaInstanceName": "alphaInstances", "workProductInstanceName": "workProductInstances",
    "contributesToAlphaName": "alphas", "contributingPatternName": "patterns",
    "recognizedAtStateName": "states", "recognizedAtPatternViewName": "patternViews",
    "viewName": "patternViews",
    "supportingAlphas": "alphas", "requiredCompetencies": "competencies", "involves": "personaGroups",
}
PARENTS = {
    "states": ("alphas", "alphaName"), "levelsOfDetail": ("workProducts", "workProductName"),
    "levels": ("competencies", "competencyName"), "activities": ("activitySpaces", "activitySpaceName"),
    "patternViews": ("patterns", "patternName"), "narrativeElements": ("narrativeTypes", "narrativeTypeName"),
}
BINDING_REFERENCES = {
    "fromState": ("stateName", 0), "toState": ("stateName", 1),
    "fromLevelOfDetail": ("levelOfDetailName", 0), "toLevelOfDetail": ("levelOfDetailName", 1),
}
CONTEXT_FIELDS = ("description", "checklist", "entryCriteria", "exitCriteria", "evidencedBy", "evidenceBy",
                  "doneCriteria", "completionCriteria", "url", "path")
URL = re.compile(r'https?://[^\s<>\]"]+')


def label(key):
    return LABELS.get(key, re.sub(r"(?<=[a-z0-9])(?=[A-Z])|_", " ", key).capitalize())


def section_id(section, field=""):
    parts = f"{section} {field}".lower()
    return re.sub(r"[^a-z0-9]+", "-", parts).strip("-")


def plain(value):
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", " ".join(value.splitlines()))


def scalar(value):
    if (isinstance(value, str) and value.strip() and "\n" not in value and value == value.strip()
            and not re.match(r'^(?:true$|false$|null$|[\d"\[{]|-\d)', value)):
        return plain(value)
    return json.dumps(value, ensure_ascii=False)


def synthesized(record):
    tags = record.get("tags")
    return isinstance(tags, dict) and "synthesized" in (tags.get("lifecycleTags") or [])


@dataclass
class Target:
    record: dict
    doc: object
    location: tuple
    section: str
    source: str


class References:
    def __init__(self, doc, view, library, members, outputs):
        self.doc = doc
        self.library = library
        self.outputs = outputs
        self.primary = defaultdict(list)
        self.support = defaultdict(list)
        self.index(self.primary, doc, view if view is not None else doc.data,
                   "Studio practice view" if view is not None else "Authored content")
        for member, member_view in members:
            self.index(self.primary, member, member_view or member.data, "Studio practice view")
        for dependency in library.values():
            if dependency is not doc:
                self.index(self.support, dependency, dependency.data, "Authored content")

    def index(self, index, doc, data, section, ancestry=(), inherited_source=None):
        for key, values in data.items():
            if not isinstance(values, list) or key in ("practices", "checklist"):
                continue
            visible_section = section
            if not ancestry and section == "Studio practice view" and doc.data.get(key) == values:
                visible_section = "Authored content"
            for record in values:
                if not isinstance(record, dict) or not isinstance(record.get("name"), str):
                    continue
                location = (*ancestry, (key, record["name"]))
                owner = record.get("contributingPracticeName") or record.get("_contributingPracticeName")
                if not owner and section == "Studio practice view" and len(location) == 1:
                    originals = [source.name for source in self.library.values()
                                 if any(isinstance(row, dict) and row.get("name") == record["name"]
                                        for row in source.data.get(key, []))]
                    owner = originals[0] if len(originals) == 1 else doc.name
                source = owner or inherited_source or doc.name
                index[key, record["name"].casefold()].append(Target(record, doc, location, visible_section, source))
                self.index(index, doc, record, visible_section, location, source)

    def document_label(self, doc, section="Authored content", field=""):
        title = f"{plain(doc.name)} v{plain(doc.version)} · {section}"
        if field:
            title += f" / {label(field)}"
        exported = self.outputs.get(doc.filename)
        if exported and exported[0].data == doc.data:
            anchor = "#" + section_id(section, field)
            return f"[{title}]({quote(doc.filename)}{anchor}) (`{doc.filename}`)"
        return f"{title} (separate export `{doc.filename}`, absent from this export)"

    def excerpt(self, key, value, record, ancestry, source_doc):
        if key in ("baselinePracticeName", "baselinePracticeNames", "baselineName",
                   "practiceDependencyNames", "practiceNames", "documentName"):
            doc = self.library.get(value)
            return (f"Document context — {self.document_label(doc)}." if doc else ""), {}
        singular = key[:-1] if key.endswith("Names") else key
        kind = TARGETS.get(singular)
        if key in ("activitySpaces", "activities") and ("patternViews" in dict(ancestry)):
            kind = key
        if key in ("contributesTo", "mapsTo", "partOf") and ancestry:
            kind = next((group for group, _ in reversed(ancestry)
                         if group in ("alphas", "workProducts")), None)
        if key == "instanceName":
            kind = "workProductInstances" if "levelOfDetailName" in record else "alphaInstances"
        if not kind:
            return "", {}

        token = (kind, value.casefold())
        scope = record.get("baselineName") or record.get("practiceName")
        parent = PARENTS.get(kind)
        candidates = []
        indexes = (self.primary, self.support) if self.doc.kind == "method" else (self.primary,)
        for index in indexes:
            candidates = index.get(token, [])
            if scope:
                candidates = [target for target in candidates
                              if scope in (target.doc.name, target.source)]
            if parent:
                group, field = parent
                parent_name = record.get(field) or dict(ancestry).get(group)
                if not parent_name and record.get("instanceName"):
                    instance_kind = "alphaInstances" if group == "alphas" else "workProductInstances"
                    instances = self.primary.get((instance_kind, record["instanceName"].casefold()), [])
                    if len(instances) == 1:
                        parent_name = instances[0].record.get(field)
                if isinstance(parent_name, str):
                    candidates = [target for target in candidates if any(
                        group == candidate_group and parent_name.casefold() == candidate_name.casefold()
                        for candidate_group, candidate_name in target.location[:-1])]
            if candidates:
                break

        local = [target for target in candidates if target.doc is source_doc]
        candidates = local or candidates
        unique = {(target.source, target.location, json.dumps(target.record, sort_keys=True)): target
                  for target in reversed(candidates)}
        if len(unique) != 1:
            if len(unique) > 1:
                names = ", ".join(sorted({target.doc.name for target in unique.values()}))
                return f"Reference is ambiguous in the available sources ({plain(names)}).", {}
            return "Reference target is unavailable in the exported context.", {}
        target = next(iter(unique.values()))
        title = " / ".join(plain(name) for _, name in target.location)
        if synthesized(target.record):
            return f"Referenced {title} is a Studio-synthesised placeholder. Its definition is unavailable.", {}
        detail = self.document_label(target.doc, target.section, target.location[0][0])
        source = f" · contribution from {plain(target.source)}" if target.source != target.doc.name else ""
        excerpt = {field: target.record[field] for field in CONTEXT_FIELDS if target.record.get(field)}
        return f"Reference context — {title} in {detail}{source}.", excerpt


def render_fields(lines, data, refs, doc, depth=0, ancestry=(), section="", inventory=None,
                  target=None, endpoints=None):
    prefix = "  " * depth
    target = data.get("targetAlpha") or data.get("targetWorkProduct") or target
    if synthesized(data):
        lines.append(f"{prefix}- **Studio-synthesised placeholder.** The definition is unavailable.")
    for key, value in data.items():
        title = f"{plain(label(key))} (`{plain(key)}`)"
        if section:
            lines.extend(["", f'<a id="{section_id(section, key)}"></a>', f"### {title}", ""])
        lead = f"{prefix}- " if not section else ""
        step = depth + (not section)
        if isinstance(value, dict) and value:
            if lead:
                lines.append(f"{lead}**{title}**")
            render_fields(lines, value, refs, doc, step, ancestry, inventory=inventory, target=target)
        elif isinstance(value, list) and value:
            if lead:
                lines.append(f"{lead}**{title}**")
            for item in value:
                item_prefix = "  " * step
                if isinstance(item, dict) and item:
                    name = item.get("name")
                    location = (*ancestry, (key, name)) if isinstance(name, str) else ancestry
                    if section and isinstance(name, str):
                        lines.extend(["", f"#### {plain(name)}", ""])
                        render_fields(lines, item, refs, doc, step, location, inventory=inventory, target=target)
                    else:
                        lines.append(f"{item_prefix}1. **{plain(name)}**" if isinstance(name, str)
                                     else f"{item_prefix}1. Entry")
                        pair = (data, target) if key in ("stateContributions", "lodContributions") and target else None
                        render_fields(lines, item, refs, doc, step + 2, location, inventory=inventory,
                                      target=target, endpoints=pair)
                else:
                    lines.append(f"{item_prefix}1. {scalar(item)}")
                    add_context(lines, key, item, data, refs, doc, step + 2, ancestry, inventory)
        else:
            lines.append(f"{lead}**{title}** — {scalar(value)}" if lead else scalar(value))
            ref_key, ref_record = key, data
            if endpoints and key in BINDING_REFERENCES:
                ref_key, endpoint = BINDING_REFERENCES[key]
                ref_record = endpoints[endpoint]
            add_context(lines, ref_key, value, ref_record, refs, doc, step, ancestry, inventory)


def add_context(lines, key, value, record, refs, doc, depth, ancestry, inventory):
    if not isinstance(value, str):
        return
    prefix = "  " * depth
    if inventory is not None:
        section = " / ".join(name for _, name in ancestry) or doc.name
        for url in URL.findall(value):
            inventory[url.rstrip(".,);")].add(section)
        if key == "path" and any(group == "assets" for group, _ in ancestry):
            inventory[value].add(section)
    if refs:
        description, excerpt = refs.excerpt(key, value, record, ancestry, doc)
        if description:
            lines.append(f"{prefix}- {description}")
            if excerpt:
                render_fields(lines, excerpt, None, doc, depth + 1)


def render(doc, view, library, edges, issues, diagnostics, members, outputs):
    refs = References(doc, view, library, members, outputs)
    lines = [f"# {plain(doc.name)}", "", f"{doc.kind.title()} · version {plain(doc.version)}",
             "", f"Source — {plain(doc.source)}"]
    if members:
        lines.extend(["", "## Method members", ""])
        lines.extend(f"1. {refs.document_label(member)}" for member, _ in members)
    if edges or issues or diagnostics:
        lines.extend(["", "## Dependencies and gaps", ""])
        for owner, targets in edges.items():
            for target in targets:
                lines.append(f"- {plain(owner.name)} uses {refs.document_label(target)}.")
        lines.extend(f"- Unresolved dependency — {plain(issue)}." for issue in issues)
        lines.extend(f"- Studio resolver message — {plain(row)}" for row in diagnostics.splitlines() if row)

    inventory = defaultdict(set)
    lines.extend(["", "## Authored content"])
    render_fields(lines, doc.data, refs, doc, section="Authored content", inventory=inventory)
    if view is not None:
        lines.extend(["", "## Studio practice view", "",
                      "Studio GAS adds or changes the fields below. Other fields retain their authored values "
                      "unless listed as omitted."])
        if issues or diagnostics:
            lines.extend(["", "**Incomplete Studio view.** See Dependencies and gaps."])
        changed = {key: value for key, value in view.items()
                   if key not in doc.data or value != doc.data[key]}
        omitted = [key for key in doc.data if key not in view]
        if omitted:
            lines.extend(["", "Studio omits these authored fields in its composed view — "
                          + ", ".join(f"`{plain(key)}`" for key in omitted) + "."])
        if changed:
            render_fields(lines, changed, refs, doc, section="Studio practice view", inventory=inventory)
        else:
            lines.extend(["", "The visible content matches the authored content."])

    if inventory:
        lines.extend(["", "## External sources and assets", "",
                      "Add a source separately when a question requires its contents.", ""])
        for address, sections in inventory.items():
            locations = ", ".join(plain(name) for name in sorted(sections))
            display = f"<{address}>" if URL.fullmatch(address) else plain(address)
            lines.append(f"- {display} · referenced in {locations}")
    return "\n".join(lines).rstrip() + "\n"
