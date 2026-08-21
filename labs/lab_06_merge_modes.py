"""
Lab 06: Native Auto-Merge vs Your Own Merge Call
=============================================================
Chapter 06 companion script.

Builds both merge paths from Chapter 06 Section 8 / Appendix A.1 side by side --
enabling native auto-merge (an enrollment, not a merge) and attempting a direct
merge call (an immediate, synchronous attempt) -- so their different responses are
visible in real output, not just in prose.

Usage
-----
Fixture mode (default, offline -- prints what each call WOULD do)::

    python labs/lab_06_merge_modes.py

Live mode, against a real PR on the sandbox repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_06_merge_modes.py --pr 5

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 06 — Native Auto-Merge vs Your Own Merge Call
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import GhClientError, run_gh  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def enable_native_auto_merge(repo: str, pr_number: int, *, squash: bool = True) -> dict:
    """Enroll a PR in native auto-merge (Chapter 06 Section 3).

    Parameters
    ----------
    repo : str
        "owner/name".
    pr_number : int
        The PR to enroll.
    squash : bool
        Whether to use the squash merge strategy once GitHub performs the merge.

    Returns
    -------
    dict
        A summary of the attempt: {"enrolled": bool, "detail": str}.

    Notes
    -----
    This calls the GraphQL-backed `enablePullRequestAutoMerge` mutation via
    `gh pr merge --auto`. As Chapter 06 Section 9 documents, GITHUB_TOKEN cannot
    call this mutation -- verified live against this repo's own sandbox -- so this
    will fail with a GraphQL permission error unless run with a PAT/App token.
    """
    args = ["pr", "merge", str(pr_number), "--repo", repo, "--auto"]
    args.append("--squash" if squash else "--merge")
    try:
        run_gh(args, fixture="pr_small_feature")  # fixture stands in for a real response
        return {"enrolled": True, "detail": "Auto-merge enrollment succeeded (queued, not merged yet)."}
    except GhClientError as exc:
        return {"enrolled": False, "detail": str(exc)}


def attempt_direct_merge(repo: str, pr_number: int) -> dict:
    """Attempt an immediate, synchronous merge (Chapter 06 Section 4).

    Parameters
    ----------
    repo : str
        "owner/name".
    pr_number : int
        The PR to attempt to merge right now.

    Returns
    -------
    dict
        A summary of the attempt: {"merged": bool, "detail": str}.
    """
    try:
        run_gh(
            ["api", "-X", "PUT", f"repos/{repo}/pulls/{pr_number}/merge"],
            fixture="pr_small_feature",
        )
        return {"merged": True, "detail": "Merged immediately (was mergeable at call time)."}
    except GhClientError as exc:
        return {"merged": False, "detail": str(exc)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run both merge paths against the same PR and print both responses."""
    parser = argparse.ArgumentParser(description="Chapter 06 demo: enroll vs execute.")
    parser.add_argument("--pr", type=int, default=1)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section(f"Path A: enable native auto-merge on PR #{args.pr}")
    result_a = enable_native_auto_merge(repo, args.pr)
    print(f"enrolled={result_a['enrolled']}")
    print(f"  {result_a['detail']}")

    section(f"Path B: attempt a direct merge call on PR #{args.pr}")
    result_b = attempt_direct_merge(repo, args.pr)
    print(f"merged={result_b['merged']}")
    print(f"  {result_b['detail']}")

    print(
        "\nNote the shape of the difference: Path A tells you whether the ENROLLMENT\n"
        "succeeded, not whether the PR is merged. Path B tells you whether the MERGE\n"
        "itself succeeded, right now. Never conflate the two return values."
    )


if __name__ == "__main__":
    main()
