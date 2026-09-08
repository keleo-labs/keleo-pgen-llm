#!/usr/bin/env python3
"""Apply REMAP changes to MEDDPICC Opportunity Qualification practice JSON.

Changes:
1. Trim descriptions to word limits (20 for elements, 12 for states/LODs)
2. Add workProductLevels to alpha state backgrounds
3. Add contributesToAlphaNames to work products
4. Add ledBy to activities
5. Update practice narrative contexts (trimmed)
"""

import json
import sys
import os

PRACTICE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "practices", "red-hat-customer-account-planning",
    "meddpicc-opportunity-qualification.json"
)


def apply_changes(practice):
    # 1. Update practice description
    practice["description"] = (
        "Structured deal qualification using eight dimensions to assess "
        "opportunity health throughout the sales cycle."
    )

    # 2. Update practice narrative contexts (trimmed versions from mapping guide)
    for narr in practice.get("narratives", []):
        if narr["name"] == "MEDDPICC Qualification Story":
            for ctx in narr["narrativeContexts"]:
                if ctx["narrativeElementName"] == "Situation":
                    ctx["context"] = (
                        "Sales organizations pursuing enterprise technology opportunities face "
                        "subjective deal assessments leading to inaccurate pipeline forecasting, "
                        "wasted pursuit resources, and missed opportunities to strengthen "
                        "qualification before competitive threats solidify. Without a shared "
                        "vocabulary and structured assessment framework, sellers and managers "
                        "evaluate deals through different lenses, creating misalignment that "
                        "compounds through the pipeline."
                    )
                elif ctx["narrativeElementName"] == "Task":
                    ctx["context"] = (
                        "The MEDDPICC framework provides eight complementary qualification "
                        "dimensions each with a cumulative Good/Better/Best scoring rubric and "
                        "a Rudimentary/Proficient/Exceptional quality assessment. The methodology "
                        "aligns these dimensions to Red Hat sales stages, creating stage-gate "
                        "expectations while recognizing that Economic Buyer and Champion "
                        "engagement are continuous throughout."
                    )
                elif ctx["narrativeElementName"] == "Action":
                    ctx["context"] = (
                        "Account teams apply MEDDPICC by systematically evaluating each dimension "
                        "against the rubric, documenting findings in the MEDDPICC Scorecard within "
                        "Red Hat Sales Cloud, identifying qualification gaps through the Guidance "
                        "for Missing Letters framework, and engaging specialist resources. Sales "
                        "managers conduct structured deal reviews using the three-phase workflow, "
                        "optionally augmented by PeopleAI/SalesAI for AI-prioritized focus areas. "
                        "The Business Value Framework connects Pain Identification to Metrics "
                        "through a quantified value narrative. Partner engagement extends "
                        "qualification depth across all dimensions."
                    )
                elif ctx["narrativeElementName"] == "Result":
                    ctx["context"] = (
                        "Organizations that systematically apply MEDDPICC achieve improved deal "
                        "qualification accuracy through evidence-based assessment, enhanced "
                        "pipeline predictability through structured multi-dimensional scoring, "
                        "increased deal velocity through targeted gap remediation guided by "
                        "specific coaching, and organizational alignment through a shared "
                        "qualification vocabulary. The Global Bookings Pipeline Procedure "
                        "reinforces this discipline by requiring completed scorecards for "
                        "threshold opportunities in Commit and Best Case forecast categories."
                    )

    # 3. Update alpha descriptions and state descriptions, add workProductLevels
    alpha_updates = {
        "Opportunity": {
            "description": (
                "A qualified prospect engagement progressing through defined stages "
                "toward commercial commitment and revenue forecasting."
            ),
            "states": {
                "Identified": {
                    "description": "Opportunity recognized and entered into pipeline tracking.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Initial Assessment"}
                    ]
                },
                "Qualified": {
                    "description": "Structured qualification confirms the opportunity merits investment.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Qualified Assessment"},
                        {"workProductName": "Business Value Assessment", "levelOfDetailName": "Pain Hypothesis"},
                        {"workProductName": "Deal Review Briefing", "levelOfDetailName": "Pre-Review Notes"}
                    ]
                },
                "Validated": {
                    "description": "Technical and business fit confirmed through structured validation.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Validated Assessment"},
                        {"workProductName": "Business Value Assessment", "levelOfDetailName": "Quantified Impact"},
                        {"workProductName": "Deal Review Briefing", "levelOfDetailName": "Structured Analysis"}
                    ]
                },
                "Committed": {
                    "description": "Formal proposal presented and customer has signaled commercial intent.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Coaching-Enhanced Assessment"},
                        {"workProductName": "Mutual Close Plan", "levelOfDetailName": "Agreed Milestones"},
                        {"workProductName": "Deal Review Briefing", "levelOfDetailName": "Action Plan"}
                    ]
                },
                "Won": {
                    "description": "Commercial agreement executed and opportunity transitions to fulfillment.",
                    "workProductLevels": [
                        {"workProductName": "Mutual Close Plan", "levelOfDetailName": "Active Tracking"}
                    ]
                },
                "Expanding": {
                    "description": "Won opportunity has generated follow-on expansion opportunities.",
                    "workProductLevels": None
                }
            }
        },
        "Value Proposition": {
            "description": (
                "The business case connecting technology solutions to measurable "
                "customer outcomes through hypothesis, validation, and proof."
            ),
            "states": {
                "Hypothesized": {
                    "description": "Value proposition constructed based on initial customer understanding.",
                    "workProductLevels": [
                        {"workProductName": "Business Value Assessment", "levelOfDetailName": "Pain Hypothesis"}
                    ]
                },
                "Articulated": {
                    "description": "Value proposition tested and refined through discovery conversations.",
                    "workProductLevels": None
                },
                "Validated": {
                    "description": "Business value expressed in measurable financial or operational terms.",
                    "workProductLevels": [
                        {"workProductName": "Business Value Assessment", "levelOfDetailName": "Quantified Impact"}
                    ]
                },
                "Compelling": {
                    "description": "Value claims supported by third-party validation and structured evidence.",
                    "workProductLevels": [
                        {"workProductName": "Business Value Assessment", "levelOfDetailName": "Validated Business Case"}
                    ]
                },
                "Proven": {
                    "description": "Delivered value tracked and communicated as ongoing partnership proof.",
                    "workProductLevels": None
                }
            }
        },
        "Customer": {
            "description": (
                "An organization targeted for commercial engagement, progressing "
                "through understanding, engagement, trust, and advocacy."
            ),
            "states": {
                "Targeted": {
                    "description": "Organization identified as a potential customer based on alignment.",
                    "workProductLevels": None
                },
                "Understood": {
                    "description": "Documented understanding of customer's business model and stakeholders.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Qualified Assessment"}
                    ]
                },
                "Engaged": {
                    "description": "Active dialogue with meaningful business and technical exchange.",
                    "workProductLevels": None
                },
                "Trusting": {
                    "description": "Relationship evolved to trusted advisory status.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Validated Assessment"}
                    ]
                },
                "Advocating": {
                    "description": "Customer actively champions solutions through references and recommendation.",
                    "workProductLevels": None
                }
            }
        },
        "Customer Relationship": {
            "description": (
                "The ongoing commercial and advisory partnership between seller "
                "and customer through strategic partnership."
            ),
            "states": {
                "Initiated": {
                    "description": "Initial contact established with the customer organization.",
                    "workProductLevels": None
                },
                "Developing": {
                    "description": "Regular engagement producing mutual value with expanding access.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Initial Assessment"}
                    ]
                },
                "Established": {
                    "description": "Active engagement and structured account management in place.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Qualified Assessment"}
                    ]
                },
                "Strategic": {
                    "description": "Strategic partnership with executive alignment evolved.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Validated Assessment"}
                    ]
                },
                "Transformational": {
                    "description": "Partnership drives measurable transformation with seller as advisor.",
                    "workProductLevels": None
                }
            }
        },
        "Deal": {
            "description": (
                "The commercial transaction from shaping through proposal, "
                "negotiation, closing, and renewal."
            ),
            "states": {
                "Shaped": {
                    "description": "Commercial structure defined with scope and pricing approach.",
                    "workProductLevels": None
                },
                "Proposed": {
                    "description": "Formal commercial proposal presented with scope and pricing.",
                    "workProductLevels": [
                        {"workProductName": "Mutual Close Plan", "levelOfDetailName": "Draft Timeline"}
                    ]
                },
                "Negotiated": {
                    "description": "Commercial terms actively negotiated with procurement and legal.",
                    "workProductLevels": [
                        {"workProductName": "Mutual Close Plan", "levelOfDetailName": "Agreed Milestones"}
                    ]
                },
                "Closed": {
                    "description": "Commercial agreement executed, entitlements provisioned.",
                    "workProductLevels": [
                        {"workProductName": "Mutual Close Plan", "levelOfDetailName": "Active Tracking"}
                    ]
                },
                "Renewed": {
                    "description": "Commercial relationship renewed with maintained or expanded scope.",
                    "workProductLevels": None
                }
            }
        },
        "Solution Fit": {
            "description": (
                "Alignment between technology capabilities and customer requirements "
                "through exploration, demonstration, and confirmation."
            ),
            "states": {
                "Explored": {
                    "description": "Initial solution alignment exploration with candidate products identified.",
                    "workProductLevels": None
                },
                "Scoped": {
                    "description": "Customer technical requirements systematically documented.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Qualified Assessment"}
                    ]
                },
                "Designed": {
                    "description": "Technical architecture maps products to customer requirements.",
                    "workProductLevels": None
                },
                "Demonstrated": {
                    "description": "Solution proven through demonstration, POC, or reference validation.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Validated Assessment"}
                    ]
                },
                "Confirmed": {
                    "description": "Solution refined to implementation-grade detail with deployment planned.",
                    "workProductLevels": None
                }
            }
        },
        "Competitive Position": {
            "description": (
                "Differentiated standing relative to alternative solutions "
                "in a customer evaluation context."
            ),
            "states": {
                "Assessed": {
                    "description": "Initial competitive landscape assessment conducted.",
                    "workProductLevels": None
                },
                "Mapped": {
                    "description": "Competitors identified with positions catalogued and documented.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Qualified Assessment"}
                    ]
                },
                "Differentiated": {
                    "description": "Unique value expressed in customer-relevant terms.",
                    "workProductLevels": None
                },
                "Defended": {
                    "description": "Competitive challenges addressed with evidence-based responses.",
                    "workProductLevels": [
                        {"workProductName": "MEDDPICC Scorecard", "levelOfDetailName": "Validated Assessment"}
                    ]
                },
                "Preferred": {
                    "description": "Seller selected as preferred vendor with alternatives excluded.",
                    "workProductLevels": None
                }
            }
        }
    }

    for alpha in practice.get("alphas", []):
        if alpha["name"] in alpha_updates:
            updates = alpha_updates[alpha["name"]]
            alpha["description"] = updates["description"]
            for state in alpha.get("states", []):
                if state["name"] in updates["states"]:
                    state_upd = updates["states"][state["name"]]
                    state["description"] = state_upd["description"]
                    wpl = state_upd.get("workProductLevels")
                    if wpl:
                        if "background" not in state:
                            state["background"] = {}
                        state["background"]["workProductLevels"] = wpl
                    # Remove workProductLevels if it was None and previously existed
                    # (shouldn't happen in this case but safe)

    # 4. Add contributesToAlphaNames to work products
    wp_contrib = {
        "MEDDPICC Scorecard": ["Opportunity"],
        "Business Value Assessment": ["Value Proposition"],
        "Deal Review Briefing": ["Opportunity"],
        "Mutual Close Plan": ["Deal"],
    }

    for wp in practice.get("workProducts", []):
        if wp["name"] in wp_contrib:
            wp["contributesToAlphaNames"] = wp_contrib[wp["name"]]

    # 5. Update work product descriptions (trimmed)
    wp_descs = {
        "MEDDPICC Scorecard": "Structured assessment tracking qualification across all eight MEDDPICC dimensions.",
        "Business Value Assessment": "Quantified analysis linking customer pain to measurable outcomes via the Business Value Framework.",
        "Deal Review Briefing": "Coaching preparation combining deal analysis with AI-prioritized insights for structured reviews.",
        "Mutual Close Plan": "Jointly owned timeline tracking decision milestones and paper process steps.",
    }

    for wp in practice.get("workProducts", []):
        if wp["name"] in wp_descs:
            wp["description"] = wp_descs[wp["name"]]

    # 6. Add ledBy to activities and update descriptions
    activity_ledby = {
        "Identify and Articulate Customer Pain": "Account Executive",
        "Build Business Value Case": "Business Value Consultant",
        "Identify and Engage Economic Buyer": "Account Executive",
        "Develop and Validate Champion": "Account Executive",
        "Define Decision Criteria": "Solution Architect",
        "Map Decision Process": "Account Executive",
        "Navigate Paper Process": "Account Executive",
        "Assess and Counter Competition": "Account Executive",
        "Conduct MEDDPICC Deal Review": "Sales Manager",
    }

    activity_descs = {
        "Identify and Articulate Customer Pain": (
            "Structured discovery to uncover and articulate customer challenges and impact."
        ),
        "Build Business Value Case": (
            "Quantifying outcomes and building the financial case linking pain to metrics."
        ),
        "Identify and Engage Economic Buyer": (
            "Identifying budget authority and establishing sustained engagement for purchasing commitment."
        ),
        "Develop and Validate Champion": (
            "Identifying, cultivating, and strengthening an internal advocate within the customer."
        ),
        "Define Decision Criteria": (
            "Understanding, documenting, and proactively shaping customer vendor evaluation requirements."
        ),
        "Map Decision Process": (
            "Mapping customer buying process steps, identifying stakeholders, and aligning to timeline."
        ),
        "Navigate Paper Process": (
            "Navigating procurement, legal, contracting, and signature workflows for deal execution."
        ),
        "Assess and Counter Competition": (
            "Identifying all competitive threats and developing differentiated positioning."
        ),
        "Conduct MEDDPICC Deal Review": (
            "Leading structured deal reviews with scoring, coaching, and AI-augmented prioritization."
        ),
    }

    for activity in practice.get("activities", []):
        if activity["name"] in activity_ledby:
            activity["ledBy"] = activity_ledby[activity["name"]]
        if activity["name"] in activity_descs:
            activity["description"] = activity_descs[activity["name"]]

    # 7. Remove spurious "kind" properties from elements
    # The schema doesn't support "kind" on alphas, activities, patterns, etc.
    # These were incorrectly added and should be removed
    for alpha in practice.get("alphas", []):
        alpha.pop("kind", None)
    for activity in practice.get("activities", []):
        activity.pop("kind", None)
    for pattern in practice.get("patterns", []):
        pattern.pop("kind", None)
    for citation in practice.get("citations", []):
        citation.pop("kind", None)

    return practice


def main():
    with open(PRACTICE_PATH, "r", encoding="utf-8") as f:
        practice = json.load(f)

    practice = apply_changes(practice)

    with open(PRACTICE_PATH, "w", encoding="utf-8") as f:
        json.dump(practice, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {PRACTICE_PATH}")
    print("Changes applied:")
    print("  - Practice description trimmed")
    print("  - Practice narrative contexts updated")
    print("  - Alpha descriptions trimmed (max 20 words)")
    print("  - State descriptions trimmed (max 12 words)")
    print("  - workProductLevels added to state backgrounds")
    print("  - contributesToAlphaNames added to work products")
    print("  - Work product descriptions updated")
    print("  - ledBy added to all activities")
    print("  - Activity descriptions trimmed")
    print("  - Spurious 'kind' properties removed from elements")


if __name__ == "__main__":
    main()
