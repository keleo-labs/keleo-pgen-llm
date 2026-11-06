#!/usr/bin/env python3
"""Regression checks for child-to-parent state Background mappings."""

import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "assess_practice", Path(__file__).resolve().parents[1] / "utils/assess-practice.py"
)
assess = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assess)

baseline = {"alphas": [{"name": "Parent", "states": [
    {"name": "Ready", "background": {"given": ["approved"]}},
    {"name": "Operating"},
]}]}
child = {"name": "Child", "contributesTo": "Parent", "states": [
    {"name": "Defined"}, {"name": "Built"},
]}
parent = {"name": "Parent", "states": [
    {"name": "Ready", "background": {
        "given": ["approved"],
        "alphaStates": [{"alphaName": "Child", "stateName": "Defined"}],
    }},
    {"name": "Operating", "background": {
        "alphaStates": [{"alphaName": "Child", "stateName": "Built"}],
    }},
]}

practice = {"alphas": [child, parent]}
check = assess.check_contributes_to_backgrounds
assert check(practice, baseline, "practice") == []
assert "must be redeclared" in check({"alphas": [child]}, baseline, "practice")[0]["message"]

parent["states"][1]["background"]["alphaStates"] = []
assert "Built" in check(practice, baseline, "practice")[0]["path"]
parent["states"][1]["background"]["alphaStates"] = [
    {"alphaName": "Child", "stateName": "Built"}
]
parent["states"][0]["background"].pop("given")
assert "removed an inherited" in check(practice, baseline, "practice")[0]["message"]
