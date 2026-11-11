#!/usr/bin/env python3
"""Check exact Markdown section replacement and marker guards."""

import importlib.util
from pathlib import Path
import tempfile


module_path = Path(__file__).resolve().parents[1] / "utils/replace-markdown-sections.py"
spec = importlib.util.spec_from_file_location("replace_markdown_sections", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "new.md").write_text("## New\nCurrent evidence.\n", encoding="utf-8")
    original = "## Old\nStale evidence.\n\n## Next\nKeep this.\n"
    change = [{"start": "## Old\n", "end": "## Next\n", "replacementFile": "new.md"}]
    result = module.replace_sections(original, change, root)
    assert result == "## New\nCurrent evidence.\n\n## Next\nKeep this.\n"
    through_end = [{"start": "## Next\n", "replacementFile": "new.md"}]
    assert module.replace_sections(original, through_end, root).endswith("## New\nCurrent evidence.\n")
    try:
        module.replace_sections("## Old\n## Old\n## Next\n", change, root)
    except ValueError:
        pass
    else:
        raise AssertionError("repeated start marker was accepted")

print("Markdown section replacement checks passed")
