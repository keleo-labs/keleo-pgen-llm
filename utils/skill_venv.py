#!/usr/bin/env python3
"""Shared virtualenv management for skills that need third-party Python packages.

Four skills needed the same three things: a venv that is not the system or
Homebrew interpreter, packages installed into it, and a way to re-enter it from
a script that was started with the wrong Python. This is that, once.

Why a venv at all, and never a bare `pip install`:

  * Most current distributions and Homebrew ship a Python marked
    externally-managed (PEP 668), where `pip install` into the system
    interpreter aborts, and `--break-system-packages` does what it says.
  * Two skills wanting different versions of the same package would otherwise
    fight over one site-packages.

Why outside the skill directory: a skill is mirrored into ~/.claude/skills and
~/.cursor/skills and rewritten by `sync.py --push`. A venv kept inside one would
be built twice and destroyed on redeploy. These live in
``~/.local/share/agent-skills/<skill>/venv`` instead, which is also where the
rest of a skill's own state belongs.

Use from a script:

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python-env"))
    from skill_venv import ensure_venv, reexec_into_venv

    reexec_into_venv("my-skill", ["requests"])   # returns already inside it

Use from a shell, or from a SKILL.md instruction:

    PY=$(python3 ../python-env/skill_venv.py my-skill requests)
    "$PY" scripts/thing.py

Standard library only, Python 3.9+, Linux and macOS.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

__all__ = ["ensure_venv", "reexec_into_venv", "venv_python", "VenvError"]


class VenvError(RuntimeError):
    """Raised with guidance a user can act on, not just a traceback."""


def _base_dir() -> Path:
    """Where skill venvs live. Overridable, mostly so the tests can redirect it."""
    override = os.environ.get("AGENT_SKILLS_HOME")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return root / "agent-skills"


def _check_name(skill: str) -> str:
    """A skill name is a single directory name, and nothing cleverer.

    Guards against two real mistakes: a caller passing a path fragment, and a
    shell that failed to split its arguments, which silently creates a
    directory named after the whole command line.
    """
    name = skill.strip()
    if not name or name in (".", "..") or not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise VenvError(
            f"invalid skill name {skill!r}: expected one directory name made of "
            f"letters, digits, dot, dash or underscore")
    return name


def venv_python(skill: str) -> Path:
    """The interpreter path for a skill's venv, whether or not it exists yet."""
    return _base_dir() / _check_name(skill) / "venv" / "bin" / "python"


def _missing_venv_module_help() -> str:
    """What to install when `python3 -m venv` is unavailable.

    Debian and Ubuntu split venv out of the base Python package, which is the
    single most common reason this fails on Linux. Nothing here assumes
    Homebrew: it is not present on most Linux machines, and not every macOS
    user has it either.
    """
    return (
        "python3 -m venv is unavailable. Install it:\n"
        "  Debian/Ubuntu   sudo apt install python3-venv\n"
        "  Fedora/RHEL     sudo dnf install python3-virtualenv\n"
        "  Arch            already present in the python package\n"
        "  macOS           included with python.org builds, Homebrew Python, "
        "and Xcode command line tools\n"
        "If your distribution's Python is too old, install a current one with "
        "pyenv, mise, or uv rather than replacing the system interpreter."
    )


def _create(venv_dir: Path) -> None:
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                       check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:                      # no interpreter at all
        raise VenvError(f"{sys.executable} is not runnable: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        if "ensurepip" in detail or "No module named venv" in detail:
            raise VenvError(_missing_venv_module_help()) from exc
        raise VenvError(f"could not create {venv_dir}:\n{detail}") from exc


def _installed(python: Path, module: str) -> bool:
    return subprocess.run([str(python), "-c", f"import {module}"],
                          capture_output=True).returncode == 0


def _import_name(package: str) -> str:
    """Best guess at what `pip install <package>` makes importable.

    Only used to skip work that is already done; a wrong guess costs one
    redundant pip call, never a wrong result.
    """
    known = {"python-dotenv": "dotenv", "python-pptx": "pptx",
             "pyyaml": "yaml", "pillow": "PIL", "beautifulsoup4": "bs4",
             "pymupdf": "fitz"}
    base = package.split("[")[0].split("==")[0].split(">")[0].split("<")[0].strip()
    return known.get(base.lower(), base.replace("-", "_"))


def ensure_venv(skill: str, packages: "list[str] | tuple[str, ...]" = (),
                *, quiet: bool = True) -> Path:
    """Create the skill's venv if absent, install any missing packages, return
    its interpreter. Idempotent: the common case runs one import check per
    package and touches the network not at all.
    """
    python = venv_python(skill)
    if not python.exists():
        _create(python.parent.parent)
    if not python.exists():
        raise VenvError(f"venv created but {python} is missing")

    wanted = [p for p in packages if not _installed(python, _import_name(p))]
    if wanted:
        cmd = [str(python), "-m", "pip", "install", "--disable-pip-version-check"]
        if quiet:
            cmd.append("-q")
        cmd += list(wanted)
        try:
            subprocess.run(cmd, check=True, capture_output=quiet, text=True)
        except subprocess.CalledProcessError as exc:
            raise VenvError(
                f"could not install {' '.join(wanted)} into {python.parent.parent}:\n"
                f"{(exc.stderr or exc.stdout or '').strip()}") from exc
    return python


def in_venv(skill: str) -> bool:
    try:
        return Path(sys.prefix).resolve() == venv_python(skill).parent.parent.resolve()
    except OSError:
        return False


def reexec_into_venv(skill: str, packages: "list[str] | tuple[str, ...]" = ()) -> None:
    """Restart the calling script inside the skill's venv, unless already there.

    Returns normally when there is nothing to do, so a script can call this
    unconditionally as its first statement.
    """
    if in_venv(skill):
        return
    python = ensure_venv(skill, packages)
    os.execv(str(python), [str(python), *sys.argv])


def main(argv: "list[str] | None" = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if args else 2
    skill, packages = args[0], args[1:]
    try:
        print(ensure_venv(skill, packages, quiet=True))
    except VenvError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
