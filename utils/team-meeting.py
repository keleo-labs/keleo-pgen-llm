#!/usr/bin/env python3
"""Resolve, prepare, migrate and check team-meeting workspaces. Version 5.0.0.

Examples:
  team-meeting.py resolve reports/service-weekly/series.json
  team-meeting.py prepare reports/service-weekly/series.json --at 2026-10-26T09:00:00Z --fix
  team-meeting.py migrate --workspace /path/to/legacy/workspace --fix
  team-meeting.py check-report reports/service-weekly/2026-10-26-0900/report.md

Writes default to dry-run. No source service is contacted by this utility.
"""

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

VERSION = "5.0.0"
CONFIG_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
HEADINGS = ["Suggested agenda", "Introductory summary", "How we work",
            "What we discussed last time", "Acknowledgements", "News", "Reminders", "Analysis"]
PATH_FIELDS = ("fixturePath", "statePath", "mappingPath", "recipePath")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def local_path(value, declaring_file):
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        raise ValueError(f"Expected a local file path, got {value}")
    return str((Path(declaring_file).parent / Path(value).expanduser()).resolve())


def validate(value, schema_name, project_root=ROOT):
    from jsonschema import Draft202012Validator, FormatChecker
    schema_dir = Path(project_root) / ".agents/skills/team-meeting/references"
    schema = read_json(schema_dir / schema_name)
    if schema_name == "series.schema.json":
        signal_schema = read_json(schema_dir / "signals.schema.json")
        schema["$defs"]["signal"] = signal_schema["$defs"]["signal"]
        schema["properties"]["signals"]["items"] = {"$ref": "#/$defs/signal"}
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
                    key=lambda error: str(list(error.path)))
    if errors:
        raise ValueError("; ".join(f"{'/'.join(map(str, e.path))}: {e.message}" for e in errors))


def resolve(series_path, project_root=ROOT):
    series_path = Path(series_path).resolve()
    project_root = Path(project_root).resolve()
    global_path = project_root / "config/team-meeting/signals.json"
    base, series = read_json(global_path), read_json(series_path)
    validate(base, "signals.schema.json", project_root)
    validate(series, "series.schema.json", project_root)
    result = deepcopy(series)
    signals, seen = [], set()
    for origin, config in ((global_path, base), (series_path, series)):
        for definition in config["signals"]:
            identity = definition["id"]
            if identity in seen:
                raise ValueError(f"Duplicate signal ID: {identity}; inheritance is additive only")
            seen.add(identity)
            signal = deepcopy(definition)
            for key in PATH_FIELDS:
                if key in signal:
                    signal[key] = local_path(signal[key], origin)
            signal["origin"] = str(origin)
            signals.append(signal)
    result["signals"] = signals
    result["history"]["paths"] = [local_path(p, series_path) for p in series["history"]["paths"]]
    result["review"]["recipes"] = [local_path(p, series_path) for p in series["review"]["recipes"]]
    if "relatedSeriesPaths" in result["review"]:
        result["review"]["relatedSeriesPaths"] = [local_path(p, series_path) for p in series["review"]["relatedSeriesPaths"]]
    for group in result["practice"]["groups"]:
        group["paths"] = [local_path(p, series_path) for p in group["paths"]]
        group["mergedPath"] = local_path(group["mergedPath"], series_path)
    for calendar in result["calendars"]:
        ZoneInfo(calendar["timezone"])
    if len({c["timezone"] for c in result["calendars"]}) != 1:
        raise ValueError("A series needs one meeting timezone across its calendar selectors")
    result["configurationSources"] = {"project": str(global_path), "series": str(series_path)}
    return result


def prepare(series_path, at, fix=False, project_root=ROOT):
    effective = resolve(series_path, project_root)
    start = datetime.fromisoformat(at.replace("Z", "+00:00"))
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("Meeting start needs a timezone-qualified RFC3339 timestamp")
    local = start.astimezone(ZoneInfo(effective["calendars"][0]["timezone"]))
    destination = Path(series_path).resolve().parent / local.strftime("%Y-%m-%d-%H%M")
    if destination.exists():
        raise ValueError(f"Instance already exists; revise in place without replacing snapshots: {destination}")
    groups = effective["practice"]["groups"]
    for group in groups:
        if not Path(group["mergedPath"]).is_file():
            raise ValueError(f"Resolve the agreed practice first: {group['mergedPath']}")
    if not fix:
        return {"dryRun": True, "directory": str(destination)}
    # Build before rename so a failed copy never leaves a half-prepared instance.
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "instance"
        stage.mkdir()
        (stage / "evidence").mkdir()
        context = stage / "context"
        context.mkdir()
        effective["meetingStart"] = start.isoformat()
        effective["contextSnapshots"] = []
        for index, group in enumerate(groups):
            target = context / f"{index + 1}-merged-practice.json"
            shutil.copy2(group["mergedPath"], target)
            effective["contextSnapshots"].append(str(target.relative_to(stage)))
        write_json(stage / "effective-config.json", effective)
        stage.rename(destination)
    return {"directory": str(destination), "configuration": str(destination / "effective-config.json")}


