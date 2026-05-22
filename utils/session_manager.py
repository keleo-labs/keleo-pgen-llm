"""
Session Manager: Checkpoint and resume support.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from .module_validator import count_words


def get_checkpoint_path(practice_dir: Path) -> Path:
    """Get path to current checkpoint file."""
    return practice_dir / ".checkpoint.json"


def get_checkpoints_dir(practice_dir: Path) -> Path:
    """Get path to historical checkpoints directory."""
    return practice_dir / ".checkpoints"


def detect_checkpoint(practice_dir: Path) -> Optional[Dict]:
    """
    Read checkpoint file if exists.

    Args:
        practice_dir: Path to practice directory

    Returns:
        Checkpoint dict if exists, None otherwise
    """
    checkpoint_path = get_checkpoint_path(practice_dir)

    if not checkpoint_path.exists():
        return None

    with open(checkpoint_path) as f:
        return json.load(f)


def analyze_completion_status(practice_dir: Path, checkpoint: Dict) -> Dict:
    """
    Verify checkpoint claims against actual files.

    Args:
        practice_dir: Path to practice directory
        checkpoint: Checkpoint dict

    Returns:
        Status dict with verified completion info and issues
    """
    status = {
        "practiceType": checkpoint.get("practiceType", "Practice"),
        "phase": checkpoint.get("phase", "unknown"),
        "verified": {
            "phase1": {},
            "phase15": {},
            "phase2": {}
        },
        "issues": []
    }

    # For Practice
    if checkpoint["practiceType"] == "Practice":
        report_elements = practice_dir / "report-elements"

        for module_num in ["00", "01", "02", "03", "04", "05", "06", "07"]:
            # Check for module file (might be split)
            module_files = list(report_elements.glob(f"{module_num}*.md"))

            if module_files:
                status["verified"]["phase1"][module_num] = {
                    "complete": True,
                    "files": [f.name for f in module_files],
                    "total_words": sum(count_words(f) for f in module_files)
                }
            else:
                status["verified"]["phase1"][module_num] = {
                    "complete": False,
                    "files": [],
                    "total_words": 0
                }

        # Check Phase 1.5
        if (practice_dir / "research-report.md").exists():
            status["verified"]["phase15"]["report"] = True
        if (practice_dir / "cross-reference-index.json").exists():
            status["verified"]["phase15"]["xref"] = True

        # Check Phase 2
        practice_name = practice_dir.name
        if (practice_dir / f"{practice_name}.json").exists():
            status["verified"]["phase2"]["json"] = True

    # For Method
    elif checkpoint["practiceType"] == "Method":
        report_elements = practice_dir / "report-elements"

        # Check method-level modules
        if (report_elements / "00-method-plan.md").exists():
            status["verified"]["phase1"]["method-plan"] = True
        if (report_elements / "08-method-assembly.md").exists():
            status["verified"]["phase1"]["method-assembly"] = True

        # Check each practice
        if "phase1Modules" in checkpoint["status"]:
            for practice_name in checkpoint["status"]["phase1Modules"].keys():
                practice_dir_path = report_elements / practice_name

                status["verified"]["phase1"][practice_name] = {}

                for module_num in ["00", "01", "02", "03", "04", "05", "06", "07"]:
                    module_files = list(practice_dir_path.glob(f"{module_num}*.md"))
                    status["verified"]["phase1"][practice_name][module_num] = bool(module_files)

        # Check Phase 1.5
        reports_dir = practice_dir / "reports"
        if reports_dir.exists():
            status["verified"]["phase15"]["split_reports"] = True
            status["verified"]["phase15"]["report_count"] = len(list(reports_dir.glob("*.md")))

        # Check Phase 2
        practices_dir = practice_dir / "practices"
        if practices_dir.exists():
            status["verified"]["phase2"]["practice_jsons"] = [f.name for f in practices_dir.glob("*.json")]

        method_name = practice_dir.name
        if (practice_dir / f"{method_name}.json").exists():
            status["verified"]["phase2"]["method_json"] = True

    return status


def plan_remaining_work(status: Dict, checkpoint: Dict) -> List[str]:
    """
    Generate action plan for remaining work.

    Args:
        status: Status dict from analyze_completion_status()
        checkpoint: Checkpoint dict

    Returns:
        List of action items
    """
    plan = []

    practice_type = status["practiceType"]

    if practice_type == "Practice":
        # Phase 1: Check incomplete modules
        for module_num in ["00", "01", "02", "03", "04", "05", "06", "07"]:
            module_status = status["verified"]["phase1"].get(module_num, {})
            if not module_status.get("complete", False):
                plan.append(f"Generate module {module_num}")

        # Phase 1.5: Check assembly
        if not status["verified"]["phase15"].get("report"):
            plan.append("Assemble research report")
        if not status["verified"]["phase15"].get("xref"):
            plan.append("Generate cross-reference index")

        # Phase 2: Check JSON
        if not status["verified"]["phase2"].get("json"):
            plan.append("Build practice JSON")

    elif practice_type == "Method":
        # Check method modules
        if not status["verified"]["phase1"].get("method-plan"):
            plan.append("Generate method plan (module 00)")

        # Check practice modules
        for practice_name, modules in status["verified"]["phase1"].items():
            if practice_name in ["method-plan", "method-assembly"]:
                continue

            if isinstance(modules, dict):
                for module_num in ["00", "01", "02", "03", "04", "05", "06", "07"]:
                    if not modules.get(module_num, False):
                        plan.append(f"Generate {practice_name} module {module_num}")

        # Check method assembly
        if not status["verified"]["phase1"].get("method-assembly"):
            plan.append("Generate method assembly (module 08)")

        # Phase 1.5
        if not status["verified"]["phase15"].get("split_reports"):
            plan.append("Assemble split practice reports")

        # Phase 2
        practice_jsons = status["verified"]["phase2"].get("practice_jsons", [])
        expected_practices = len([k for k in status["verified"]["phase1"].keys()
                                   if k not in ["method-plan", "method-assembly"]])

        if len(practice_jsons) < expected_practices:
            plan.append(f"Build practice JSONs ({len(practice_jsons)}/{expected_practices} complete)")

        if not status["verified"]["phase2"].get("method_json"):
            plan.append("Build method JSON")

    return plan


def save_checkpoint(practice_dir: Path, checkpoint: Dict) -> None:
    """
    Save checkpoint with timestamp.

    Args:
        practice_dir: Path to practice directory
        checkpoint: Checkpoint dict to save
    """
    checkpoint["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    # Save current checkpoint
    checkpoint_path = get_checkpoint_path(practice_dir)
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    # Save historical checkpoint
    checkpoints_dir = get_checkpoints_dir(practice_dir)
    checkpoints_dir.mkdir(exist_ok=True)

    phase = checkpoint.get("phase", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    historical_path = checkpoints_dir / f"{phase}-{timestamp}.json"

    with open(historical_path, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def create_initial_checkpoint(practice_dir: Path, practice_type: str, practice_name: str) -> Dict:
    """
    Create initial checkpoint for new translation.

    Args:
        practice_dir: Path to practice directory
        practice_type: "Practice" or "Method"
        practice_name: Name of practice/method

    Returns:
        Initial checkpoint dict
    """
    checkpoint = {
        "checkpointVersion": "1.0",
        "practiceName": practice_name,
        "practiceType": practice_type,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "phase": "phase-1",
        "status": {}
    }

    if practice_type == "Practice":
        checkpoint["status"]["phase1Modules"] = {
            "completed": [],
            "inProgress": None,
            "remaining": ["00", "01", "02", "03", "04", "05", "06", "07"]
        }
        checkpoint["status"]["phase15Assembly"] = "not-started"
        checkpoint["status"]["phase2Json"] = "not-started"

    elif practice_type == "Method":
        checkpoint["status"]["phase1Modules"] = {}
        checkpoint["status"]["phase15Assembly"] = {}
        checkpoint["status"]["phase2Json"] = {}

    save_checkpoint(practice_dir, checkpoint)
    return checkpoint


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python session_manager.py <practice_directory>")
        sys.exit(1)

    practice_dir = Path(sys.argv[1])

    # Try to detect checkpoint
    checkpoint = detect_checkpoint(practice_dir)

    if checkpoint:
        print(f"Checkpoint found: {checkpoint['practiceName']} ({checkpoint['practiceType']})")
        print(f"Phase: {checkpoint['phase']}")
        print(f"Last updated: {checkpoint['lastUpdated']}")

        # Analyze completion status
        status = analyze_completion_status(practice_dir, checkpoint)
        print(f"\nVerified status:")
        print(json.dumps(status, indent=2))

        # Plan remaining work
        plan = plan_remaining_work(status, checkpoint)
        print(f"\nRemaining work:")
        for item in plan:
            print(f"  - {item}")
    else:
        print(f"No checkpoint found in {practice_dir}")
