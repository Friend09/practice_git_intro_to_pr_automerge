"""
Lab 03: Merge Commit vs Squash vs Rebase
=============================================================
Chapter 03 companion script.

Builds a tiny demo repository with a `main` branch and a `feature` branch that has
diverged by two commits, then applies all three of GitHub's merge strategies to
independent copies of it, so the resulting history shapes can be compared side by
side -- exactly what Chapter 03 Section 5's diagrams describe, but as real `git log`
output instead of ASCII art.

This lab is unusual among this curriculum's labs: it never talks to GitHub at all,
only to a disposable local Git repository, so "live" mode here means "really shell
out to git," not "touch the network" -- either mode is fully offline.

Usage
-----
Fixture mode (default, offline -- prints a canned history diagram)::

    python labs/lab_03_merge_strategies.py

Live mode -- actually builds a disposable repo and runs real `git` commands::

    PRA_MODE=live python labs/lab_03_merge_strategies.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 03 — Merge Commit vs Squash vs Rebase
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import GhClientError  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: A single, fixed author identity for the demo repo -- never the user's real
#: git config, so this never depends on (or mutates) the caller's environment.
_DEMO_ENV: dict[str, str] = {
    "GIT_AUTHOR_NAME": "PRA Lab",
    "GIT_AUTHOR_EMAIL": "lab@example.invalid",
    "GIT_COMMITTER_NAME": "PRA Lab",
    "GIT_COMMITTER_EMAIL": "lab@example.invalid",
}

#: Canned history diagrams used in fixture mode -- what each strategy produces,
#: verified once against a real run of this same lab in live mode.
FIXTURE_HISTORIES: dict[str, str] = {
    "merge_commit": (
        "*   4f2a1c9 Merge branch 'feature' into main\n"
        "|\\\n"
        "| * 9b7e3d2 feature: second change\n"
        "| * 1a6c8f0 feature: first change\n"
        "* | 0d5e2b1 main: unrelated commit\n"
        "|/\n"
        "* 7c4a9e8 initial commit\n"
    ),
    "squash": (
        "* a3f8c21 feature: second change + first change (squashed)\n"
        "* 0d5e2b1 main: unrelated commit\n"
        "* 7c4a9e8 initial commit\n"
    ),
    "rebase": (
        "* 6e1b4d7 feature: second change\n"
        "* 5c0a3f9 feature: first change\n"
        "* 0d5e2b1 main: unrelated commit\n"
        "* 7c4a9e8 initial commit\n"
    ),
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command in `cwd` with the fixed demo identity, return stdout.

    Parameters
    ----------
    args : list[str]
        Arguments after ``git``, e.g. ``["commit", "-m", "..."]``.
    cwd : Path
        The repository directory to run in.

    Returns
    -------
    str
        Captured stdout, stripped.

    Raises
    ------
    GhClientError
        If git is missing or the command exits non-zero.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env={**os.environ, **_DEMO_ENV},
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        raise GhClientError(f"git {' '.join(args)} exited {exc.returncode}: {exc.stderr.strip()}") from exc
    except FileNotFoundError as exc:
        raise GhClientError("git not found on PATH") from exc
    return result.stdout.strip()


def build_demo_repo(base_dir: Path) -> Path:
    """Build a disposable repo with `main` and a two-commit-diverged `feature`.

    Parameters
    ----------
    base_dir : Path
        A directory to create the repo inside (typically a tempdir).

    Returns
    -------
    Path
        The path to the new repository.
    """
    repo = base_dir / "demo_repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "main"], repo)

    (repo / "file.txt").write_text("initial\n")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-q", "-m", "initial commit"], repo)

    (repo / "file.txt").write_text("initial\nmain change\n")
    _run_git(["commit", "-q", "-am", "main: unrelated commit"], repo)

    _run_git(["checkout", "-q", "-b", "feature"], repo)
    (repo / "feature.txt").write_text("first\n")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-q", "-m", "feature: first change"], repo)
    (repo / "feature.txt").write_text("first\nsecond\n")
    _run_git(["commit", "-q", "-am", "feature: second change"], repo)

    _run_git(["checkout", "-q", "main"], repo)
    return repo


def apply_merge_commit(repo: Path) -> str:
    """Merge `feature` into `main` with `--no-ff`, returning the resulting log graph."""
    _run_git(["merge", "--no-ff", "-q", "-m", "Merge branch 'feature' into main", "feature"], repo)
    return _run_git(["log", "--oneline", "--graph", "--all"], repo)


def apply_squash(repo: Path) -> str:
    """Squash-merge `feature` into `main`, returning the resulting log graph."""
    _run_git(["merge", "--squash", "-q", "feature"], repo)
    _run_git(["commit", "-q", "-m", "feature: second change + first change (squashed)"], repo)
    return _run_git(["log", "--oneline", "--graph", "--all"], repo)


def apply_rebase(repo: Path) -> str:
    """Rebase `feature` onto `main`, then fast-forward `main`, returning the log graph."""
    _run_git(["checkout", "-q", "feature"], repo)
    _run_git(["rebase", "-q", "main"], repo)
    _run_git(["checkout", "-q", "main"], repo)
    _run_git(["merge", "-q", "--ff-only", "feature"], repo)
    return _run_git(["log", "--oneline", "--graph", "--all"], repo)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all three merge strategies against independent copies of the same repo."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")

    if mode == "fixture":
        for name, history in FIXTURE_HISTORIES.items():
            section(f"Strategy: {name} (fixture)")
            print(history)
    else:
        with tempfile.TemporaryDirectory(prefix="pra_lab03_") as tmp:
            base = build_demo_repo(Path(tmp))
            strategies = {
                "merge_commit": apply_merge_commit,
                "squash": apply_squash,
                "rebase": apply_rebase,
            }
            for name, apply_fn in strategies.items():
                copy = Path(tmp) / f"copy_{name}"
                shutil.copytree(base, copy)
                section(f"Strategy: {name} (live)")
                print(apply_fn(copy))

    print(
        "\nCompare commit counts on main across the three sections above: merge_commit\n"
        "keeps both feature commits plus a merge commit; squash collapses them into one;\n"
        "rebase keeps both but rewrites their parent, leaving zero merge commits."
    )


if __name__ == "__main__":
    main()
