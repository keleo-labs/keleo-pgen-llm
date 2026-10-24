#!/usr/bin/env python3
"""Regression scenarios for public tooling issues #42, #43, #46, #47 and #48."""
import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils._shared import check_dependency_versions, version_satisfies_range


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "utils" / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


post = module("post-validate-method")
scan = module("scan-corpus")
sync = module("sync-practices")
audit = module("audit-bundle-freshness")
assess = module("assess-practice")
summary = module("practice-summary")
grader = module("eval-skill-output")


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def run_main(mod, args):
    output = io.StringIO()
    with patch.object(sys, "argv", [mod.__file__, *args]), redirect_stdout(output):
        try:
            mod.main()
        except SystemExit as exc:
            return exc.code, json.loads(output.getvalue())
    raise AssertionError("main did not exit")


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    directory = root / "practices" / "source"
    practice = {"kind": "practice", "name": "Example", "version": "1.0.0"}
    write(directory / "practice.json", practice)
    write(directory / "baseline.json", {"kind": "practiceBaseline"})
    write(directory / "method.json", {"kind": "method"})
    write(directory / "changes.json", {"kind": "changeRequest"})
    write(directory / "working.json", ["working data"])
    # Given mixed document kinds, when validated, only extension practices are linted.
    with patch.object(post, "run_lint", return_value={"status": "PASS", "final_errors": 0}) as lint:
        code, report = run_main(post, [str(directory)])
        assert code == 0 and report["total_errors"] == 0, report
        assert lint.call_count == 1 and report["skipped_file_count"] == 4
    (directory / "broken.json").write_text("{")
    with patch.object(post, "run_lint", return_value={"status": "FAIL"}):
        code, report = run_main(post, [str(directory)])
        assert code == 1 and report["total_errors"] == 2, report
    (directory / "broken.json").unlink()
    with patch.object(scan.subprocess, "run") as process:
        assert scan.assess(directory / "working.json", None) == ([], True)
        assert scan.assess(directory / "changes.json", None) == ([], True)
        process.assert_not_called()
    with patch.object(scan, "get_project_root", return_value=root), \
         patch.object(scan, "candidate_documents", return_value=[directory / "practice.json"]), \
         patch.object(scan, "assess", return_value=scan.scan_failure("document could not be read")):
        code, report = run_main(scan, ["--json"])
        assert code == 1 and report["summary"]["unreadable"] == ["practices/source/practice.json"]

    # Given a subprocess timeout, when scanned in either mode, the run fails visibly.
    for runner in (scan.assess, scan.validate):
        with patch.object(scan, "resolve_context", return_value=([], True)), \
             patch.object(scan, "resolve_context_paths", return_value=(["baseline.json"], [], True)), \
             patch.object(scan.subprocess, "run", side_effect=subprocess.TimeoutExpired("validator", 300)):
            findings, complete = runner(directory / "practice.json", "schema.json")
            assert not complete and "timed out" in findings[0]["message"]
    with patch.object(scan, "get_project_root", return_value=root), \
         patch.object(scan, "candidate_documents", return_value=[directory / "practice.json"]), \
         patch.object(scan, "assess", return_value=scan.scan_failure("timed out")):
        code, report = run_main(scan, ["--json", "--category", "outcome-refs"])
        assert code == 1 and report["summary"]["documentsFailed"] == 1
        assert report["summary"]["scanFailures"][0]["reason"] == "timed out"

    # Given equal versions with changed content, sync reports drift without overwriting.
    target = root / "practices" / "target" / "practice.json"
    write(target, {**practice, "description": "Target-only edit"})
    original = target.read_bytes()
    actions, _ = sync.sync_practices(directory, fix=True)
    assert actions[0]["actions"][0]["status"] == "content_differs"
    assert target.read_bytes() == original
    write(target, practice)
    actions, _ = sync.sync_practices(directory)
    assert actions[0]["actions"][0]["status"] == "up_to_date"
    write(target, {**practice, "version": "2.0.0"})
    actions, _ = sync.sync_practices(directory, fix=True)
    assert actions[0]["actions"][0]["status"] == "target_newer"
    write(target, practice)
    method = directory / "method.json"
    write(method, {"kind": "method", "name": "Collection", "practices": [{**practice, "description": "Embedded edit"}]})
    original = method.read_bytes()
    assert sync.sync_embedded_practices(root, fix=True)[0]["status"] == "content-differs"
    assert method.read_bytes() == original

    # Given a stale constraint and equal-version drift, a bundle audit reports both.
    bundle = root / "bundles" / "example.keleo"
    bundle.parent.mkdir()
    bundled = {**practice, "description": "Old content", "dependencyVersions": [
        {"documentName": "Foundation", "versionRange": "^1.0.0"}]}
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"documents": [
            {"documentName": "Example", "path": "documents/example.json"},
            {"documentName": "Foundation", "path": "documents/foundation.json"}]}))
        archive.writestr("documents/example.json", json.dumps(bundled))
        archive.writestr("documents/foundation.json", json.dumps({"name": "Foundation", "kind": "practiceBaseline", "version": "2.1.0"}))
    report = audit.audit_bundle(bundle, audit.build_source_index(root), root)
    assert report["documents"][0]["status"] == "content-differs", report
    assert len(report["versionFindings"]) == 1, report

for version, constraint, expected in [("2.1.0", "^1.7.1", False), ("2.1.0", "^2.0.0", True),
                                      ("0.2.3", "^0.2.0", True), ("0.3.0", "^0.2.0", False),
                                      ("1.2", "~1.2.0", True), ("2.1.0", ">=2.0.0 <3.0.0", True)]:
    assert version_satisfies_range(version, constraint) is expected
