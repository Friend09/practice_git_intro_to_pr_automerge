"""
Lab 07: The GitHub API In Depth & GitHub Apps
=============================================================
Chapter 07 companion script.

Demonstrates the two API patterns Chapter 07 teaches: paginated reads with
truncation handling (Section 4), and publishing a check run as a worked example of
writing data back to GitHub (Section 7).

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_07_api_and_apps.py

Live mode, against a real PR on the sandbox repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_07_api_and_apps.py --pr 5

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 07 — The GitHub API In Depth & GitHub Apps
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import GhClientError, load_fixture, run_gh  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: GitHub's page size ceiling for list endpoints when requesting the maximum.
MAX_PAGE_SIZE: int = 100

#: GitHub's hard cap on files returned for a single PR's diff (Chapter 07 §4).
FILE_COUNT_TRUNCATION_LIMIT: int = 300


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def fetch_pr_files_paginated(pr_number: int) -> tuple[list[dict], bool]:
    """Fetch every changed file for a PR, page by page, flagging truncation.

    Parameters
    ----------
    pr_number : int
        The PR to fetch files for.

    Returns
    -------
    tuple[list[dict], bool]
        The list of file records, and whether GitHub's file-count ceiling was hit
        (meaning the diff may be larger than what's returned).
    """
    mode = os.environ.get("PRA_MODE", "fixture")

    if mode == "fixture":
        # Fixture mode: fixtures/pr_small_feature.json doesn't carry a files list,
        # so this demonstrates the *shape* of the walk against a small stand-in.
        data = load_fixture("pr_small_feature")
        files = [{"path": f"generated/filler_{i:02d}.py"} for i in range(data["changed_files"])]
        return files, False

    all_files: list[dict] = []
    page = 1
    while True:
        result = run_gh(
            [
                "api",
                f"repos/{os.environ['PRA_REPO']}/pulls/{pr_number}/files",
                "-X", "GET",
                "-f", f"per_page={MAX_PAGE_SIZE}",
                "-f", f"page={page}",
            ]
        )
        # gh api returns a list directly for this endpoint.
        batch = result if isinstance(result, list) else result.get("files", [])
        all_files.extend(batch)
        if len(batch) < MAX_PAGE_SIZE or len(all_files) >= FILE_COUNT_TRUNCATION_LIMIT:
            break
        page += 1

    truncated = len(all_files) >= FILE_COUNT_TRUNCATION_LIMIT
    return all_files, truncated


def publish_check_run(
    repo: str, name: str, head_sha: str, *, passed: bool, title: str, summary: str
) -> None:
    """Publish a check run to GitHub -- the write pattern from Chapter 07 §7.

    Parameters
    ----------
    repo : str
        "owner/name".
    name : str
        The check-run's context name (what shows up in the PR's checks list).
    head_sha : str
        The commit SHA to attach the check run to.
    passed : bool
        Whether the check run's conclusion is "success" or "failure".
    title : str
        Short check-run title.
    summary : str
        Longer, human-readable rationale.
    """
    conclusion = "success" if passed else "failure"
    run_gh(
        [
            "api",
            f"repos/{repo}/check-runs",
            "-f", f"name={name}",
            "-f", f"head_sha={head_sha}",
            "-f", "status=completed",
            "-f", f"conclusion={conclusion}",
            "-f", f"output[title]={title}",
            "-f", f"output[summary]={summary}",
        ]
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Demonstrate paginated reading, and (in live mode) publishing a check run."""
    parser = argparse.ArgumentParser(description="Chapter 07 API demo: read + write.")
    parser.add_argument("--pr", type=int, default=1, help="PR number (used in live mode)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section(f"Paginated read: PR #{args.pr}'s changed files")
    files, truncated = fetch_pr_files_paginated(args.pr)
    print(f"Fetched {len(files)} file(s).")
    if truncated:
        print(f"WARNING: hit the {FILE_COUNT_TRUNCATION_LIMIT}-file ceiling -- diff may be larger.")
    for f in files[:5]:
        print(f"  {f['path']}")
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more")

    mode = os.environ.get("PRA_MODE", "fixture")
    if mode != "live":
        print("\n(Skipping the write demo -- set PRA_MODE=live to publish a real check run.)")
        return

    section("Write demo: publishing a check run")
    try:
        pr_data = run_gh(["pr", "view", str(args.pr), "--json", "headRefOid"])
        sha = pr_data["headRefOid"]
        publish_check_run(
            os.environ["PRA_REPO"],
            "lab-07-api-demo",
            sha,
            passed=True,
            title="Lab 07 demo",
            summary="Published from labs/lab_07_api_and_apps.py",
        )
        print(f"Published a check run onto {sha}.")
    except GhClientError as exc:
        print(f"Could not publish (expected if your token lacks checks:write): {exc}")


if __name__ == "__main__":
    main()
