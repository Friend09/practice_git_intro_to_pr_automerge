"""
Lab 02: Refs, Branches & What a PR Really Is
=============================================================
Chapter 02 companion script.

Demonstrates the two layers Chapter 02 draws a line between: the raw Git refs
GitHub maintains for every open pull request (`refs/pull/N/head`,
`refs/pull/N/merge`), and the higher-level PR object the REST API hands back,
including the computed, sometimes-null `mergeable_state` field.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_02_pr_refs.py

Live mode, against a real PR on the sandbox repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_02_pr_refs.py --pr 1

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 02 — Refs, Branches & What a PR Really Is
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import GhClientError, load_fixture, run_gh  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def list_pr_refs(repo: str) -> list[dict[str, str]]:
    """List the Git refs GitHub maintains for open pull requests (Chapter 02 §3-4).

    Unlike every other lab in this curriculum, this does not go through
    `pr_automerge.gh_client.run_gh` -- that wrapper is specifically for the `gh`
    CLI's API surface, and this function is deliberately going *underneath* the
    API to plain Git itself, via `git ls-remote`, to show that PR refs are
    ordinary refs a normal git client can see without any GitHub-specific tooling.

    Parameters
    ----------
    repo : str
        "owner/name" -- only used to build the live remote URL.

    Returns
    -------
    list[dict]
        Each item: {"ref": "refs/pull/101/head", "sha": "..."}.

    Raises
    ------
    GhClientError
        If `git` is not on PATH, or `PRA_MODE=live` without network access.
    """
    mode = os.environ.get("PRA_MODE", "fixture")
    if mode == "fixture":
        return load_fixture("git_refs_sample")["refs"]

    remote_url = f"https://github.com/{repo}.git"
    try:
        result = subprocess.run(
            ["git", "ls-remote", remote_url, "refs/pull/*", "refs/heads/main"],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        raise GhClientError(f"git ls-remote exited {exc.returncode}: {exc.stderr.strip()}") from exc
    except FileNotFoundError as exc:
        raise GhClientError("git not found on PATH") from exc

    refs: list[dict[str, str]] = []
    for line in result.stdout.strip().splitlines():
        sha, ref = line.split("\t", maxsplit=1)
        refs.append({"ref": ref, "sha": sha})
    return refs


def fetch_pr_object(repo: str, pr_number: int) -> dict:
    """Fetch the higher-level PR object the REST API returns (Chapter 02 §5-7).

    Parameters
    ----------
    repo : str
        "owner/name".
    pr_number : int
        The PR to fetch.

    Returns
    -------
    dict
        The raw pull request payload, including `mergeable`, `mergeable_state`,
        `head`, and `base`.
    """
    return run_gh(
        ["api", f"repos/{repo}/pulls/{pr_number}"],
        fixture="pr_raw_pull",
    )


def summarize_pr_identity(pr: dict) -> dict[str, str]:
    """Reduce a raw PR object to the four facts Chapter 02 cares about.

    Parameters
    ----------
    pr : dict
        A raw PR payload from :func:`fetch_pr_object`.

    Returns
    -------
    dict
        {"head_ref": ..., "head_sha": ..., "base_ref": ..., "mergeable_state": ...}
    """
    return {
        "head_ref": pr["head"]["ref"],
        "head_sha": pr["head"]["sha"][:12],
        "base_ref": pr["base"]["ref"],
        "mergeable_state": pr["mergeable_state"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """List PR refs at the Git level, then fetch the same PR's API-level object."""
    parser = argparse.ArgumentParser(description="Chapter 02 demo: refs vs the PR object.")
    parser.add_argument("--pr", type=int, default=101)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section("Layer 1: Raw Git refs (no GitHub API involved)")
    refs = list_pr_refs(repo)
    for ref in refs:
        print(f"  {ref['ref']:<28} {ref['sha'][:12]}")

    section(f"Layer 2: The PR object for #{args.pr} (REST API)")
    pr = fetch_pr_object(repo, args.pr)
    identity = summarize_pr_identity(pr)
    for key, value in identity.items():
        print(f"  {key:<18}: {value}")

    print(
        "\nNote the shape of the difference: Layer 1 is dumb, generic Git plumbing --\n"
        "GitHub just happens to publish two refs per PR. Layer 2 is GitHub's own\n"
        "computed view on top of that plumbing, including mergeable_state, which can\n"
        "be null while GitHub is still computing it (Chapter 02 §8)."
    )


if __name__ == "__main__":
    main()