def report_errors(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    # Ignore fenced examples rather than counting their headings as report sections.
    visible, fenced = [], False
    for line in lines:
        if line.startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            visible.append(line)
    headings = [line[3:].strip() for line in visible if line.startswith("## ")]
    errors = []
    if not visible or not re.match(r"^# \S", visible[0]):
        errors.append("First line must be the meeting name as a level-one title")
    if len(visible) < 2 or not re.match(r"^## \S", visible[1]) or visible[1][3:].strip() in HEADINGS:
        errors.append("Second line must be the dated meeting instance as the first level-two heading")
    if next((line for line in visible[2:] if line.strip()), "") != "## Suggested agenda":
        errors.append("Suggested agenda must follow the meeting instance immediately")
    if headings[1:] != HEADINGS or len(headings) != len(HEADINGS) + 1:
        errors.append("Expected instance heading followed by eight ordered sections: " + ", ".join(HEADINGS))
    for index, heading in enumerate(HEADINGS):
        marker = "## " + heading
        if marker not in visible:
            continue
        begin = visible.index(marker) + 1
        end = next((i for i in range(begin, len(visible)) if visible[i].startswith("## ")), len(visible))
        section = visible[begin:end]
        if not any(line.strip() and not line.startswith("#") for line in section):
            errors.append(f"Empty section: {heading}")
        if heading in ("Acknowledgements", "News", "Reminders", "Suggested agenda"):
            details = [i for i, line in enumerate(section) if line.startswith("### ")]
            summary = section[:details[0]] if details else section
            bullets = [line for line in summary if re.match(r"^[-*] \S", line)]
            if not bullets:
                errors.append(f"{heading} needs summary bullets")
            if heading in ("News", "Suggested agenda"):
                if len(details) != len(bullets):
                    errors.append(f"{heading} needs one detail subsection per summary item")
                if heading == "Suggested agenda" and not details:
                    errors.append("Suggested agenda needs topic detail subsections")
                for offset, start in enumerate(details):
                    stop = details[offset + 1] if offset + 1 < len(details) else len(section)
                    if heading == "Suggested agenda" and not any(re.match(r"^[-*] \S", line) for line in section[start + 1:stop]):
                        errors.append(f"Suggested agenda detail needs briefing bullets: {section[start][4:]}")
    return errors


def markdown_fields(text, section):
    match = re.search(r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    body = match.group(1) if match else ""
    return dict(re.findall(r"^\*\*(.+?):\*\*\s*(.+)$", body, re.M)), body


def relocate(value, workspace):
    """Preserve legacy evidence links without rewriting identifiers or remote URIs."""
    if isinstance(value, dict):
        return {key: relocate(item, workspace) for key, item in value.items()}
    if isinstance(value, list):
        return [relocate(item, workspace) for item in value]
    if isinstance(value, str) and value.startswith(("resources/", "meetings/", "reports/")):
        return str((workspace / value).resolve())
    return value


def migrate(workspace, fix=False, project_root=ROOT):
    workspace, project_root = Path(workspace).resolve(), Path(project_root).resolve()
    text = (workspace / "my-config/skill-config.md").read_text()
    if "## team-call" not in text:
        _, migrated = markdown_fields(text, "team-meeting")
        pointers = re.findall(r"^- (.+/series\.json)\s*$", migrated, re.M)
        if not pointers:
            raise ValueError("No legacy team-call configuration or migrated series pointers found")
        result = []
        for pointer in pointers:
            series_path = Path(local_path(pointer, workspace / "my-config/skill-config.md"))
            resolve(series_path, project_root)
            result.append({"series": str(series_path.parent), "status": "already migrated"})
        return result
    fields, body = markdown_fields(text, "team-call")
    titles = [fields.get(key, "") for key in ("Weekly sync", "All Hands")]
    if any(not title or title.startswith("your-") for title in titles):
        raise ValueError("Both exact legacy calendar titles must be configured")
    state_path = workspace / fields["News signals state"]
    state = read_json(state_path)
    method_path = Path(state["methodPath"])
    method = read_json(method_path)
    roster = (workspace / "resources/org-roster.md").read_text()
    team_block = re.search(r"^## My team.*?\n(.*?)(?=^## |\Z)", roster, re.M | re.S)
    if not team_block:
        raise ValueError("Cannot find the legacy My team roster")
    focus = re.findall(r"^- (.+)$", body, re.M)
    members = []
    for row in team_block.group(1).splitlines():
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) >= 3 and "@" in cells[1]:
            members.append({"name": cells[0], "email": cells[1], "role": cells[2],
                            "responsibilities": [item for item in focus if cells[0] in item]})
    if not members:
        raise ValueError("No team members found; migration stopped")
    # The old roster excludes the manager; retain the named anchor as a team participant.
    anchor = re.search(r"\*\*Anchor:\*\* (.+?) \(`([^`]+)`\)", roster)
    if anchor:
        members.append({"name": anchor.group(1), "email": anchor.group(2), "role": "Team manager", "responsibilities": []})
    report_fields, _ = markdown_fields(text, "team-1-2-1")
    slugs = [re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") for title in titles]
    refs = project_root / ".agents/skills/team-meeting/references"
    result = []
    for index, (title, slug) in enumerate(zip(titles, slugs)):
        destination = project_root / "reports" / slug
        if destination.exists():
            resolve(destination / "series.json", project_root)
            result.append({"series": str(destination), "status": "already migrated"})
            continue
        result.append({"series": str(destination), "status": "migrate" if fix else "dry run"})
        if not fix:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".migrate-", dir=destination.parent) as temporary:
            stage = Path(temporary) / slug
            stage.mkdir()
            recipes = stage / "recipes"
            recipes.mkdir()
            for name in ("review.md", "signals.md", "business-picture.md", "news-state.schema.json",
                         "focus.md", "facilitation.md", "group-evidence.md", "deal-facts.md"):
                shutil.copy2(refs / name, recipes / name)
            migrated_state = relocate(state, workspace)
            migrated_state.update({"version": "2.0.0", "mappingPath": "mapping.json",
                                   "journalPath": "journal.json", "methodPath": str(method_path.resolve())})
            write_json(stage / "signals/state.json", migrated_state)
            mapping = relocate(read_json(workspace / state["mappingPath"]), workspace)
            # Keep pinned historical mapping versions byte-semantically intact.
            write_json(stage / "signals/mapping.json", mapping)
            journal = relocate(read_json(workspace / state["journalPath"]), workspace)
            write_json(stage / "signals/journal.json", journal)
            signals = [{"id": name, "recipe": name, "statePath": "signals/state.json",
                        "mappingPath": "signals/mapping.json", "recipePath": "recipes/signals.md"}
                       for name in ("team-mail", "team-slack", "recent-assistance", "commercial-verification")]
            signals.extend([{"id": "recognition", "recipe": "recognition", "recipePath": "recipes/review.md"},
                            {"id": "business-picture", "recipe": "business-picture", "recipePath": "recipes/business-picture.md"},
                            {"id": "team-requests", "recipe": "team-requests", "recipePath": "recipes/review.md"}])
            if fields.get("Newsletter"):
                signals.append({"id": "team-newsletter", "recipe": "web", "settings": {"url": fields["Newsletter"]}})
            review = {"cadence": "weekly" if index == 0 else "monthly/quarterly", "quarterOpening": bool(index),
                      "recipes": ["recipes/review.md", "recipes/business-picture.md", "recipes/focus.md", "recipes/facilitation.md"],
                      "relatedSeriesPaths": [f"../{slugs[1-index]}/series.json"], "focus": focus}
            if report_fields.get("Team requests report"):
                review["requestReportId"] = report_fields["Team requests report"]
            refreshed = re.search(r"\*\*Refreshed:\*\* (\S+)", roster)
            if refreshed:
                review["sourceRosterDate"] = refreshed.group(1)
            config = {"version": CONFIG_VERSION, "team": {"name": method["name"], "role": method.get("description", method["name"]), "members": members},
                      "objectives": None, "calendars": [{"id": "primary", "title": title, "timezone": "Europe/London"}],
                      "history": {"paths": [str(workspace / "meetings/team-meetings")], "lookbackMeetings": 4},
                      "practice": {"confirmed": True, "groups": [{"name": method["name"], "paths": [str(method_path.resolve())], "mergedPath": "context/merged-practice.json"}]},
                      "narratives": {"summary": "ABT", "retrospective": "STAR", "news": "ABT", "contributions": ["STAR", "PAR"], "confirmed": False},
                      "review": review, "signals": signals}
            validate(config, "series.schema.json", project_root)
            write_json(stage / "series.json", config)
            (stage / "context").mkdir()
            (stage / "context/source-skill-config.md").write_text(text, encoding="utf-8")
            completed = subprocess.run([sys.executable, str(project_root / "utils/resolve-context.py"),
                                        str(method_path), "--transitive", "-o", str(stage / "context/merged-practice.json")],
                                       cwd=project_root, capture_output=True, text=True)
            if completed.returncode:
                raise ValueError("Context resolution failed: " + (completed.stderr + completed.stdout)[-2000:])
            write_json(stage / "context/provenance.json", {"version": CONFIG_VERSION, "sourceWorkspace": str(workspace),
                       "methodPath": str(method_path), "methodVersion": method.get("version"), "sourceConfiguration": str(workspace / "my-config/skill-config.md"),
                       "legacyEvidencePathBase": str(workspace), "sourceState": str(state_path), "independentJournal": True})
            stage.rename(destination)
    return result


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        shutil.copytree(ROOT / ".agents/skills/team-meeting/references", self.root / ".agents/skills/team-meeting/references")
        write_json(self.root / "config/team-meeting/signals.json", {"version": CONFIG_VERSION, "signals": [{"id": "global", "recipe": "local", "fixturePath": "global.md"}]})
        self.series = self.root / "reports/service/series.json"
        self.config = read_json(ROOT / ".agents/skills/team-meeting/references/example-series.json")
        write_json(self.series, self.config)
        write_json(self.series.parent / "context/merged-practice.json", {"name": "Service", "version": VERSION})

    def test_additive_and_path_origins(self):
        config = resolve(self.series, self.root)
        self.assertEqual([s["id"] for s in config["signals"]], ["global", "service-updates"])
        self.assertEqual(config["signals"][0]["fixturePath"], str(self.root / "config/team-meeting/global.md"))
        self.assertEqual(config["signals"][1]["fixturePath"], str(self.series.parent / "signals/updates.md"))

    def test_duplicate_and_disable_rejected(self):
        for signal in ({"id": "global", "recipe": "local"}, {"id": "new", "recipe": "local", "enabled": False}):
            self.config["signals"] = [signal]
            write_json(self.series, self.config)
            with self.assertRaises(ValueError):
                resolve(self.series, self.root)
        self.assertFalse((self.series.parent / "2026-10-26-0900").exists())

    def test_prepare_dry_run_timezone_and_snapshot(self):
        plan = prepare(self.series, "2026-10-26T09:00:00Z", project_root=self.root)
        self.assertFalse(Path(plan["directory"]).exists())
        result = prepare(self.series, "2026-10-26T09:00:00Z", True, self.root)
        snapshot = read_json(Path(result["directory"]) / "effective-config.json")
        self.assertEqual(snapshot["team"]["name"], "Service operations")
        self.assertEqual(snapshot["version"], CONFIG_VERSION)
        with self.assertRaises(ValueError):
            prepare(self.series, "2026-10-26T09:00:00Z", True, self.root)
        with self.assertRaises(ValueError):
            prepare(self.series, "2026-10-27T09:00:00", project_root=self.root)

    def test_report_shape(self):
        report = self.root / "report.md"
        bodies = {"Acknowledgements": "- No suitable evidence was found.",
                  "News": "- No qualifying development was found.\n\n### Source coverage\n\nNo suitable evidence was found.",
                  "Reminders": "- No reminder was found.",
                  "Suggested agenda": "- Clarify ownership.\n\n### Clarify ownership\n\n- Agree the handoff."}
        report.write_text("# Service operations\n## 26 October 2026 · 09:00 UTC\n\n" +
                          "\n\n".join(f"## {h}\n\n" + bodies.get(h, "Evidence is unavailable.") for h in HEADINGS))
        self.assertEqual(report_errors(report), [])
        original = report.read_text()
        report.write_text(original.replace("# Service operations\n", "Service operations\n", 1))
        self.assertTrue(report_errors(report), "Meeting name needs title styling")
        report.write_text(original.replace("## 26 October 2026 · 09:00 UTC\n", "26 October 2026 · 09:00 UTC\n", 1))
        self.assertTrue(report_errors(report), "Meeting instance needs heading styling")
        report.write_text(original.replace("## 26 October 2026 · 09:00 UTC\n\n", "## 26 October 2026 · 09:00 UTC\n\n## Preface\n\n", 1))
        self.assertTrue(report_errors(report), "Agenda must follow the instance")
        report.write_text(original.replace("## 26 October 2026 · 09:00 UTC\n\n", "## 26 October 2026 · 09:00 UTC\n\nContext first.\n\n", 1))
        self.assertTrue(report_errors(report), "No prose may precede the agenda")
        report.write_text(original.replace("## Acknowledgements\n\n- No suitable evidence was found.\n\n", ""))
        self.assertTrue(report_errors(report), "Missing acknowledgements must fail")
        report.write_text(original.replace("## Acknowledgements", "## TEMP").replace("## News", "## Acknowledgements").replace("## TEMP", "## News"))
        self.assertTrue(report_errors(report), "Acknowledgements after News must fail")
        report.write_text(original)
        report.write_text(original.replace("### Clarify ownership\n\n- Agree the handoff.", "No briefing supplied."))
        self.assertTrue(report_errors(report), "An agenda summary alone must fail")
        report.write_text(original.replace("- Agree the handoff.", "Agree the handoff."))
        self.assertTrue(report_errors(report), "Agenda details need bullets")
        report.write_text(original.replace("- No qualifying development was found.", "- First item.\n- Second item."))
        self.assertTrue(report_errors(report), "News index and detail counts must agree")
        report.write_text(original)
        report.write_text(report.read_text().replace("## News", "## Private manager notes"))
        self.assertTrue(report_errors(report))

    def test_missing_sources_are_not_silently_removed(self):
        effective = resolve(self.series, self.root)
        self.assertFalse(Path(effective["signals"][1]["fixturePath"]).exists())
        self.assertEqual(len(effective["signals"]), 2)
        (self.series.parent / "context/merged-practice.json").unlink()
        with self.assertRaises(ValueError):
            prepare(self.series, "2026-10-26T09:00:00Z", True, self.root)
        self.assertFalse((self.series.parent / "2026-10-26-0900").exists())
        (self.root / "config/team-meeting/signals.json").unlink()
        with self.assertRaises(OSError):
            resolve(self.series, self.root)

    def test_optional_quota_configuration(self):
        quota = {"version": "1.0.0", "sourceSkill": "product-quota-attainment",
                 "geography": "Region A", "quotaViews": ["Product A", "Combined View", "Product D"],
                 "metric": "ACV+", "currency": "USD", "currencyBasis": "plan-rate",
                 "period": "review-quarter", "viewsAreAdditive": False,
                 "retainProductBreakdown": True}
        self.config["version"] = "1.1.0"
        self.config["review"]["metrics"] = {"quotaAttainment": quota}
        write_json(self.series, self.config)
        self.assertEqual(resolve(self.series, self.root)["review"]["metrics"]["quotaAttainment"], quota)
        for field, value in (("quotaViews", ["Product D", "Product D"]),
                             ("currency", "usd"), ("viewsAreAdditive", True),
                             ("retainProductBreakdown", False)):
            invalid = deepcopy(self.config)
            invalid["review"]["metrics"]["quotaAttainment"][field] = value
            write_json(self.series, invalid)
            with self.assertRaises(ValueError):
                resolve(self.series, self.root)

    def test_independent_journal_copies_and_legacy_links(self):
        original = {"evidencePaths": ["resources/team-news/evidence/mail.json"], "records": []}
        copied = relocate(original, self.root)
        self.assertEqual(copied["evidencePaths"][0], str(self.root / "resources/team-news/evidence/mail.json"))
        first, second = self.root / "first.json", self.root / "second.json"
        write_json(first, copied)
        write_json(second, copied)
        copied["records"].append("new")
        write_json(first, copied)
        self.assertEqual(read_json(second)["records"], [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("resolve", "prepare", "migrate"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--project-root", type=Path, default=ROOT)
        if name == "migrate":
            sub.add_argument("--workspace", type=Path, required=True)
        else:
            sub.add_argument("series", type=Path)
        if name == "prepare":
            sub.add_argument("--at", required=True)
        if name in ("prepare", "migrate"):
            sub.add_argument("--fix", action="store_true")
    check = subparsers.add_parser("check-report")
    check.add_argument("report", type=Path)
    subparsers.add_parser("self-test")
    args = parser.parse_args()
    try:
        if args.command in ("resolve", "prepare", "migrate", "self-test"):
            from skill_venv import reexec_into_venv
            reexec_into_venv("keleo-validate", ["jsonschema"])
        if args.command == "resolve":
            result = resolve(args.series, args.project_root)
        elif args.command == "prepare":
            result = prepare(args.series, args.at, args.fix, args.project_root)
        elif args.command == "migrate":
            result = migrate(args.workspace, args.fix, args.project_root)
        elif args.command == "self-test":
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(WorkspaceTests)
            return 0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1
        else:
            errors = report_errors(args.report)
            print("\n".join(errors) if errors else "Team-meeting report structure: OK")
            return int(bool(errors))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Team meeting failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
