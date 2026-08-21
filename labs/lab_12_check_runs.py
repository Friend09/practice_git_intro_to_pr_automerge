"""
Lab 12: Status Checks, Check Runs & Commit Statuses
=============================================================
Chapter 12 companion script.

Demonstrates publishing a check run (the API this repo's Gate 2/Gate 3 workflows
actually use), the status/conclusion vocabulary, and how the result connects back
to the required-check name-matching from Chapter 05.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_12_check_runs.py

Live mode, against a real PR/commit::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_12_check_runs.py --sha <full-sha>

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 12 — Status Checks, Check Runs & Commit Statuses
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import run_gh  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: The `status` field's full vocabulary (Chapter 12 §4).
CHECK_RUN_STATUSES: list[str] = ["queued", "in_progress", "completed"]

#: The `conclusion` field's full vocabulary -- only meaningful once status="completed".
CHECK_RUN_CONCLUSIONS: list[str] = [
    "success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required",
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def publish_check_run(
    repo: str,
    head_sha: str,
    name: str,
    *,
    conclusion: str,
    title: str,
    summary: str,
) -> dict:
    """Publish a completed check run (Chapter 12 §5 -- what Gate 2/Gate 3 actually call).

    Parameters
    ----------
    repo : str
        "owner/name".
    head_sha : str
        The commit this check run applies to -- always the PR's real head SHA
        (Chapter 10 §2), never the synthetic merge commit.
    name : str
        The check's name -- this is the exact string branch protection matches
        against as a required check (Chapter 05 §2).
    conclusion : str
        One of :data:`CHECK_RUN_CONCLUSIONS`.
    title : str
        Short, human-readable summary line.
    summary : str
        Longer Markdown body, shown in the PR's checks tab.

    Returns
    -------
    dict
        The created check run object.
    """
    return run_gh(
        [
            "api",
            f"repos/{repo}/check-runs",
            "-f",
            f"name={name}",
            "-f",
            f"head_sha={head_sha}",
            "-f",
            "status=completed",
            "-f",
            f"conclusion={conclusion}",
        ],
        fixture="check_run_response",
    )


def commit_status_vs_check_run() -> list[dict]:
    """Return the trade-off comparison between the two publishing APIs (Chapter 12 §3).

    Returns
    -------
    list[dict]
        Rows comparing the Commit Status API and the Checks API.
    """
    return [
        {
            "property": "Output detail",
            "commit_status": "One state + one short description string",
            "check_run": "Title, Markdown summary, annotations on specific lines",
        },
        {
            "property": "Required-check matching",
            "commit_status": "By context string",
            "check_run": "By check name string -- same matching mechanism, different field",
        },
        {
            "property": "Re-runnable from the UI",
            "commit_status": "No",
            "check_run": "Yes, if published by a GitHub App",
        },
        {
            "property": "This repo's usage",
            "commit_status": "Not used",
            "check_run": "Used by every gate workflow",
        },
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Publish a sample check run and print the two-API comparison."""
    parser = argparse.ArgumentParser(description="Chapter 12 demo: publishing a check run.")
    parser.add_argument("--sha", default="a1b2c3d4e5f60718293a4b5c6d7e8f9012345678")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section("Status and conclusion vocabulary")
    print(f"  status values:     {CHECK_RUN_STATUSES}")
    print(f"  conclusion values: {CHECK_RUN_CONCLUSIONS}")

    section(f"Publishing a check run for {args.sha[:12]}")
    result = publish_check_run(
        repo,
        args.sha,
        "gate3-risk-score",
        conclusion="success",
        title="risk=66.0 <= threshold=70",
        summary="Gate 3 passed.",
    )
    print(f"  id: {result['id']}")
    print(f"  name: {result['name']}")
    print(f"  status/conclusion: {result['status']}/{result['conclusion']}")

    section("Commit Status API vs Checks API")
    for row in commit_status_vs_check_run():
        print(f"  {row['property']:<28} status={row['commit_status']:<40} check_run={row['check_run']}")

    print(
        "\nNote: the check name above ('gate3-risk-score') is the exact string branch\n"
        "protection matches against as a required check (Chapter 05 §2) -- rename the job\n"
        "and the required check silently stops being satisfied."
    )


if __name__ == "__main__":
    main()
