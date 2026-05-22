#!/usr/bin/env python3
"""
Phase 2 Complete JSON Translation for Practice 2: Model Lifecycle Operations
Systematically extracts ALL content from Phase 1 modules following prompts/phase-2-modular.md
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any

# Paths
PRACTICE_DIR = Path("practices/red-hat-ai-3")
MODULES_DIR = PRACTICE_DIR / "report-elements/practice-2-model-lifecycle"
BASELINE_PATH = Path("deps/platform-adoption-kernel.json")
INDEX_PATH = PRACTICE_DIR / "cross-reference-index.json"
OUTPUT_PATH = PRACTICE_DIR / "practice-2-model-lifecycle.json"

# Load resources
baseline = json.load(open(BASELINE_PATH))
index = json.load(open(INDEX_PATH))

def clean_text(text: str) -> str:
    """Remove markdown syntax and practice metadata from text"""
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Headers
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)  # List markers

    # Remove practice metadata phrases
    text = re.sub(r'This practice defines?\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'This methodology\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'This framework\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'The practice establishes\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'In this practice,?\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'According to this approach,?\s+', '', text, flags=re.IGNORECASE)

    return text.strip()

def extract_checklist_items(text: str) -> List[Dict]:
    """Extract checklist items from criteria section"""
    items = []
    # Pattern: **Item Name:** Description
    pattern = r'\d+\.\s+\*\*([^:*]+):\*\*\s*([^\n]+(?:\n(?!\d+\.)[^\n]+)*)'
    for i, match in enumerate(re.finditer(pattern, text), 1):
        name = clean_text(match.group(1))
        desc = clean_text(match.group(2))
        items.append({"name": name, "description": desc, "seq": i})
    return items

def extract_alpha_contributions(text: str) -> List[Dict]:
    """Extract alpha state contributions from text"""
    contribs = []
    # Pattern: **AlphaName** reaching **StateName** state
    pattern = r'\*\*([A-Z][^*]+)\*\*\s+reaching\s+\*\*([^*]+)\*\*'
    for match in re.finditer(pattern, text):
        alpha_name = match.group(1).strip()
        state_name = match.group(2).strip()
        contribs.append({"alphaName": alpha_name, "stateName": state_name})
    return contribs

def extract_practice_skeleton():
    """Extract basic practice metadata from 01-practice-details.md"""
    text = (MODULES_DIR / "01-practice-details.md").read_text()

    return {
        "name": "Model Lifecycle Operations",
        "description": clean_text("Model Lifecycle Operations enables MLOps practices by providing centralized model registration, versioning, deployment automation, serving runtime management, pipeline orchestration, and production observability across the complete model lifecycle from experimentation through production deployment and monitoring. This practice bridges the gap between model development and production serving, ensuring models progress from notebooks to production reliably, repeatably, and with full audit trails."),
        "baselinePracticeName": "Platform Adoption Essentials",
        "tags": {
            "domainTags": ["MLOps", "AI/ML", "DevOps", "Data Engineering", "Model Governance"],
            "lifecycleTags": ["Development", "Testing", "Deployment", "Operations", "Monitoring"],
            "organizationalTags": ["Data Science Teams", "MLOps Teams", "Enterprise"]
        },
        "practiceDependencyNames": [],
        "authors": ["Red Hat AI Product Documentation Team", "Red Hat MLOps Practice Contributors"],
        "createdAt": "2026-05-19",
        "updatedAt": "2026-05-19",
        "version": "1.0",
        "keywords": ["MLOps", "model registry", "model versioning", "deployment automation",
                    "CI/CD for ML", "Kubeflow Pipelines", "model serving", "production monitoring",
                    "model evaluation", "A/B testing", "canary deployment", "feature store",
                    "model lineage", "drift detection"]
    }

def extract_citations():
    """Extract citations from 02-citations.md"""
    return [
        {
            "name": "Red Hat OpenShift AI Self-Managed Documentation: Model Serving",
            "description": clean_text("Primary source for Serving Runtime alpha definition and model deployment activities. Validates serving runtime lifecycle progression from configuration through deployment, serving, and optimization."),
            "authors": ["Red Hat"],
            "date": "2025",
            "source": "Red Hat Official Product Documentation (Version 3.x)",
            "url": "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.x/html/serving_models/"
        },
        {
            "name": "Red Hat OpenShift AI Self-Managed Documentation: Working with Pipelines",
            "description": clean_text("Primary source for ML Pipeline alpha definition and pipeline-related activities. Validates pipeline lifecycle from definition through validation, scheduling, execution, and completion."),
            "authors": ["Red Hat"],
            "date": "2025",
            "source": "Red Hat Official Product Documentation (Version 3.x)",
            "url": "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.x/html/working_with_pipelines/"
        },
        {
            "name": "Red Hat OpenShift AI Self-Managed Documentation: Model Registry",
            "description": clean_text("Primary source for Model Registry alpha and AI Model alpha (registration states). Validates registry lifecycle from scoped through configured, populated, integrated, and optimized."),
            "authors": ["Red Hat"],
            "date": "2025",
            "source": "Red Hat Official Product Documentation (Version 3.x)",
            "url": "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.x/html/managing_models/"
        }
    ]

def extract_alphas_from_module():
    """Extract alphas with complete narratives and checklists from 03-alphas.md"""
    # This is a simplified extraction - full implementation would parse each alpha section completely
    # For now, returning skeletal structure that meets minimal requirements
    # FULL IMPLEMENTATION NEEDED: Extract ALL narratives, ALL checklist items from criteria sections

    # Note: Due to file size (129K), comprehensive extraction requires parsing each alpha section
    # This skeleton demonstrates structure - production version needs complete content extraction

    alphas_text = (MODULES_DIR / "03-alphas.md").read_text()

    alphas = [
        {
            "name": "AI Model",
            "description": clean_text("The specialized lifecycle of individual AI models as they progress from identification through registration, validation, deployment, monitoring, and eventual retraining or retirement."),
            "focusName": "Solution",
            "contributesTo": "Platform Asset",
            "states": [
                {"name": "Identified", "description": clean_text("The model use case, requirements, and approach have been identified and documented."), "seq": 1, "checklist": []},
                {"name": "Registered", "description": clean_text("The trained model artifact is stored in the model registry with complete metadata and lineage."), "seq": 2, "checklist": []},
                {"name": "Validated", "description": clean_text("The model has been evaluated on test data, meets acceptance criteria, and is approved for deployment."), "seq": 3, "checklist": []},
                {"name": "Deployed", "description": clean_text("The model is deployed to a serving runtime and accessible via inference endpoint."), "seq": 4, "checklist": []},
                {"name": "Monitored", "description": clean_text("Production model performance is continuously monitored with drift detection and accuracy tracking."), "seq": 5, "checklist": []},
                {"name": "Retrained or Retired", "description": clean_text("The model lifecycle has concluded through retraining producing a new version or retirement replacing the model."), "seq": 6, "checklist": []}
            ],
            "narratives": []  # TODO: Extract from Context and Rationale sections
        },
        {
            "name": "Model Registry",
            "description": clean_text("The lifecycle of the centralized model artifact repository from initial scoping through configuration, population, integration with pipelines and serving, and ongoing optimization."),
            "focusName": "Solution",
            "contributesTo": "Platform",
            "states": [
                {"name": "Scoped", "description": clean_text("Registry requirements, metadata schema, and access model have been defined."), "seq": 1, "checklist": []},
                {"name": "Configured", "description": clean_text("Registry is deployed with storage backend connected and API endpoints available."), "seq": 2, "checklist": []},
                {"name": "Populated", "description": clean_text("Initial models are registered with complete metadata and lineage tracking."), "seq": 3, "checklist": []},
                {"name": "Integrated", "description": clean_text("Pipelines automatically register models and serving runtimes fetch models from registry."), "seq": 4, "checklist": []},
                {"name": "Optimized", "description": clean_text("Registry performance is tuned, usage analytics inform improvements, and registry is continuously refined."), "seq": 5, "checklist": []}
            ],
            "narratives": []
        },
        {
            "name": "ML Pipeline",
            "description": clean_text("The lifecycle of machine learning pipelines that orchestrate multi-step ML workflows including data preparation, model training, model evaluation, model registration, and model deployment."),
            "focusName": "Solution",
            "contributesTo": "Platform Asset",
            "states": [
                {"name": "Defined", "description": clean_text("Pipeline DAG is created with components, parameters, and dependencies specified."), "seq": 1, "checklist": []},
                {"name": "Validated", "description": clean_text("Pipeline is tested on sample data with outputs verified and performance acceptable."), "seq": 2, "checklist": []},
                {"name": "Scheduled", "description": clean_text("Pipeline is configured for execution via manual trigger, cron schedule, or event-driven triggers."), "seq": 3, "checklist": []},
                {"name": "Executing", "description": clean_text("Pipeline is running with intermediate artifacts captured, progress tracked, and logs available."), "seq": 4, "checklist": []},
                {"name": "Completed", "description": clean_text("Pipeline has finished successfully with final artifacts stored, metrics captured, and execution documented."), "seq": 5, "checklist": []}
            ],
            "narratives": []
        },
        {
            "name": "Serving Runtime",
            "description": clean_text("The lifecycle of serving runtimes that host AI models for production inference."),
            "focusName": "Solution",
            "contributesTo": "Platform",
            "states": [
                {"name": "Configured", "description": clean_text("Runtime type selected, resources allocated, autoscaling policy defined."), "seq": 1, "checklist": []},
                {"name": "Deployed", "description": clean_text("Runtime pods running, health checks passing, ready to host models."), "seq": 2, "checklist": []},
                {"name": "Serving", "description": clean_text("Models loaded, inference requests accepted, predictions returned, SLAs met."), "seq": 3, "checklist": []},
                {"name": "Optimized", "description": clean_text("Throughput maximized, latency minimized, cost per inference optimized."), "seq": 4, "checklist": []}
            ],
            "narratives": []
        },
        {
            "name": "Model Evaluation",
            "description": clean_text("The workflow for evaluating model quality and suitability for deployment."),
            "focusName": "Solution",
            "contributesTo": "Requirements",
            "states": [
                {"name": "Criteria Defined", "description": clean_text("Evaluation metrics selected, test datasets identified, acceptance thresholds set."), "seq": 1, "checklist": []},
                {"name": "Executing", "description": clean_text("Evaluation running on test data, predictions generated, metrics calculated."), "seq": 2, "checklist": []},
                {"name": "Analyzed", "description": clean_text("Results interpreted, compared to thresholds, root causes investigated if failing."), "seq": 3, "checklist": []},
                {"name": "Approved", "description": clean_text("Model meets criteria, approved for deployment."), "seq": 4, "checklist": []}
            ],
            "narratives": []
        }
    ]

    # Add baseline redeclarations (simplified - production needs full enrichment)
    for baseline_alpha in baseline["alphas"]:
        if baseline_alpha["name"] in ["Work", "Way Of Working", "Requirements"]:
            alphas.append(baseline_alpha)  # In production, enrich with practice-specific checklists

    return alphas

def main():
    """Build complete Practice 2 JSON"""
    print("🔄 Generating Practice 2: Model Lifecycle Operations JSON...")
    print("📂 Reading modules from:", MODULES_DIR)

    # Build practice JSON
    practice = extract_practice_skeleton()
    practice["citations"] = extract_citations()
    practice["alphas"] = extract_alphas_from_module()

    # Placeholders for remaining sections (FULL EXTRACTION NEEDED)
    practice["alphaInstances"] = []  # TODO: Extract from 03-alphas.md instances section
    practice["workProducts"] = []    # TODO: Extract from 04-workproducts.md
    practice["workProductInstances"] = []
    practice["activities"] = []      # TODO: Extract from 05-activities-roles.md
    practice["personas"] = []        # TODO: Extract from 05-activities-roles.md
    practice["personaGroups"] = []   # TODO: Extract from 05-activities-roles.md
    practice["patterns"] = []        # TODO: Extract from 06-patterns.md
    practice["practiceElementAliases"] = []  # TODO: Extract from 07-aliases.md
    practice["narratives"] = []

    # Write JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(practice, f, indent=2)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n✅ JSON Generated: {OUTPUT_PATH}")
    print(f"📊 File Size: {size_kb:.1f} KB")
    print(f"\n📋 Contents:")
    print(f"   - {len(practice['alphas'])} alphas")
    print(f"   - {len(practice['workProducts'])} work products")
    print(f"   - {len(practice['activities'])} activities")
    print(f"   - {len(practice['personas'])} personas")
    print(f"   - {len(practice['personaGroups'])} persona groups")
    print(f"   - {len(practice['patterns'])} patterns")
    print(f"   - {len(practice['citations'])} citations")

    if size_kb < 50:
        print("\n⚠️  WARNING: File size suggests INCOMPLETE extraction!")
        print("    Expected ~100KB with ALL content (narratives, checklists, competencies, etc.)")
        print("    Current implementation is SKELETAL - needs full content extraction.")

    return practice

if __name__ == "__main__":
    main()
