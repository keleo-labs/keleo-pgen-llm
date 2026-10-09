#!/usr/bin/env python3
"""Run a skill's eval cases with and without the skill, in isolated workspaces.

The global CLAUDE.md mandates grading every eval case twice -- once with the
skill, once without -- and reading the delta. Nothing here could do that:
`eval-skill-output.py --evals` grades directories a skill already produced, so
it measures output, never the skill's contribution.

Running the two arms naively in this repo measures almost nothing, because the
no-skill arm still inherits the project CLAUDE.md -- which restates the phase
pipeline, the alpha rules, the delineation thresholds and the structural
constraints -- plus whatever auto-memory has accumulated. Ponytail shipped
exactly this bug (a SessionStart hook fired on every arm) and had to supersede
a published benchmark over it. So isolation here is enforced and checked before
any cell runs, not assumed:

  - cells run in a temp directory outside any git repo, because inside one
    Claude Code shows the model recent commit messages
  - CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 and CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
  - --setting-sources project,local, so the user's global settings stay out
  - the with-skill arm gets exactly one skill copied in; the without-skill arm
    gets no .claude directory at all
  - arms are interleaved within a case, so a slow afternoon cannot masquerade
    as an arm difference

Workspaces are kept, so a change to an assertion is re-scored offline with
--rescore instead of paying for the generation twice.

Usage:
    # Prove the isolation, no API calls, no cost
    python3 utils/run-skill-eval.py --selftest

    # See exactly what a cell would run, without running it
    python3 utils/run-skill-eval.py --evals <evals.json> --case 4 --dry-run

    # Run one case, both arms, once each (this spends real money)
    python3 utils/run-skill-eval.py --evals <evals.json> --case 4 \\
        --arms with-skill,without-skill --runs 1

    # Re-grade kept workspaces after changing an assertion (no API)
    python3 utils/run-skill-eval.py --rescore runs/<stamp>

Cost warning: one /generate-method cell is a full three-phase pipeline --
a 30-50K word analysis, a 40-60K word mapping guide, JSON generation and
several verification gates. Start with one case and one run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"

ARMS = ("with-skill", "without-skill")

# Copied into every cell: the inputs a run resolves against. Deliberately not
# CLAUDE.md, not .claude/, not memory -- those are the contamination.
#
# `prompts/` is the judgement call. It holds the phase prompts the skill
# orchestrates, so including it makes the without-skill arm "without the
# skill's orchestration" rather than "without guidance" -- in the first real
# run that arm followed the phase prompts unaided and produced a complete,
# fully-passing practice. Both readings are defensible; the default includes
# them, because the question worth answering is what the skill's orchestration
# adds over the prompts it already ships, not what an unguided agent does.
# `--no-prompts` measures the harder comparison.
SHARED_INPUTS = ("deps", "references", "prompts", "utils")
SHARED_INPUTS_NO_PROMPTS = tuple(n for n in SHARED_INPUTS if n != "prompts")

ISOLATION_ENV = {
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
}

# The generation skills open with a mandatory plan-mode gate and will stop to ask
# a clarifying question. Headless there is nobody to answer, so the first real
# run of this harness produced a with-skill cell that wrote its prompt history,
# recorded "Answered: <pending>" and halted after 40 turns -- scoring 0 against a
# without-skill arm that ran to completion. That measured the gate, not the skill.
#
# Both arms get this, so it cannot bias the comparison.
NONINTERACTIVE_PREAMBLE = (
    "You are running non-interactively in a benchmark harness. There is no user "
    "to answer questions or approve a plan. Do not enter plan mode, do not call "
    "ExitPlanMode, and do not stop to ask anything. Where you would have asked, "
    "choose the most reasonable option, write the assumption down in the "
    "prompt-history file, and continue. Complete the whole task end to end."
)

# Anything here in a without-skill workspace means the arm is not actually
# running without the skill, and the measured delta is meaningless.
CONTAMINANTS = ("CLAUDE.md", ".claude", "AGENTS.md", ".cursor", "memory")


def _copy_inputs(dest: Path, inputs=SHARED_INPUTS):
    """Copy the resolvable inputs into a cell, following symlinks.

    deps/ and references/ are symlinks into ../../keleo-language; a cell lives
    outside this tree, so the targets must be materialised rather than linked.
    """
    for name in inputs:
        src = PROJECT_ROOT / name
        if not src.exists():
            continue
        shutil.copytree(src, dest / name, symlinks=False,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def prepare_cell(workdir: Path, arm: str, skill_name: str, inputs=SHARED_INPUTS):
    """Build one cell's workspace. Returns the workspace path."""
    workdir.mkdir(parents=True, exist_ok=True)
    _copy_inputs(workdir, inputs)
    for name in ("practices", "baselines", "bundles", "reports"):
        (workdir / name).mkdir(exist_ok=True)

    if arm == "with-skill":
        src = PROJECT_ROOT / ".claude" / "skills" / skill_name
        if not src.exists():
            raise FileNotFoundError(f"no such skill: {src}")
        dest = workdir / ".claude" / "skills" / skill_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, symlinks=False,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Supporting foundations the skill reads at runtime.
        for foundation in ("verification-foundation", "reporting-foundation",
                           "deck-foundation", "diagram-foundation"):
            fsrc = PROJECT_ROOT / ".claude" / "skills" / foundation
            if fsrc.exists():
                shutil.copytree(fsrc, workdir / ".claude" / "skills" / foundation,
                                symlinks=False,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return workdir


def check_isolation(workdir: Path, arm: str):
    """Return a list of contamination problems found in a prepared cell."""
    problems = []
    if arm == "without-skill":
        for name in CONTAMINANTS:
            if (workdir / name).exists():
                problems.append(f"without-skill cell contains {name}")
    else:
        for name in ("CLAUDE.md", "AGENTS.md"):
            if (workdir / name).exists():
                problems.append(f"with-skill cell contains ambient instructions: {name}")
        skills = workdir / ".claude" / "skills"
        if not skills.exists():
            problems.append("with-skill cell has no .claude/skills")

    # A cell inside a git repo shows the model recent commit messages.
    probe = workdir.resolve()
    for parent in [probe, *probe.parents]:
        if (parent / ".git").exists():
            problems.append(f"cell sits inside a git repo at {parent}")
            break
    return problems


def run_cell(workdir: Path, prompt: str, arm: str, timeout: int, dry_run: bool):
    """Run one headless Claude Code session in a prepared workspace."""
    cmd = [
        shutil.which("claude") or "claude",
        "-p", prompt,
        "--append-system-prompt", NONINTERACTIVE_PREAMBLE,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
        "--setting-sources", "project,local",
        "--strict-mcp-config",
    ]
    env = {**os.environ, **ISOLATION_ENV}

    if dry_run:
        return {"dryRun": True, "cmd": cmd,
                "env": {k: env[k] for k in ISOLATION_ENV}, "cwd": str(workdir)}

    started = time.time()
    proc = subprocess.run(cmd, cwd=workdir, env=env, capture_output=True,
                          text=True, timeout=timeout)
    duration_ms = int((time.time() - started) * 1000)

    try:
        payload = json.loads(proc.stdout)
    except (ValueError, TypeError):
        return {"error": "unparseable CLI output", "stderr": proc.stderr[-2000:],
                "duration_ms": duration_ms, "returncode": proc.returncode}

    usage = payload.get("usage") or {}
    return {
        "duration_ms": payload.get("duration_ms", duration_ms),
        "total_cost_usd": payload.get("total_cost_usd"),
        "num_turns": payload.get("num_turns"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        "is_error": payload.get("is_error", False),
        "returncode": proc.returncode,
    }


def grade_cell(workdir: Path, case: dict):
    """Grade a finished cell with the existing grader. No API, re-runnable."""
    target = workdir / case["directory"] if case.get("directory") else None
    if not target or not target.is_dir():
        candidates = sorted((workdir / "practices").glob("*")) + \
                     sorted((workdir / "baselines").glob("*"))
        candidates = [c for c in candidates if c.is_dir()]
        if not candidates:
            return {"error": "no output directory produced"}
        target = candidates[0]

    cmd = ["python3", str(PROJECT_ROOT / "utils" / "eval-skill-output.py"), str(target)]
    if case.get("baseline"):
        baseline = PROJECT_ROOT / case["baseline"]
        if baseline.exists():
            cmd += ["--baseline", str(baseline)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    try:
        return json.loads(proc.stdout)
    except (ValueError, TypeError):
        return {"error": "grader produced no JSON", "stderr": proc.stderr[-1000:]}


def aggregate(cells):
    """Per-arm means plus the with/without delta."""
    by_arm = {}
    for cell in cells:
        by_arm.setdefault(cell["arm"], []).append(cell)

    summary = {}
    for arm, group in by_arm.items():
        rates = [c["grading"]["summary"]["pass_rate"] for c in group
                 if c.get("grading", {}).get("summary")]
        errs = [c["grading"]["summary"]["error_pass_rate"] for c in group
                if c.get("grading", {}).get("summary")]
        toks = [c["metrics"]["total_tokens"] for c in group
                if c.get("metrics", {}).get("total_tokens")]
        durs = [c["metrics"]["duration_ms"] for c in group
                if c.get("metrics", {}).get("duration_ms")]
        costs = [c["metrics"]["total_cost_usd"] for c in group
                 if c.get("metrics", {}).get("total_cost_usd")]
        summary[arm] = {
            "cells": len(group),
            "mean_pass_rate": round(statistics.mean(rates), 3) if rates else None,
            "mean_error_pass_rate": round(statistics.mean(errs), 3) if errs else None,
            "median_total_tokens": int(statistics.median(toks)) if toks else None,
            "median_duration_ms": int(statistics.median(durs)) if durs else None,
            "median_cost_usd": round(statistics.median(costs), 4) if costs else None,
        }

    delta = {}
    a, b = summary.get("with-skill"), summary.get("without-skill")
    if a and b:
        for key in ("mean_pass_rate", "mean_error_pass_rate",
                    "median_total_tokens", "median_duration_ms", "median_cost_usd"):
            if a.get(key) is not None and b.get(key) is not None:
                delta[key] = round(a[key] - b[key], 4)
    return {"byArm": summary, "delta": delta}


def load_cases(evals_path, case_filter):
    data = json.loads(Path(evals_path).read_text(encoding="utf-8"))
    cases = data.get("evals", [])
    if case_filter:
        wanted = {c.strip() for c in case_filter.split(",") if c.strip()}
        cases = [c for c in cases
                 if str(c.get("id")) in wanted or c.get("name") in wanted]
    return data.get("skill_name", ""), cases


def selftest():
    """Prove the isolation holds before anything is measured with it.

    Ponytail's equivalent (_selftest_plugin_dir in its run.py) exists because a
    silently non-isolated arm produces a plausible number that means nothing.
    """
    failures = 0
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        root = Path(tmp)

        for arm in ARMS:
            cell = prepare_cell(root / arm, arm, "generate-method")
            problems = check_isolation(cell, arm)
            if problems:
                for p in problems:
                    print(f"XX {arm}: {p}")
                failures += len(problems)
            else:
                print(f"ok {arm}: no contamination in the prepared workspace")

        without = root / "without-skill"
        if (without / "deps").exists() and (without / "references").exists():
            print("ok without-skill still has the inputs a run resolves against")
        else:
            print("XX without-skill is missing deps/ or references/")
            failures += 1

        schema = without / "deps" / "language.schema.json"
        if schema.exists() and schema.stat().st_size > 0:
            print("ok symlinked inputs were materialised, not copied as dangling links")
        else:
            print("XX deps/language.schema.json did not survive the copy")
            failures += 1

        with_skill = root / "with-skill" / ".claude" / "skills"
        if (with_skill / "generate-method").exists():
            others = [p.name for p in with_skill.iterdir()
                      if p.is_dir() and not p.name.endswith("-foundation")]
            if others == ["generate-method"]:
                print("ok with-skill carries exactly one skill under test")
            else:
                print(f"XX with-skill carries extra skills: {others}")
                failures += 1
        else:
            print("XX with-skill is missing the skill under test")
            failures += 1

        # The env the cells would run under must actually disable the two
        # ambient sources; a typo here silently re-contaminates every arm.
        for key, want in ISOLATION_ENV.items():
            if {**os.environ, **ISOLATION_ENV}.get(key) != want:
                print(f"XX isolation env not applied: {key}")
                failures += 1
        print("ok isolation env disables ambient CLAUDE.md and auto-memory")

        # A check that cannot fail proves nothing, so plant each contaminant in
        # turn and require the checker to object.
        for planted in ("CLAUDE.md", ".claude", "memory"):
            probe = root / f"probe-{planted.strip('.')}"
            prepare_cell(probe, "without-skill", "generate-method")
            target = probe / planted
            if planted.endswith(".md"):
                target.write_text("ambient instructions", encoding="utf-8")
            else:
                target.mkdir(parents=True, exist_ok=True)
            if check_isolation(probe, "without-skill"):
                print(f"ok planted {planted} is detected")
            else:
                print(f"XX planted {planted} went undetected")
                failures += 1

        # And a cell inside a git repo must be refused, because Claude Code
        # shows the model recent commit messages there.
        gitprobe = root / "probe-git"
        prepare_cell(gitprobe, "without-skill", "generate-method")
        (gitprobe / ".git").mkdir()
        if any("git repo" in p for p in check_isolation(gitprobe, "without-skill")):
            print("ok a cell inside a git repo is detected")
        else:
            print("XX a cell inside a git repo went undetected")
            failures += 1

    print(f"\nselftest: {'isolation holds' if not failures else f'{failures} BROKEN'}")
    return 0 if not failures else 1


def rescore(run_dir):
    """Recompute grading and aggregates from kept workspaces. No API calls."""
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        run_dir = RUNS_DIR / run_dir.name
    results_path = run_dir / "results.json"
    if not results_path.exists():
        sys.exit(f"no results.json in {run_dir}")

    previous = json.loads(results_path.read_text(encoding="utf-8"))
    cells = previous.get("cells", [])
    for cell in cells:
        workdir = Path(cell["workdir"])
        if workdir.is_dir():
            cell["grading"] = grade_cell(workdir, cell["case"])

    out = {**previous, "cells": cells, "aggregate": aggregate(cells), "rescored": True}
    results_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (run_dir / "benchmark.json").write_text(
        json.dumps(out["aggregate"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["aggregate"], indent=2))
    print(f"\nrescored {len(cells)} cells from {run_dir} (no API calls)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Run skill eval cases with and without the skill, in isolated workspaces")
    parser.add_argument("--evals", help="Path to an evals.json")
    parser.add_argument("--case", help="Comma-separated eval ids or names (default: all)")
    parser.add_argument("--arms", default=",".join(ARMS),
                        help=f"Comma-separated arms (default: {','.join(ARMS)})")
    parser.add_argument("--runs", type=int, default=1, help="Runs per cell (default: 1)")
    parser.add_argument("--timeout", type=int, default=7200,
                        help="Per-cell timeout in seconds (default: 7200)")
    parser.add_argument("--no-prompts", action="store_true",
                        help="Withhold prompts/ from cells, so the without-skill arm "
                             "has no phase prompts to follow either")
    parser.add_argument("--dry-run", action="store_true",
                        help="Prepare and check cells, print the command, run nothing")
    parser.add_argument("--selftest", action="store_true",
                        help="Prove the isolation holds (no API, no cost)")
    parser.add_argument("--rescore", help="Re-grade kept workspaces from a run dir (no API)")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.rescore:
        sys.exit(rescore(args.rescore))
    if not args.evals:
        parser.error("give --evals, --rescore or --selftest")

    # An unproven harness produces numbers nobody should act on.
    if selftest():
        sys.exit("isolation does not hold; refusing to run cells")
    print()

    skill_name, cases = load_cases(args.evals, args.case)
    if not cases:
        sys.exit("no matching eval cases")
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    cells = []
    for case in cases:
        for run_index in range(args.runs):
            # Interleave arms inside a case so drift over the run cannot be
            # read as an arm difference.
            for arm in arms:
                label = f"{case.get('name', case.get('id'))}__{arm}__{run_index}"
                print(f"[{label}] preparing", flush=True)
                # Cells live outside the repo; a kept workspace is moved back
                # under runs/ afterwards.
                staging = Path(tempfile.mkdtemp(prefix="keleo-cell-", dir="/tmp"))
                try:
                    cell_dir = prepare_cell(
                        staging / "ws", arm, skill_name,
                        SHARED_INPUTS_NO_PROMPTS if args.no_prompts else SHARED_INPUTS)
                    problems = check_isolation(cell_dir, arm)
                    if problems:
                        for p in problems:
                            print(f"  XX {p}")
                        sys.exit("refusing to run a contaminated cell")

                    metrics = run_cell(cell_dir, case["prompt"], arm,
                                       args.timeout, args.dry_run)
                    if args.dry_run:
                        print(f"  would run: {' '.join(metrics['cmd'][:6])} ...")
                        print(f"  cwd: {metrics['cwd']}")
                        print(f"  env: {metrics['env']}")
                        continue

                    kept = run_dir / label
                    shutil.move(str(cell_dir), str(kept))
                    cells.append({
                        "case": case, "arm": arm, "run": run_index,
                        "workdir": str(kept), "metrics": metrics,
                        "grading": grade_cell(kept, case),
                    })
                    print(f"  done in {metrics.get('duration_ms', 0) / 1000:.0f}s", flush=True)
                finally:
                    shutil.rmtree(staging, ignore_errors=True)

    if args.dry_run:
        print("\ndry run: nothing executed, nothing spent")
        return 0

    out = {"stamp": stamp, "skill": skill_name, "arms": arms,
           "runs": args.runs, "cells": cells, "aggregate": aggregate(cells)}
    (run_dir / "results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (run_dir / "benchmark.json").write_text(
        json.dumps(out["aggregate"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["aggregate"], indent=2))
    print(f"\nworkspaces kept in {run_dir}; re-grade with --rescore {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
