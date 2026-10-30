#!/usr/bin/env python3
"""Validate series-local team-news state without fetching or changing evidence. Version: 2.0.0.

Usage: python3 utils/check-team-news.py [state.json] [--self-test]
Uses the existing keleo-validate virtualenv and shared python-env bootstrap.
"""

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "skills/team-meeting/references/news-state.schema.json"


def timestamp(value):
    if not re.fullmatch(r"\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)", value):
        raise ValueError("Expected a timezone-qualified timestamp")
    return datetime.fromisoformat(value.upper().replace("Z", "+00:00"))


def check_state(state):
    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    formats = FormatChecker()
    # jsonschema's date-time checker otherwise silently needs an optional package.
    @formats.checks("date-time", raises=(ValueError, TypeError))
    def valid_time(value):
        return not isinstance(value, str) or timestamp(value) is not None

    @formats.checks("uri", raises=ValueError)
    def valid_uri(value):
        if not isinstance(value, str):
            return True
        parts = urlsplit(value)
        return (bool(parts.scheme) and not re.search(r"\s|%(?![0-9a-fA-F]{2})", value)
                and (parts.scheme not in ("http", "https") or bool(parts.netloc)))

    errors = [f"{'/'.join(map(str, error.absolute_path))}: {error.message}"
              for error in Draft202012Validator(schema, format_checker=formats).iter_errors(state)]
    if errors:
        return errors

    def index(items, field, label):
        result = {}
        for item in items:
            key = item[field]
            if key in result:
                errors.append(f"Duplicate {label}: {key}")
            result[key] = item
        return result

    entities = index(state["watchlist"], "key", "entity key")
    snapshots = index(state["snapshots"], "id", "snapshot ID")
    index(state["runs"], "id", "run ID")
    records = set()
    for entity in entities.values():
        record = entity.get("record")
        if record:
            identity = (entity["type"], record["id"])
            if identity in records:
                errors.append(f"Duplicate verified identity: {identity}")
            records.add(identity)
        pointer = entity.get("lastSuccessfulSnapshotId")
        if pointer is not None and (pointer not in snapshots or
                snapshots[pointer]["entityKey"] != entity["key"]):
            errors.append(f"Invalid last successful snapshot: {entity['key']}")
        if entity["retained"] == (entity["retentionReason"] == "archived"):
            errors.append(f"Inconsistent retention: {entity['key']}")
    for snapshot in snapshots.values():
        entity = entities.get(snapshot["entityKey"])
        if entity is None or entity.get("record", {}).get("id") != snapshot["recordId"]:
            errors.append(f"Unresolved snapshot identity: {snapshot['id']}")
        index(snapshot["facts"], "field", f"fact field in {snapshot['id']}")
        for fact in snapshot["facts"]:
            if "changedAt" in fact and timestamp(fact["changedAt"]) > timestamp(snapshot["observedAt"]):
                errors.append(f"Future change in snapshot: {snapshot['id']}")
    for run in state["runs"]:
        if not (timestamp(run["windowStart"]) <= timestamp(run["windowEnd"]) <= timestamp(run["checkedAt"])):
            errors.append(f"Invalid collection window: {run['id']}")
        index(run["coverage"], "source", f"coverage source in {run['id']}")
        for coverage in run["coverage"]:
            if (coverage["status"] == "complete") == bool(coverage["gaps"]):
                errors.append(f"Inconsistent coverage: {run['id']}/{coverage['source']}")
        for pending in run["pendingChecks"]:
            for key in pending["entityKeys"]:
                if key not in entities:
                    errors.append(f"Unknown pending entity: {key}")
    return errors


class NewsStateTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / "skills/team-meeting/evals/files/news-state.json").read_text())

    def test_valid_state_and_schema(self):
        self.assertEqual(check_state(self.state), [])

    def test_invalid_money_dates_and_unknown_properties(self):
        for change in ("currency", "date", "uri", "extra"):
            state = deepcopy(self.state)
            if change == "currency":
                del state["snapshots"][0]["facts"][0]["value"]["currency"]
            elif change == "date":
                state["snapshots"][0]["observedAt"] = "not-a-date"
            elif change == "uri":
                state["snapshots"][0]["facts"][0]["sourceUri"] = "not a uri"
            else:
                state["unexpected"] = True
            self.assertTrue(check_state(state), change)

    def test_duplicate_identity_and_broken_success_pointer(self):
        state = deepcopy(self.state)
        state["watchlist"].append({**state["watchlist"][0], "key": "other"})
        self.assertTrue(any("Duplicate verified identity" in error for error in check_state(state)))
        state = deepcopy(self.state)
        state["watchlist"][0]["lastSuccessfulSnapshotId"] = "missing"
        self.assertTrue(any("Invalid last successful snapshot" in error for error in check_state(state)))

    def test_partial_coverage_and_pending_work(self):
        state = deepcopy(self.state)
        state["runs"][0]["coverage"][0]["status"] = "complete"
        state["runs"][0]["pendingChecks"][0]["entityKeys"] = ["missing"]
        errors = check_state(state)
        self.assertTrue(any("Inconsistent coverage" in error for error in errors))
        self.assertTrue(any("Unknown pending entity" in error for error in errors))


def main():
    from skill_venv import reexec_into_venv
    reexec_into_venv("keleo-validate", ["jsonschema"])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", nargs="?", type=Path)
    parser.add_argument("--version", action="version", version="2.0.0")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(NewsStateTests)).wasSuccessful() else 1
    if args.state is None:
        parser.error("give the series signals/state.json path")
    try:
        errors = check_state(json.loads(args.state.read_text()))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Validation failed: {error}\n")
    print("\n".join(errors) if errors else "Team-news state schema and integrity: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
