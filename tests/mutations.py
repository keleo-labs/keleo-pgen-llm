"""Deliberate defects planted in the known-good practice fixture.

Each mutation names the assertion that must catch it. `eval-skill-output.py
--selftest` grades the clean fixture, then grades a copy carrying each defect
in turn, and reports any assertion that fails to notice. An assertion nothing
can trip is an assertion that inflates every eval score it appears in.

Borrowed from ponytail's agentic benchmark (MIT), where every instrument ships
a `good` and a `bad` reference and must pass one and catch the other before
any measurement is trusted.

Mutations are applied to an in-memory copy of the fixture, so there are no
mutant files on disk to drift from the fixture they derive from.

Defects marked "memory:" reproduce a mistake that actually reached generated
output and was recorded as project feedback.
"""

# Each entry: (assertion_id, slug, what the defect is, mutate_fn)
# mutate_fn takes the parsed fixture dict and changes it in place.

def _alpha(d, name):
    return next(a for a in d["alphas"] if a["name"] == name)


def _wp(d, name):
    return next(w for w in d["workProducts"] if w["name"] == name)


def _activity(d, name):
    return next(a for a in d["activities"] if a["name"] == name)


def _rename_alpha(d, old, new):
    """Rename an alpha and every reference to it.

    A rename that leaves references behind trips a dozen unrelated crossref
    errors, which proves nothing about the assertion under test. A mutation
    must isolate one defect.
    """
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("name", "alphaName", "practiceElementName") and value == old:
                    node[key] = new
                elif key == "contributesToAlphaNames" and isinstance(value, list):
                    node[key] = [new if v == old else v for v in value]
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(d)


