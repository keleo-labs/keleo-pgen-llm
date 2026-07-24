#!/usr/bin/env python3
"""Fix narrative names, descriptions, and citation references.

Addresses three issues:
1. Names that reference narrative type templates (e.g., "The STAR narrative for...")
2. Descriptions that expose narrative mechanics instead of describing subject matter
3. Missing citationNames on narratives

Usage:
    # Dry run — show what would be changed
    python3 utils/fix-narrative-metadata.py <file.json>

    # Apply fixes in-place
    python3 utils/fix-narrative-metadata.py <file.json> --fix

Output: JSON report to stdout.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


NARRATIVE_TYPE_PATTERNS = [
    r"\bSTAR\b",
    r"\bThree-Act\b",
    r"\bThree Act\b",
    r"\bHero'?s Journey\b",
    r"\bABT\b",
    r"\bStoryBrand\b",
    r"\bEssay\b",
    r"\bmicro-narrative\b",
    r"\btransformation journey narrative\b",
]

SELF_REF_PATTERNS = [
    r"^The \w+ narrative for ",
    r"^The \w+ \w+ narrative for ",
    r"^The transformation journey narrative for ",
    r"narrative for the .+ alpha",
    r"narrative for the .+ competency",
    r"narrative for the .+ activity space",
]


NARRATIVE_REWRITES = {
    "Digital Transformation Essentials Baseline Narrative": {
        "name": "End-to-End Digital Transformation",
        "description": "How organizations progress from initial strategic awareness through sustained adaptive capability across strategic, technological, organizational, and ethical dimensions.",
        "citationNames": [
            "Teece (2007)", "Ross et al. (2019)", "Leinwand and Mani (2021)",
            "Kotter (2014)", "Vargo and Lusch (2016)", "Nieto-Rodriguez (2014)",
            "Brown (2021)", "University of Exeter (2026)",
        ],
    },
    "Digital Strategy Narrative": {
        "name": "From Reactive to Adaptive Strategy",
        "description": "How organizations evolve from uncoordinated digital initiatives to continuously adaptive strategy with embedded dynamic capabilities for sensing, seizing, and transforming.",
        "citationNames": [
            "Teece (2007)", "Teece (2010)", "Ross (2014)",
            "Leinwand and Mani (2021)", "Brown (2021)",
        ],
    },
    "Business Model Narrative": {
        "name": "Pipeline to Platform Transition",
        "description": "How organizations facing competitive pressure from platform-native competitors design, prototype, validate, and scale alternative business models through structured experimentation.",
        "citationNames": [
            "Osterwalder (2010)", "Parker et al. (2016)", "Choudhary (2013)",
            "Cusumano et al. (2020)", "Blank (2015)",
        ],
    },
    "Customer Value Delivery Narrative": {
        "name": "From Product-Centric to Value Co-Creation",
        "description": "How organizations bridge the disconnect between outputs delivered and outcomes achieved, progressing from product-centric delivery to platform-mediated value co-creation with customers as active partners.",
        "citationNames": [
            "Vargo and Lusch (2016)", "Ng et al. (2015)",
            "Tukker (2004)", "Furr and Shipilov (2019)",
        ],
    },
    "Digital Infrastructure Narrative": {
        "name": "Architectural Modernization Path",
        "description": "How organizations progress from monolithic legacy systems through dual-backbone architecture to composable, cloud-native infrastructure enabling ecosystem-scale agility.",
        "citationNames": [
            "Ross et al. (2019)", "Google Cloud (2020)",
            "Benzell et al. (2017)", "Brown (2021)",
        ],
    },
    "Data Capital Narrative": {
        "name": "Data as Strategic Capital",
        "description": "How organizations transform disconnected data silos into strategically managed assets generating intelligence, competitive advantage, and new revenue streams within ethical stewardship boundaries.",
        "citationNames": [
            "DalleMule and Davenport (2017)", "Davenport and Ronanki (2018)",
            "AI Index Report 2026",
        ],
    },
    "Platform Ecosystem Narrative": {
        "name": "Building Multi-Sided Platform Ecosystems",
        "description": "How pipeline-based organizations facing existential pressure from platform-native competitors progressively build and orchestrate multi-sided ecosystems with self-reinforcing network effects.",
        "citationNames": [
            "Parker et al. (2016)", "Gawer (2010)",
            "Cusumano et al. (2020)", "Helfat and Raubitschek (2018)",
        ],
    },
    "Organizational Capability Narrative": {
        "name": "Agile Organizational Transformation",
        "description": "How hierarchical organizations with functional silos transform into agile, cross-functional, value-oriented team topologies enabling rapid decision-making at enterprise scale.",
        "citationNames": [
            "Birkinshaw (2017)", "Kotter (2014)",
            "Westerman et al. (2019)", "Brown (2021)",
        ],
    },
    "Digital Culture Narrative": {
        "name": "Cultivating Digital-Ready Culture",
        "description": "How organizations overcome risk aversion, blame culture, and hierarchy dependency to embed digital values of impact, speed, openness, and autonomy into daily behaviours.",
        "citationNames": [
            "Westerman et al. (2019)", "Brown (2020)",
            "Kotter (2014)", "University of Exeter (2026)",
        ],
    },
    "Transformation Leadership Narrative": {
        "name": "Leading Through the Frozen Middle",
        "description": "How leadership teams developed for predictability and control transition to empowerment-driven transformation, overcoming the frozen middle through dual operating systems, psychological safety, and distributed capability.",
        "citationNames": [
            "Kotter (2014)", "Nieto-Rodriguez (2014)",
            "Brown (2021)", "University of Exeter (2026)",
        ],
    },
    "Innovation Capability Narrative": {
        "name": "Overcoming Destructive Innovation Patterns",
        "description": "How organizations confront the five destructive patterns of Theatre, Tourism, Inquisition, Ghettos, and Fatigue to build innovation as a governed capability with three-horizon portfolio management.",
        "citationNames": [
            "Blank (2015)", "Kelley (2005)",
            "Nieto-Rodriguez (2014)", "University of Exeter (2026)",
        ],
    },
    "Responsible Digital Governance Narrative": {
        "name": "From Compliance to Ethical Leadership",
        "description": "How organizations progress from recognizing surveillance capitalism dynamics and algorithmic bias risks to proactive ethical leadership that anticipates emerging challenges and demonstrates positive societal impact.",
        "citationNames": [
            "Floridi (2018)", "Zuboff (2019)", "Crawford (2021)",
            "Mateescu and Nguyen (2019)", "University of Exeter (2026)",
        ],
    },
    "Digital Security Narrative": {
        "name": "Building Digital Resilience",
        "description": "How organizations build security architecture and resilience across expanding cloud, edge, API, and ecosystem boundaries while enabling rather than impeding transformation speed.",
        "citationNames": [
            "Furnell (2026)", "Schwab (2016)", "University of Exeter (2026)",
        ],
    },
    "Formulate Transformation Strategy Narrative": {
        "name": "Strategy Formulation Process",
        "description": "How organizations move from uncoordinated digital initiatives to a living strategy with dynamic capabilities embedded in organizational routines and continuous market sensing.",
        "citationNames": [
            "Teece (2007)", "Ross (2014)", "Brown (2021)",
        ],
    },
    "Lead and Sustain Change Narrative": {
        "name": "Change Leadership Lifecycle",
        "description": "How change leaders assess the frozen middle, build innovation governance with three-horizon portfolio management, and embed continuous transformation as a permanent organizational state.",
        "citationNames": [
            "Kotter (2014)", "Nieto-Rodriguez (2014)",
            "Blank (2015)", "University of Exeter (2026)",
        ],
    },
    "Ensure Responsible Operations Narrative": {
        "name": "Responsible Operations Framework",
        "description": "How organizations close the growing gap between technological capability and ethical governance across surveillance capitalism, algorithmic bias, workforce displacement, and environmental costs.",
        "citationNames": [
            "Floridi (2018)", "Zuboff (2019)", "Crawford (2021)",
            "De Stefano (2016)", "Forde et al. (2017)",
        ],
    },
    "Design Customer Experiences Narrative": {
        "name": "Customer Experience Transformation",
        "description": "How organizations transform from product-feature definitions of value to customer-outcome-oriented delivery through journey mapping, value destroyer elimination, and platform-mediated co-creation.",
        "citationNames": [
            "Vargo and Lusch (2016)", "Ng et al. (2015)", "Tukker (2004)",
        ],
    },
    "Govern and Leverage Data Narrative": {
        "name": "Data Governance and Monetization",
        "description": "How organizations progress from disconnected data silos to self-optimizing data systems with AI-augmented decision-making and data-derived revenue within ethical stewardship boundaries.",
        "citationNames": [
            "DalleMule and Davenport (2017)", "Davenport and Ronanki (2018)",
            "AI Index Report 2026",
        ],
    },
    "Strategic Thinking Narrative": {
        "name": "Strategic Capability Development",
        "description": "How leaders develop capability to formulate, communicate, and continuously adapt strategy, progressing from basic concepts through dynamic capabilities mastery to shaping industry strategic direction.",
        "citationNames": [
            "Teece (2007)", "Teece (2010)", "Ross (2014)",
        ],
    },
    "Business Model and Service Design Narrative": {
        "name": "Business Model Design Capability",
        "description": "Why deep capability in multi-sided platform design, outcome-based delivery, and product-service system development is essential despite widely available frameworks, given the complexity of the servitization paradox and commercial failure patterns.",
        "citationNames": [
            "Osterwalder (2010)", "Neely (2008)", "Neely (2013)",
            "Roos (2014)", "Baines et al. (2017)", "Tukker (2004)",
        ],
    },
    "Technology Architecture Narrative": {
        "name": "Architecture Capability Imperative",
        "description": "Why deep architectural expertise is critical given that the most common strategic failure is attempting digital services innovation without first establishing a reliable operational backbone.",
        "citationNames": [
            "Ross et al. (2019)", "Google Cloud (2020)",
            "Benzell et al. (2017)",
        ],
    },
    "Organizational Change Leadership Narrative": {
        "name": "Change Leadership Capability Path",
        "description": "How change leadership develops from basic stakeholder management through enterprise-wide transformation leadership to building permanent organizational change capability that integrates ethical responsibility with transformation ambition.",
        "citationNames": [
            "Kotter (2014)", "Nieto-Rodriguez (2014)",
            "Birkinshaw (2017)", "University of Exeter (2026)",
        ],
    },
    "Regulatory and Ethical Governance Narrative": {
        "name": "Governance Expertise Development",
        "description": "How governance expertise develops from basic compliance through multi-jurisdictional complexity to proactive ethical strategy, grounded in Floridi's soft ethics framework and informed by surveillance capitalism critique.",
        "citationNames": [
            "Floridi (2018)", "Zuboff (2019)", "Crawford (2021)",
            "De Stefano (2016)", "Forde et al. (2017)",
            "Mateescu and Nguyen (2019)",
        ],
    },
}


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def has_self_reference(name, description, type_patterns=NARRATIVE_TYPE_PATTERNS, self_ref_patterns=SELF_REF_PATTERNS):
    """Check if name or description references narrative type mechanics."""
    text = f"{name} {description}"
    for pattern in type_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    for pattern in self_ref_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return True
    return False


def collect_all_narratives(data):
    """Collect all narratives from all locations in the data."""
    narratives = []
    for n in data.get("narratives", []):
        narratives.append(("top-level", None, n))

    for coll_key in ("alphas", "activitySpaces", "competencies"):
        for elem in data.get(coll_key, []):
            for n in elem.get("narratives", []):
                narratives.append((coll_key, elem.get("name"), n))

    return narratives


def fix_narrative_metadata(data, dry_run=True):
    """Fix narrative names, descriptions, and add citationNames."""
    all_narrs = collect_all_narratives(data)
    citation_names = [c.get("name") for c in data.get("citations", []) if c.get("name")]

    changes = []

    for location, parent_name, narrative in all_narrs:
        old_name = narrative.get("name", "")
        rewrite = NARRATIVE_REWRITES.get(old_name)

        if rewrite:
            change = {
                "location": f"{location}:{parent_name}" if parent_name else location,
                "oldName": old_name,
                "newName": rewrite["name"],
                "oldDescription": narrative.get("description", ""),
                "newDescription": rewrite["description"],
                "citationNames": rewrite["citationNames"],
            }
            changes.append(change)

            if not dry_run:
                narrative["name"] = rewrite["name"]
                narrative["description"] = rewrite["description"]
                valid_citations = [c for c in rewrite["citationNames"] if c in citation_names]
                narrative["citationNames"] = valid_citations
        elif not narrative.get("citationNames") and citation_names:
            change = {
                "location": f"{location}:{parent_name}" if parent_name else location,
                "oldName": old_name,
                "issue": "missing citationNames (no rewrite defined)",
            }
            changes.append(change)

    return {
        "totalNarratives": len(all_narrs),
        "rewrites": len([c for c in changes if "newName" in c]),
        "citationOnlyFixes": len([c for c in changes if "issue" in c]),
        "changes": changes,
        "dryRun": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(description="Fix narrative names, descriptions, and citations")
    parser.add_argument("file", help="Practice/baseline JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    args = parser.parse_args()

    path = Path(args.file)
    data = load_json(path)

    result = fix_narrative_metadata(data, dry_run=not args.fix)

    if args.fix and result["rewrites"] > 0:
        save_json_file(path, data)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
