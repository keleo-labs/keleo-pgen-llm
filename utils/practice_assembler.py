"""
Practice Assembler: Assemble markdown reports from modules.

Handles Phase 1.5 assembly tasks.
"""
from pathlib import Path
from typing import List


def assemble_practice_report(practice_dir: Path) -> str:
    """
    Assemble practice report from modules 00-07.

    Args:
        practice_dir: Path to practice directory (contains report-elements/)

    Returns:
        Assembled report content
    """
    report_elements = practice_dir / "report-elements"

    if not report_elements.exists():
        raise ValueError(f"report-elements directory not found in {practice_dir}")

    # Concatenate all modules
    modules = sorted(report_elements.glob("*.md"))

    assembled_content = []
    for module_file in modules:
        content = module_file.read_text()
        assembled_content.append(f"# {module_file.stem}\n\n{content}\n\n")

    return "\n".join(assembled_content)


def assemble_method_overview(method_dir: Path) -> str:
    """
    Assemble method overview from modules 00 and 08.

    Args:
        method_dir: Path to method directory

    Returns:
        Method overview content
    """
    report_elements = method_dir / "report-elements"

    overview_parts = []

    # Module 00: Method plan
    method_plan = report_elements / "00-method-plan.md"
    if method_plan.exists():
        overview_parts.append(method_plan.read_text())

    # Module 08: Method assembly
    method_assembly = report_elements / "08-method-assembly.md"
    if method_assembly.exists():
        overview_parts.append(method_assembly.read_text())

    return "\n\n---\n\n".join(overview_parts)


def create_report_index(method_dir: Path, practice_names: List[str]) -> str:
    """
    Create research-report.md as index with links.

    Args:
        method_dir: Path to method directory
        practice_names: List of practice names

    Returns:
        Index content
    """
    index_lines = [
        f"# {method_dir.name} Research Report",
        "",
        "This method includes multiple practices. Reports are split for manageability.",
        "",
        "## Method Overview",
        "",
        "See [reports/method-overview.md](reports/method-overview.md) for method-level planning and integration guidance.",
        "",
        "## Practice Reports",
        ""
    ]

    for i, practice_name in enumerate(practice_names, 1):
        index_lines.append(f"{i}. [Practice {i}: {practice_name}](reports/practice-{i}-report.md)")

    index_lines.extend([
        "",
        "## Cross-Reference Index",
        "",
        "See [cross-reference-index.json](cross-reference-index.json) for validation index."
    ])

    return "\n".join(index_lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python practice_assembler.py <practice_directory>")
        sys.exit(1)

    practice_dir = Path(sys.argv[1])
    report = assemble_practice_report(practice_dir)

    output_file = practice_dir / "research-report.md"
    output_file.write_text(report)

    print(f"Assembled report written to {output_file}")