MUTATIONS = [
    # --- structural ---
    (
        "structure:kind", "wrong-kind",
        "kind discriminator set to a value the schema does not define",
        lambda d: d.__setitem__("kind", "practiceDocument"),
    ),
    (
        "structure:uniqueness", "duplicate-alpha-name",
        "two alphas share a name, so symbolic references become ambiguous",
        lambda d: _alpha(d, "Onboarding Readiness").__setitem__("name", "Platform Onboarding"),
    ),
    (
        "coverage:alpha-states", "two-state-alpha",
        "an alpha drops below the three-state minimum",
        lambda d: _alpha(d, "Platform Onboarding")["states"].pop(),
    ),
    (
        "coverage:wp-lods", "single-lod",
        "a work product drops below the two-LOD minimum",
        lambda d: _wp(d, "Onboarding Guide")["levelsOfDetail"].pop(),
    ),

    # --- alpha relationships (memory: no floating alphas) ---
    (
        "rel:alpha-practice", "floating-alpha",
        "memory: a new alpha with neither contributesTo nor mapsTo",
        lambda d: _alpha(d, "Platform Onboarding").pop("contributesTo"),
    ),
    (
        "qual:relatesto-targets", "dangling-relatesto",
        "relatesTo names an alpha that exists nowhere in the effective context",
        lambda d: _alpha(d, "Platform Onboarding")["relatesTo"][0].__setitem__(
            "alphaName", "Nonexistent Alpha"),
    ),
    (
        "bref:alpha", "dangling-contributesto",
        "contributesTo points at a baseline alpha that does not exist",
        lambda d: _alpha(d, "Platform Onboarding").__setitem__(
            "contributesTo", "Platform Consumption Surface"),
    ),
    (
        "bref:focus", "unknown-focus",
        "focusName is not one of the baseline's focuses",
        lambda d: _alpha(d, "Platform Onboarding").__setitem__("focusName", "Delivery"),
    ),
    (
        "rel:contributes-to-state", "dangling-contributes-to-state",
        "contributesToState names a state the parent alpha does not have",
        lambda d: _alpha(d, "Platform Onboarding")["states"][0].__setitem__(
            "contributesToState", "Partially Available"),
    ),
    (
        "rel:mapsto-naming", "variant-repeats-parent",
        "memory: a mapsTo variant name repeats the parent type, which IS-A makes redundant",
        lambda d: _rename_alpha(d, "Developer Workspace", "Developer Workspace Platform Asset"),
    ),

    # --- cross-references ---
    (
        "xref:activity-alpha", "activity-unknown-state",
        "an activity contributes to a state its alpha does not have",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot")["contributesTo"][0].__setitem__(
            "stateName", "Trialled"),
    ),
    (
        "xref:activity-wp", "activity-unknown-lod",
        "an activity works on a level of detail that does not exist",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot")["worksOn"][0].__setitem__(
            "levelOfDetailName", "Sketch Path"),
    ),
    (
        "xref:activity-persona", "activity-unknown-group",
        "an activity involves a persona group that does not exist",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot").__setitem__(
            "involves", ["Enablement Guild"]),
    ),
    (
        "xref:activity-persona", "unknown-ledby",
        "ledBy names a persona the practice never defines",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot").__setitem__(
            "ledBy", "Platform Product Owner"),
    ),
    (
        "xref:persona", "group-unknown-member",
        "a persona group lists a member persona that does not exist",
        lambda d: d["personaGroups"][0]["personaNames"].append("Release Manager"),
    ),
    (
        "xref:lod-alpha", "lod-unknown-state",
        "a level of detail contributes to a state that does not exist",
        lambda d: _wp(d, "Onboarding Guide")["levelsOfDetail"][0]["contributesTo"][0].__setitem__(
            "stateName", "Trialled"),
    ),
    (
        "xref:pattern", "pattern-unknown-state",
        "a pattern view references an alpha state that does not exist",
        lambda d: d["patterns"][0]["patternViews"][0]["alphaStates"][0].__setitem__(
            "stateName", "Trialled"),
    ),
    (
        "xref:citation", "dangling-citation-ref",
        "a narrative cites a work that is not in the citations array",
        lambda d: d["narratives"][0].__setitem__(
            "citationNames", ["An Uncited Work"]),
    ),
    (
        "xref:outcome-refs", "outcome-unknown-alpha",
        "an outcome's metric contribution names an alpha that does not exist",
        lambda d: d["outcomes"][0]["metricContributions"][0].__setitem__(
            "alphaName", "Platform Adoption Funnel"),
    ),
    (
        "bref:activityspace", "invented-activity-space",
        "memory: a Phase 3 agent invents an activity space absent from the baseline",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot").__setitem__(
            "activitySpaceName", "Accelerate Developer Onboarding"),
    ),
    (
        "bref:competency", "invented-competency-level",
        "memory: a Phase 3 agent invents a competency level name",
        lambda d: _activity(d, "Run A Guided Onboarding Pilot")
            ["recommendedCompetencyLevels"][0].__setitem__("competencyLevelName", "Expert"),
    ),
    (
        "xref:narrative-type", "invented-narrative-type",
        "memory: a narrative names a type the baseline does not define",
        lambda d: d["narratives"][0].__setitem__("narrativeTypeName", "The Hero's Journey"),
    ),
    (
        "bref:alias", "alias-unknown-target",
        "an alias targets an element that does not exist",
        lambda d: d["practiceElementAliases"][0].__setitem__(
            "practiceElementName", "Workspace Fabric"),
    ),
    (
        "xref:reference-integrity", "reference-without-links",
        "a reference carries no links, so there is nothing to open",
        lambda d: d["references"][0].__setitem__("links", []),
    ),

    # --- quality defects recorded as project feedback ---
    (
        "qual:citation-names", "author-date-citation-name",
        "memory: a citation is named Author (Year) instead of by its title",
        lambda d: d["citations"][0].__setitem__("name", "Skelton & Pais (2019)"),
    ),
    (
        "qual:narrative-citations", "narrative-without-citations",
        "memory: a narrative carries no citationNames",
        lambda d: d["narratives"][0].pop("citationNames"),
    ),
    (
        "qual:checklist-polarity", "negative-checklist",
        "memory: a checklist item is framed as an absence rather than an achievement",
        lambda d: _alpha(d, "Platform Onboarding")["states"][0]["checklist"][0].__setitem__(
            "name", "No team is blocked waiting on platform access"),
    ),
    (
        "qual:outcomes", "outcome-without-contributions",
        "memory: an extension practice outcome has neither metric nor objective contributions",
        lambda d: [(o.pop("metricContributions", None), o.pop("objectiveContributions", None))
                   for o in d["outcomes"]],
    ),
    (
        "qual:contributesto-targeting", "all-alphas-one-parent",
        "memory: Phase 2 agents default every new alpha to a single parent",
        lambda d: [
            _alpha(d, "Onboarding Readiness").__setitem__(
                "contributesTo", "Platform Consumption Interface"),
            _alpha(d, "Developer Workspace").pop("mapsTo"),
            _alpha(d, "Developer Workspace").__setitem__(
                "contributesTo", "Platform Consumption Interface"),
        ],
    ),
    (
        "qual:reference-quality", "unanchored-reference-url",
        "memory: a reference URL lacks both an anchor and a pages locator, so it lands on the front page",
        lambda d: (
            d["references"][0]["links"][0].__setitem__(
                "uri", "https://tag-app-delivery.cncf.io/whitepapers/platform-eng-maturity-model/"),
            d["references"][0]["links"][0].pop("pages", None),
        ),
    ),
    (
        "qual:pattern-progression", "pattern-single-step",
        "memory: an alpha appears in only one pattern view, so it shows no progression",
        lambda d: [v["alphaStates"].__delitem__(
            next(i for i, s in enumerate(v["alphaStates"])
                 if s["alphaName"] == "Developer Workspace"))
            for v in d["patterns"][0]["patternViews"][1:]],
    ),
    (
        "qual:description-length", "overlong-description",
        "an element description runs well past the word limit",
        lambda d: _alpha(d, "Platform Onboarding").__setitem__(
            "description",
            "The progression of a delivery team from its very first guided contact with the "
            "platform team and the platform itself, through a documented and repeatable "
            "onboarding path, all the way to entirely unaided self-service use of every "
            "capability the platform offers to its internal consumers."),
    ),
    (
        "qual:checklist-style", "participle-checklist-name",
        "a checklist name uses past-participle criteria phrasing instead of an action",
        lambda d: _alpha(d, "Platform Onboarding")["states"][0]["checklist"][0].__setitem__(
            "name", "Pilot onboarding completed"),
    ),
    (
        "qual:versioning", "missing-version",
        "the document declares no version or schemaVersion",
        lambda d: (d.pop("version", None), d.pop("schemaVersion", None)),
    ),
]
