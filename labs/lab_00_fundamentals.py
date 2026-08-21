"""
Lab 00: Fundamentals -- Git, Pull Requests & GitHub Actions
=============================================================
Chapter 00 companion script.

Builds a disposable local repo and walks it through the fundamentals this whole
curriculum assumes you already have: the three areas (working directory, staging
area, repository), the add -> commit cycle, `git log`, `git diff`, and a first,
simple branch + merge -- deliberately kept to the plainest case (a fast-forward),
leaving the three real merge STRATEGIES to Chapter 03. It then walks the end-to-end
lifecycle of a pull request -- branch, push, open, review, checks, merge -- shows
what a raw PR object looks like the moment AFTER a successful merge, and parses a
minimal GitHub Actions workflow file so "what even IS a workflow file" has a
concrete, working answer before Chapter 01 starts using the vocabulary and
Chapter 08 goes deep on its full anatomy.

Usage
-----
Fixture mode (default, offline -- prints a canned transcript)::

    python labs/lab_00_fundamentals.py

Live mode -- actually builds a disposable repo and runs real `git` commands::

    PRA_MODE=live python labs/lab_00_fundamentals.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 00 — Fundamentals: Git, Pull Requests & GitHub Actions
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import GhClientError, load_fixture  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: A single, fixed author identity for the demo repo -- never the user's real git
#: config, so this never depends on (or mutates) the caller's environment.
_DEMO_ENV: dict[str, str] = {
    "GIT_AUTHOR_NAME": "PRA Lab",
    "GIT_AUTHOR_EMAIL": "lab@example.invalid",
    "GIT_COMMITTER_NAME": "PRA Lab",
    "GIT_COMMITTER_EMAIL": "lab@example.invalid",
}

#: Canned transcripts used in fixture mode -- verified once against a real run of
#: this same lab in live mode.
FIXTURE_TRANSCRIPT: dict[str, str] = {
    "status_untracked": (
        "On branch main\n"
        "No commits yet\n"
        "Untracked files:\n"
        '  (use "git add <file>..." to include in what will be committed)\n'
        "\tREADME.md\n"
    ),
    "status_staged": (
        "On branch main\n"
        "No commits yet\n"
        "Changes to be committed:\n"
        '  (use "git rm --cached <file>..." to unstage)\n'
        "\tnew file:   README.md\n"
    ),
    "status_clean": "On branch main\nnothing to commit, working tree clean\n",
    "log_two_commits": (
        "2b1c9a0 second: mention the sandbox\n" "9f3e7d1 first commit: add README\n"
    ),
    "diff_unstaged": (
        "diff --git a/README.md b/README.md\n"
        "index 8f3e1a2..1c9b0d4 100644\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1,2 @@\n"
        " # Demo Repo\n"
        "+edited but not staged yet\n"
    ),
    "log_after_merge": (
        "3d8e2a1 second: mention the sandbox\n"
        "9f3e7d1 first commit: add README\n"
        "(feature branch fast-forwarded into main -- no separate merge commit)\n"
    ),
}

#: The end-to-end pull-request lifecycle, plain-language, in order. Chapter 01
#: names this same arc "the Airlock"; this chapter is the pre-vocabulary version.
PR_LIFECYCLE_STAGES: list[dict[str, str]] = [
    {
        "stage": "Branch created",
        "what_happens": "A new branch is created off main, e.g. `git checkout -b fix/readme-typo`.",
    },
    {
        "stage": "Commits made locally",
        "what_happens": "The add -> commit cycle from Steps 1-2 above, on that branch.",
    },
    {
        "stage": "Branch pushed",
        "what_happens": "`git push origin fix/readme-typo` uploads the branch's commits to GitHub.",
    },
    {
        "stage": "PR opened",
        "what_happens": "`gh pr create` (or the GitHub UI) asks GitHub to compare the branch against main and open a PR.",
    },
    {
        "stage": "Checks run",
        "what_happens": "GitHub Actions workflows fire automatically (Step 6 below, Chapter 08-09) and report pass/fail.",
    },
    {
        "stage": "Review requested/given",
        "what_happens": "A human (or nobody, if none is required) reviews the diff and approves or requests changes.",
    },
    {
        "stage": "Merge becomes available",
        "what_happens": "Once every required check passes and required reviews are satisfied, GitHub enables the merge button (or native auto-merge, Chapter 06, fires on its own).",
    },
    {
        "stage": "Merged",
        "what_happens": "GitHub combines the branch into main using whichever strategy is configured (Chapter 03) and marks the PR merged: true.",
    },
    {
        "stage": "Branch cleaned up",
        "what_happens": "The now-merged branch is typically deleted -- its commits live on in main's history regardless.",
    },
]

#: A minimal, real, valid GitHub Actions workflow -- deliberately smaller than
#: this repo's actual ci.yml (Chapter 08 parses that one), just enough to show
#: the four pieces every workflow file has: name, trigger, job(s), step(s).
MINIMAL_WORKFLOW_YAML: str = """
name: CI

