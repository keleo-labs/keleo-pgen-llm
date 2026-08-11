#!/usr/bin/env python3
"""
Update practice JSONs to clearly distinguish vendor vs partner responsibilities.

Adds vendor-side personas, fixes persona group composition, and updates
activity 'involves' assignments to reflect which side performs what.
"""
import json
import sys
from pathlib import Path


def update_practice_1(data):
    """Update Partner Engagement & Lifecycle practice."""

    # --- Personas ---
    existing_names = {p["name"] for p in data.get("personas", [])}

    new_vendor_personas = [
        {
            "name": "Vendor Channel Program Director",
            "description": "Vendor-side executive responsible for designing, evolving, and governing the overall partner program framework, tier structure, and incentive architecture.",
            "competencies": [
                {"competencyName": "Partner Governance", "competencyLevelName": "Adapts"},
                {"competencyName": "Partner Strategic Alignment", "competencyLevelName": "Masters"},
                {"competencyName": "Partner Value Assessment", "competencyLevelName": "Masters"},
            ],
            "tags": {
                "domainTags": ["partner-program", "channel-strategy"],
                "lifecycleTags": ["program-design"],
                "organizationalTags": ["vendor-leadership"],
            },
        },
        {
            "name": "Vendor Partner Development Manager",
            "description": "Vendor-side role responsible for enabling partner capability growth through training programs, certification pathways, and specialization guidance.",
            "competencies": [
                {"competencyName": "Sales Enablement", "competencyLevelName": "Masters"},
                {"competencyName": "Partner Relationship Management", "competencyLevelName": "Applies"},
                {"competencyName": "Partner Value Assessment", "competencyLevelName": "Applies"},
            ],
            "tags": {
                "domainTags": ["partner-enablement", "capability-development"],
                "lifecycleTags": ["enablement"],
                "organizationalTags": ["vendor-operations"],
            },
        },
        {
            "name": "Vendor Channel Operations Analyst",
            "description": "Vendor-side operational role managing program compliance monitoring, performance analytics, tier calculations, and incentive processing.",
            "competencies": [
                {"competencyName": "Partner Governance", "competencyLevelName": "Applies"},
                {"competencyName": "Partner Value Assessment", "competencyLevelName": "Applies"},
            ],
            "tags": {
                "domainTags": ["program-operations", "compliance"],
                "lifecycleTags": ["operations"],
                "organizationalTags": ["vendor-operations"],
            },
        },
    ]

    for p in new_vendor_personas:
        if p["name"] not in existing_names:
            data["personas"].append(p)

    # Update existing persona descriptions for clarity
    for p in data["personas"]:
        if p["name"] == "Partner Program Manager":
            p["description"] = "Partner-side role managing the partner organization's program participation, module selection, compliance submissions, and performance tracking within the vendor ecosystem."
        elif p["name"] == "Partner Executive Sponsor":
            p["description"] = "Partner-side executive providing strategic direction, investment commitment, and organizational sponsorship for the vendor-partner relationship."
        elif p["name"] == "Vendor Partner Account Manager":
            p["description"] = "Vendor-side relationship manager dedicated to managing a specific partner account, coordinating vendor resources, and driving mutual business outcomes."
        elif p["name"] == "Partner Seller":
            p["description"] = "Partner-side sales role responsible for selling vendor technology solutions to end customers, completing required sales training, and meeting revenue targets."
        elif p["name"] == "Partner Technical Seller":
            p["description"] = "Partner-side pre-sales technical role supporting customer evaluations with vendor technology demonstrations, proof-of-concept engagements, and solution design."

    # --- Persona Groups ---
    for pg in data["personaGroups"]:
        if pg["name"] == "Partner Alliance Management Team":
            pg["description"] = "Partner-side cross-functional team managing the organization's vendor relationship, program compliance, and strategic direction."
        elif pg["name"] == "Vendor Partner Management Team":
            pg["description"] = "Vendor-side team responsible for designing partner programs, managing partner relationships, enabling partner capabilities, and operating ecosystem infrastructure."
            pg["personaNames"] = [
                "Vendor Partner Account Manager",
                "Vendor Channel Program Director",
                "Vendor Partner Development Manager",
                "Vendor Channel Operations Analyst",
            ]

    # --- Activities: update involves and descriptions ---
    activity_updates = {
        "Onboard Partner Organization": {
            "description": "Vendor enrolls a new partner organization into the ecosystem program while the partner selects modules, completes initial training, and configures their program participation.",
            "involves": ["Partner Alliance Management Team", "Vendor Partner Management Team"],
        },
        "Develop Partner Capabilities": {
            "description": "Vendor provides structured training curricula, credentialing infrastructure, and certification programs while partner personnel complete learning paths and earn credentials.",
            "involves": ["Partner Alliance Management Team", "Vendor Partner Management Team"],
        },
        "Pursue Partner Specialization": {
            "description": "Partner organization builds and demonstrates deep expertise in a specific technology domain while the vendor validates achievement criteria and grants specialization recognition.",
            "involves": ["Partner Alliance Management Team", "Vendor Partner Management Team"],
        },
        "Manage Partner Compliance": {
            "description": "Partner completes annual compliance requirements including training renewals and code of conduct attestation while the vendor monitors compliance status and enforces program rules.",
            "involves": ["Partner Alliance Management Team", "Vendor Partner Management Team"],
        },
        "Deliver Lifecycle Rewards Activity": {
            "description": "Partner executes funded technical activities (PoCs, solution builds, workshops) and submits proof-of-performance claims while the vendor validates activity completion and processes reward payments.",
            "involves": ["Partner Alliance Management Team", "Vendor Partner Management Team"],
        },
        "Manage Ecosystem Awards and Recognition": {
            "description": "Vendor identifies, evaluates, and celebrates exceptional partner contributions through ecosystem innovation awards, with partners nominating candidates and providing evidence of impact.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Design Program Framework": {
            "description": "Vendor defines the modular program architecture, engagement motions, activity catalog, and point values that structure ecosystem operations for all partner types.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Evolve Program Operations": {
            "description": "Vendor adapts program architecture, activity recognition rules, and operational processes based on ecosystem performance data and market evolution.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Configure Activity Recognition": {
            "description": "Vendor establishes the activity tracking infrastructure including point submission workflows, validation rules, and aggregation systems that partners use to record contributions.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Establish Tier Framework": {
            "description": "Vendor defines tier structure, point thresholds, training requirements, and benefit allocations that determine partner standing levels across the ecosystem.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Calibrate Tier and Benefits": {
            "description": "Vendor adjusts tier thresholds, training requirements, and benefit allocations based on multi-year ecosystem data and competitive positioning of the partner program.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Design Capability Pathways": {
            "description": "Vendor establishes training tracks, credential programs, certification infrastructure, and learning path guidance that partners follow for capability development.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Assess Capability Impact": {
            "description": "Vendor measures the business impact of partner capability development on customer outcomes while partners provide performance data and customer satisfaction evidence.",
            "involves": ["Vendor Partner Management Team", "Partner Alliance Management Team"],
        },
        "Structure Financial Incentives": {
            "description": "Vendor designs incentive mechanisms including deal registration discounts, rebate structures, market development funds, and lifecycle rewards with eligibility criteria that partners access based on tier standing.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Deploy Partner Digital Platform": {
            "description": "Vendor establishes the digital infrastructure providing partner portal, activity tracking tools, training platform, and discovery services that partners use for self-service program engagement.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Enhance Digital Self-Service": {
            "description": "Vendor advances digital platform capabilities from basic tool access through autonomous self-service, while partners provide usage feedback and integration requirements.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Define Specialization Framework": {
            "description": "Vendor establishes technology domain definitions, achievement criteria, and validation processes that partners must meet to earn and maintain specialization designations.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Strengthen Ecosystem Trust": {
            "description": "Vendor deepens the compliance framework through transparent enforcement and brand protection standards while partners maintain adherence and report ecosystem integrity concerns.",
            "involves": ["Vendor Partner Management Team"],
        },
        "Curate Ecosystem Catalog": {
            "description": "Vendor manages ecosystem discovery platforms including partner finder and solution catalog while partners maintain their catalog listings, capability profiles, and solution descriptions.",
            "involves": ["Vendor Partner Management Team", "Partner Alliance Management Team"],
        },
    }

    for act in data.get("activities", []):
        if act["name"] in activity_updates:
            updates = activity_updates[act["name"]]
            act["description"] = updates["description"]
            act["involves"] = updates["involves"]

    return data


def update_practice_2(data):
    """Update Partner Go-to-Market Execution practice."""

    # --- Personas ---
    existing_names = {p["name"] for p in data.get("personas", [])}

    new_vendor_personas = [
        {
            "name": "Vendor Channel Sales Manager",
            "description": "Vendor-side sales role supporting partner co-selling activities, coordinating vendor specialist resources, and facilitating deal advancement for partner-sourced opportunities.",
            "competencies": [
                {"competencyName": "Deal Orchestration", "competencyLevelName": "Masters"},
                {"competencyName": "Relationship Building", "competencyLevelName": "Applies"},
                {"competencyName": "Partner Sales Acumen", "competencyLevelName": "Advanced"},
            ],
            "tags": {
                "domainTags": ["co-selling", "deal-support"],
                "lifecycleTags": ["sales-execution"],
                "organizationalTags": ["vendor-sales"],
            },
        },
        {
            "name": "Vendor Channel Marketing Manager",
            "description": "Vendor-side marketing role providing campaign assets, co-branding guidance, MDF approval, and demand generation program support to partner marketing teams.",
            "competencies": [
                {"competencyName": "Sales Enablement", "competencyLevelName": "Masters"},
                {"competencyName": "Market Development", "competencyLevelName": "Advanced"},
                {"competencyName": "Value Articulation", "competencyLevelName": "Applies"},
            ],
            "tags": {
                "domainTags": ["partner-marketing", "demand-generation"],
                "lifecycleTags": ["marketing"],
                "organizationalTags": ["vendor-marketing"],
            },
        },
        {
            "name": "Vendor Deal Desk Analyst",
            "description": "Vendor-side operational role responsible for processing deal registrations, validating eligibility, approving discount structures, and managing deal protection periods.",
            "competencies": [
                {"competencyName": "Deal Orchestration", "competencyLevelName": "Applies"},
                {"competencyName": "Channel Operations", "competencyLevelName": "Advanced"},
            ],
            "tags": {
                "domainTags": ["deal-management", "operations"],
                "lifecycleTags": ["deal-processing"],
                "organizationalTags": ["vendor-operations"],
            },
        },
    ]

    for p in new_vendor_personas:
        if p["name"] not in existing_names:
            data["personas"].append(p)

    # Update existing persona descriptions for clarity
    for p in data["personas"]:
        if p["name"] == "Partner Seller":
            p["description"] = "Partner-side sales role responsible for executing vendor sales plays with end customers, registering deals, and driving vendor technology revenue through the partner channel."
        elif p["name"] == "Partner Technical Seller":
            p["description"] = "Partner-side pre-sales technical role delivering customer demonstrations, proof-of-concept engagements, and technical assessments using vendor technology and methodologies."
        elif p["name"] == "Partner Marketing Manager":
            p["description"] = "Partner-side marketing role planning and executing co-branded demand generation campaigns, managing MDF claims, and driving lead generation for vendor solutions."
        elif p["name"] == "Partner Program Manager":
            p["description"] = "Partner-side operational role managing deal registration submissions, incentive claims, compliance documentation, and program reporting within GTM execution."
        elif p["name"] == "Partner Solution Architect":
            p["description"] = "Partner-side technical design role creating integrated solutions combining vendor technology with partner domain expertise for customer engagements."
        elif p["name"] == "Vendor Partner Account Manager":
            p["description"] = "Vendor-side relationship manager responsible for partner development, performance tracking, GTM alignment, and coordinating vendor resources for partner-led opportunities."

    # --- Persona Groups ---
    # Add new vendor GTM support team
    existing_group_names = {pg["name"] for pg in data.get("personaGroups", [])}

    if "Vendor GTM Support Team" not in existing_group_names:
        data["personaGroups"].append({
            "name": "Vendor GTM Support Team",
            "description": "Vendor-side team providing marketing assets, deal processing, co-selling support, and GTM program management to enable partner go-to-market execution.",
            "personaNames": [
                "Vendor Partner Account Manager",
                "Vendor Channel Sales Manager",
                "Vendor Channel Marketing Manager",
                "Vendor Deal Desk Analyst",
            ],
            "tags": {
                "domainTags": ["vendor-gtm-support"],
                "lifecycleTags": ["sales-enablement"],
                "organizationalTags": ["vendor-operations"],
            },
        })

    # Update existing groups
    for pg in data["personaGroups"]:
        if pg["name"] == "Partner GTM Execution Team":
            pg["description"] = "Partner-side cross-functional team responsible for executing vendor sales plays, running demand generation campaigns, managing deals, and delivering technical engagements to end customers."
        elif pg["name"] == "Joint GTM Alignment Team":
            pg["description"] = "Combined vendor-partner team responsible for aligning GTM strategy, coordinating co-selling motions, reviewing pipeline performance, and optimizing partner GTM outcomes."
            pg["personaNames"] = [
                "Vendor Partner Account Manager",
                "Vendor Channel Sales Manager",
                "Partner Seller",
                "Partner Marketing Manager",
                "Partner Program Manager",
            ]

    # --- Activities ---
    activity_updates = {
        "Execute Partner Demand Campaign": {
            "description": "Partner marketing team plans and executes co-branded demand generation campaigns while the vendor provides campaign assets, co-branding approval, and MDF funding support.",
            "involves": ["Partner GTM Execution Team", "Vendor GTM Support Team"],
        },
        "Register Partner Deal": {
            "description": "Partner seller identifies and registers a sales opportunity through the vendor deal registration system, while the vendor deal desk validates eligibility, approves discount structures, and activates deal protection.",
            "involves": ["Partner GTM Execution Team", "Vendor GTM Support Team"],
        },
        "Execute Partner Sales Play": {
            "description": "Partner sales team translates vendor-defined sales play guides into customer engagements while the vendor provides co-selling support, specialist resources, and competitive positioning guidance.",
            "involves": ["Partner GTM Execution Team", "Joint GTM Alignment Team"],
        },
        "Deliver Partner Technical Activity": {
            "description": "Partner technical sellers execute funded technical activities (PoCs, solution builds, workshops, assessments) for end customers while the vendor provides lab environments, technical content, and lifecycle rewards funding.",
            "involves": ["Partner GTM Execution Team", "Vendor GTM Support Team"],
        },
        "Manage Partner Deal Lifecycle": {
            "description": "Partner manages subscription renewals and expansion opportunities within registered deals while the vendor tracks deal status, processes incentive claims, and coordinates renewal support.",
            "involves": ["Partner GTM Execution Team", "Joint GTM Alignment Team"],
        },
        "Measure Partner GTM Performance": {
            "description": "Vendor tracks partner GTM execution metrics across demand generation, deal pipeline, and technical collaboration while partners provide campaign results, deal outcomes, and customer satisfaction data.",
            "involves": ["Joint GTM Alignment Team", "Vendor GTM Support Team"],
        },
    }

    for act in data.get("activities", []):
        if act["name"] in activity_updates:
            updates = activity_updates[act["name"]]
            act["description"] = updates["description"]
            act["involves"] = updates["involves"]

    # Update activity requiredCompetencies and recommendedCompetencyLevels
    # for activities that now involve vendor teams
    # (The existing competency references are still valid — vendor personas
    # share the same competency pool)

    return data


def main():
    p1_path = Path("practices/red-hat-partner-ecosystem-foundations/partner-engagement-lifecycle.json")
    p2_path = Path("practices/red-hat-partner-ecosystem-foundations/partner-go-to-market-execution.json")

    # Practice 1
    with open(p1_path) as f:
        p1 = json.load(f)
    p1 = update_practice_1(p1)
    with open(p1_path, "w") as f:
        json.dump(p1, f, indent=2, ensure_ascii=False)
    print(f"Updated {p1_path}")
    print(f"  Personas: {len(p1['personas'])}")
    print(f"  Persona Groups: {len(p1['personaGroups'])}")
    joint_activities = sum(1 for a in p1["activities"] if len(a.get("involves", [])) > 1)
    print(f"  Activities with joint involvement: {joint_activities}/{len(p1['activities'])}")

    # Practice 2
    with open(p2_path) as f:
        p2 = json.load(f)
    p2 = update_practice_2(p2)
    with open(p2_path, "w") as f:
        json.dump(p2, f, indent=2, ensure_ascii=False)
    print(f"\nUpdated {p2_path}")
    print(f"  Personas: {len(p2['personas'])}")
    print(f"  Persona Groups: {len(p2['personaGroups'])}")
    joint_activities = sum(1 for a in p2["activities"] if len(a.get("involves", [])) > 1)
    print(f"  Activities with joint involvement: {joint_activities}/{len(p2['activities'])}")


if __name__ == "__main__":
    main()
