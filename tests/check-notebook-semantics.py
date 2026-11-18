#!/usr/bin/env python3
"""Grade companion-guide outputs using the isolated skill eval harness."""

import argparse
import json
from pathlib import Path


FIXTURES = Path(__file__).resolve().parents[1] / (
    "skills/export-notebook-semantics/evals/files/existing-export"
)


def grade(directory):
    collision = directory.name == "existing-export"
    guides = sorted(directory.glob("*/*.md" if collision else "*.md"))
    texts = [path.read_text(encoding="utf-8").lower() for path in guides]

    def covers(*phrases):
        return any(all(phrase in text for phrase in phrases) for text in texts)

    checks = {
        "three standalone guides": len(guides) == 3 and len({path.parent for path in guides}) == 1,
        "versioned sources": bool(texts) and all("5.1.0" in text for text in texts),
        "authored and composed content": covers("authored", "studio practice view", "omit"),
        "criteria and assessment": covers("checklist", "evidence", "`current`"),
        "stage type and trigger": covers("orchestration", "ondemand", "trigger"),
    }
    if collision:
        checks["original Markdown preserved"] = all(
            (directory / fixture.name).is_file()
            and (directory / fixture.name).read_bytes() == fixture.read_bytes()
            for fixture in FIXTURES.glob("*.md")
        )
        checks["incomplete context explained"] = covers("dependencies and gaps", "unresolved", "placeholder")

    rate = sum(checks.values()) / len(checks)
    return {"checks": checks, "summary": {"pass_rate": rate, "error_pass_rate": rate}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(grade(parser.parse_args().directory)))