assert not check_dependency_versions({"dependencyVersions": [{"documentName": "Missing", "versionRange": "^1.0.0"}]}, [])

# Given an orchestration-only practice, references resolve against merged placements.
stages = [{"patternName": "Start", "relationship": "sequential", "seq": 1},
          {"orchestrationName": "Finish", "relationship": "sequential", "seq": 2},
          {"patternName": "Review", "relationship": "nested", "relativeTo": {"patternName": "Start"}}]
contribution = {"orchestrationName": "Delivery", "recognizedAtStage": {"orchestrationName": "Finish"},
                "stageForecastWeights": [{"stage": {"patternName": "Start"}, "weight": 0.3},
                                         {"stage": {"orchestrationName": "Finish"}, "weight": 1.0}]}
data = {"kind": "practice", "patternOrchestrations": [{"name": "Delivery", "stages": stages[1:]}],
        "outcomes": [{"name": "Completed", "measureDescription": "Completed stages", "objectiveContributions": [contribution]}]}
baseline = {"patternOrchestrations": [{"name": "Delivery", "stages": stages[:1]}]}
assert not assess.check_outcomes(data, "practice", baseline)
assert summary.summarize_outcome(data["outcomes"][0])["objectiveContributions"][0] == contribution
bad = copy.deepcopy(data)
bad["outcomes"][0]["objectiveContributions"][0]["recognizedAtStage"] = {"patternName": "Review"}
assert any("not found" in i["message"] for i in assess.check_outcomes(bad, "practice", baseline))
bad = copy.deepcopy(data)
bad["outcomes"][0]["objectiveContributions"][0]["stageForecastWeights"][1]["weight"] = 0.1
assert any("decrease" in i["message"] for i in assess.check_outcomes(bad, "practice", baseline))
bad["outcomes"][0]["objectiveContributions"][0]["patternName"] = "Ambiguous"
assert any("exactly one" in i["message"] for i in assess.check_outcomes(bad, "practice", baseline))

# Given a method member naming a later member's pattern, order does not hide it.
pattern_outcome = {"outcomes": [{"name": "Completed", "measureDescription": "Views",
    "objectiveContributions": [{"patternName": "Later", "recognizedAtPatternViewName": "Done"}]}]}
later = {"patterns": [{"name": "Later", "patternViews": [{"name": "Done"}]}]}
assert not [i for i in assess.check_outcomes({"practices": [pattern_outcome, later]}, "method")
            if i["category"] == "outcome-refs"]

# Given a mutation planting a valid value, selftest distinguishes an unusable mutation.
fixture = json.loads(grader.GOOD_FIXTURE.read_text())
baseline_fixture = json.loads(grader.FIXTURE_BASELINE.read_text())
assert not baseline_fixture.get("baselinePracticeNames")
valid_type = baseline_fixture["narrativeTypes"][0]["name"]
mutation = ("xref:narrative-type", "invented-narrative-type", "invalid type",
            lambda d: d["narratives"][0].__setitem__("narrativeTypeName", valid_type))
output = io.StringIO()
with patch.object(grader, "_load_mutations", return_value=[mutation]), \
     patch.object(grader, "_grade_fixture", return_value={"xref:narrative-type": True}) as grade, \
     redirect_stdout(output):
    assert grader.selftest() == 1
assert grade.call_count == 1
assert "planted value is valid" in output.getvalue() and "not caught by" not in output.getvalue()
print("PASS: mixed documents, scan failures, content drift, version constraints and orchestration outcomes")

# Optional kept agent runs: grade only the scoped contract, not unrelated practice minimums.
for run_directory in sys.argv[1:]:
    run_path = Path(run_directory)
    run = json.loads((run_path / "results.json").read_text())
    grading = []
    for cell in run["cells"]:
        result_path = Path(cell["workdir"]) / cell["case"]["directory"] / "result.json"
        result = json.loads(result_path.read_text())
        outcome = result["outcomes"][0]
        oc = outcome["objectiveContributions"][0]
        name = cell["case"]["name"]
        if name == "pattern-outcome":
            assert oc == {"patternName": "Delivery", "recognizedAtPatternViewName": "Done",
                          "forecastWeights": [{"patternViewName": "Start", "weight": 0.3},
                                              {"patternViewName": "Done", "weight": 1.0}]}
        else:
            assert result["patterns"] == [] and oc["orchestrationName"] == "Delivery"
            assert "patternName" not in oc and "forecastWeights" not in oc
            if name == "composition-outcome":
                assert oc["recognizedAtStage"] == {"orchestrationName": "Finish"}
                assert oc["stageForecastWeights"] == [
                    {"stage": {"patternName": "Start"}, "weight": 0.3},
                    {"stage": {"orchestrationName": "Finish"}, "weight": 1.0}]
            elif name == "preserve-stage-outcome":
                ref = {"patternName": "Review", "relativeTo": {"orchestrationName": "Plan"}}
                assert outcome["description"] == "Completed review"
                assert oc["recognizedAtStage"] == ref
                assert oc["stageForecastWeights"] == [{"stage": ref, "weight": 1.0}]
            else:
                raise AssertionError(f"Unrecognised scoped case: {name}")
        grading.append({"case": name, "arm": cell["arm"], "status": "PASS",
                        "evidence": str(result_path), "metrics": cell["metrics"]})
    (run_path / "objective-grading.json").write_text(json.dumps({
        "scope": "Objective contribution contract only; full practice scores are not applicable",
        "results": grading,
        "conclusion": "Both arms passed; these cases show regression coverage, not a measured skill advantage",
    }, indent=2) + "\n")
    print(f"PASS: {len(grading)} scoped agent outputs in {run_path}")