on:
  pull_request:
    paths:
      - 'sandbox/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Run tests
        run: python -m pytest
"""


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command in `cwd` with the fixed demo identity, return stdout.

    Parameters
    ----------
    args : list[str]
        Arguments after ``git``, e.g. ``["status"]``.
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
        raise GhClientError(
            f"git {' '.join(args)} exited {exc.returncode}: {exc.stderr.strip()}"
        ) from exc
    except FileNotFoundError as exc:
        raise GhClientError("git not found on PATH") from exc
    return result.stdout.strip()


def init_demo_repo(base_dir: Path) -> Path:
    """Create and initialize a disposable, empty repo inside `base_dir`.

    Parameters
    ----------
    base_dir : Path
        A directory to create the repo inside (typically a tempdir).

    Returns
    -------
    Path
        The path to the new, empty (no commits yet) repository.
    """
    repo = base_dir / "demo_repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "main"], repo)
    return repo


def demonstrate_three_areas(repo: Path) -> dict[str, str]:
    """Walk a new file through untracked -> staged -> committed, capturing `git status` each time.

    Parameters
    ----------
    repo : Path
        An initialized, empty git repository.

    Returns
    -------
    dict[str, str]
        {"untracked": ..., "staged": ..., "clean": ...} -- each value is that
        step's `git status` output.
    """
    (repo / "README.md").write_text("# Demo Repo\n")
    untracked = _run_git(["status"], repo)

    _run_git(["add", "README.md"], repo)
    staged = _run_git(["status"], repo)

    _run_git(["commit", "-q", "-m", "first commit: add README"], repo)
    clean = _run_git(["status"], repo)

    return {"untracked": untracked, "staged": staged, "clean": clean}


def demonstrate_diff_and_second_commit(repo: Path) -> dict[str, str]:
    """Edit the tracked file, show `git diff`, then stage and commit the change.

    Parameters
    ----------
    repo : Path
        A repo with at least one commit already (see :func:`demonstrate_three_areas`).

    Returns
    -------
    dict[str, str]
        {"diff": ..., "log": ...} -- the unstaged diff, then `git log` after the
        second commit.
    """
    with (repo / "README.md").open("a") as f:
        f.write("edited but not staged yet\n")
    diff = _run_git(["diff"], repo)

    _run_git(["commit", "-q", "-am", "second: mention the sandbox"], repo)
    log = _run_git(["log", "--oneline"], repo)

    return {"diff": diff, "log": log}


def demonstrate_branch_and_merge(repo: Path) -> str:
    """Create a branch, commit on it, merge it back -- the simplest case: a fast-forward.

    Deliberately the plainest possible merge (no divergence on `main` in the
    meantime, so Git can just move the pointer forward) -- the three real merge
    STRATEGIES for the non-trivial case live in Chapter 03.

    Parameters
    ----------
    repo : Path
        A repo with at least one commit already.

    Returns
    -------
    str
        `git log --oneline --all` after the merge.
    """
    _run_git(["checkout", "-q", "-b", "feature"], repo)
    (repo / "NOTES.md").write_text("a note from the feature branch\n")
    _run_git(["add", "NOTES.md"], repo)
    _run_git(["commit", "-q", "-m", "add a notes file on the feature branch"], repo)

    _run_git(["checkout", "-q", "main"], repo)
    _run_git(["merge", "-q", "--ff-only", "feature"], repo)

    return _run_git(["log", "--oneline", "--all"], repo)


def fetch_merged_pr_example() -> dict:
    """Return a raw PR object the moment AFTER a successful merge.

    Unlike every other lab in this curriculum, this is a fixed illustrative
    example regardless of `PRA_MODE` -- this lab's "live" toggle governs whether
    the GIT steps above run real subprocess commands, never whether this step
    touches GitHub (it never does).

    Returns
    -------
    dict
        The raw pull request payload -- see :func:`describe_successful_merge` for
        the fields that specifically mark success.
    """
    return load_fixture("pr_merged_example")


def describe_successful_merge(pr: dict) -> dict:
    """Extract the specific fields that mark a PR as successfully merged.

    A merged PR is `state == "closed"` -- but so is a PR someone just closed
    without merging. The field that actually distinguishes "merged" from "closed
    without merging" is the boolean `merged` itself (Chapter 04 covers reading PR
    data in full depth; this is the one fact worth knowing this early).

    Parameters
    ----------
    pr : dict
        A raw PR payload, as returned by :func:`fetch_merged_pr_example`.

    Returns
    -------
    dict
        {"state": ..., "merged": ..., "merge_commit_sha": ..., "merged_at": ...}
    """
    return {
        "state": pr["state"],
        "merged": pr["merged"],
        "merge_commit_sha": pr.get("merge_commit_sha"),
        "merged_at": pr.get("merged_at"),
    }


def describe_minimal_workflow(yaml_text: str) -> dict:
    """Parse a workflow file into the four pieces every workflow has (Ch 00 §10-11).

    A deliberately small subset of what Chapter 08's `lab_08_actions_anatomy.py`
    does -- this function only needs to show that name/trigger/job/steps exist and
    are readable, not the full anatomy (jobs plural, permissions, matrix, etc.).

    Parameters
    ----------
    yaml_text : str
        Raw workflow YAML text, e.g. :data:`MINIMAL_WORKFLOW_YAML`.

    Returns
    -------
    dict
        {"name": ..., "trigger": [...], "job_id": ..., "runs_on": ...,
         "step_names": [...]}
    """
    doc = yaml.safe_load(yaml_text)
    job_id, job = next(iter(doc["jobs"].items()))
    # PyYAML parses a bare `on:` key as the boolean True (YAML 1.1) -- this repo's
    # real workflow files always quote or structure it so that doesn't happen, but
    # a defensive lookup covers both spellings (same trap Chapter 08's lab guards
    # against).
    trigger_raw = doc.get("on") or doc.get(True) or {}
    return {
        "name": doc.get("name"),
        "trigger": (
            list(trigger_raw.keys()) if isinstance(trigger_raw, dict) else [trigger_raw]
        ),
        "job_id": job_id,
        "runs_on": job.get("runs-on"),
        "step_names": [
            s.get("name", s.get("uses", s.get("run"))) for s in job.get("steps", [])
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full walkthrough: three areas, diff, second commit, branch, merge,
    the PR lifecycle, a successful-merge example, and a minimal workflow file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")

    if mode == "fixture":
        section("Step 1: untracked -> staged -> committed (fixture)")
        print(FIXTURE_TRANSCRIPT["status_untracked"])
        print(FIXTURE_TRANSCRIPT["status_staged"])
        print(FIXTURE_TRANSCRIPT["status_clean"])

        section("Step 2: edit, diff, second commit (fixture)")
        print(FIXTURE_TRANSCRIPT["diff_unstaged"])
        print(FIXTURE_TRANSCRIPT["log_two_commits"])

        section("Step 3: branch + fast-forward merge (fixture)")
        print(FIXTURE_TRANSCRIPT["log_after_merge"])
    else:
        with tempfile.TemporaryDirectory(prefix="pra_lab00_") as tmp:
            repo = init_demo_repo(Path(tmp))

            section("Step 1: untracked -> staged -> committed (live)")
            areas = demonstrate_three_areas(repo)
            print(areas["untracked"])
            print(areas["staged"])
            print(areas["clean"])

            section("Step 2: edit, diff, second commit (live)")
            result = demonstrate_diff_and_second_commit(repo)
            print(result["diff"])
            print(result["log"])

            section("Step 3: branch + fast-forward merge (live)")
            print(demonstrate_branch_and_merge(repo))

    print(
        "\nThree areas, one direction: working directory -> (git add) -> staging area\n"
        "-> (git commit) -> repository history. A branch is just a movable pointer to a\n"
        "commit; a merge combines two branches' histories. This was the SIMPLEST case\n"
        "(a fast-forward, no real combining needed) -- Chapter 03 covers what happens\n"
        "when both branches have moved and a real merge decision is required."
    )

    section("Step 4: the end-to-end pull-request lifecycle")
    for i, item in enumerate(PR_LIFECYCLE_STAGES, start=1):
        print(f"  [{i}] {item['stage']}")
        print(f"      {item['what_happens']}")

    section("Step 5: what a SUCCESSFUL merge actually looks like, in the data")
    merged_pr = fetch_merged_pr_example()
    summary = describe_successful_merge(merged_pr)
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(
        "\nNote: state == 'closed' alone is NOT proof of a successful merge -- a PR closed\n"
        "without merging is also 'closed'. merged == True plus a real merge_commit_sha are\n"
        "the fields that actually distinguish success (Chapter 04 goes deep on reading PR data)."
    )

    section("Step 6: what a GitHub Actions workflow file actually is")
    workflow = describe_minimal_workflow(MINIMAL_WORKFLOW_YAML)
    print(f"  name: {workflow['name']}")
    print(f"  trigger (on:): {workflow['trigger']}")
    print(f"  job '{workflow['job_id']}' runs-on={workflow['runs_on']}:")
    for i, step_name in enumerate(workflow["step_names"], start=1):
        print(f"    step {i}: {step_name}")

    print(
        "\nThis is what fires at step [5] of the PR lifecycle above: a YAML file committed\n"
        "under .github/workflows/, with a NAME, a TRIGGER (on:), and one or more JOBS made\n"
        "of ordered STEPS. That's the whole shape -- Chapter 08 goes deep on every piece of\n"
        "it, and Chapters 09-13 cover triggers, contexts, tokens, and debugging in full."
    )


if __name__ == "__main__":
    main()
