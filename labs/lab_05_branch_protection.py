"""
Lab 05: Branch Protection & Rulesets
=============================================================
Chapter 05 companion script.

Demonstrates the two ways to check branch protection status -- the lightweight
`protected: true/false` boolean `GITHUB_TOKEN` *can* read, and the full protection
object (required checks, review requirements, enforce_admins) that requires
Administration permission `GITHUB_TOKEN` never has. This is a real discovery from
this repo's own build (see `notes/IMPROVEMENTS_SUMMARY.md`, Live-Repo Verification
Log #1), not a hypothetical.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_05_branch_protection.py

Live mode, against a real repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_05_branch_protection.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 05 — Branch Protection & Rulesets
"""

from __future__ import annotations

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


def check_protected_light(repo: str, branch: str = "main") -> bool:
    """Read whether a branch is protected, using the endpoint `GITHUB_TOKEN` can call.

    `GET /repos/{o}/{r}/branches/{branch}` returns a `protected` boolean without
    requiring Administration permission -- this is Gate 1's actual data source
    (Chapter 14), chosen specifically because `GITHUB_TOKEN` can read it.

    Parameters
    ----------
    repo : str
        "owner/name".
    branch : str
        Branch name to check.

    Returns
    -------
    bool
        Whether the branch has protection enabled at all (no detail on *what*
        is enforced).
    """
    result = run_gh(
        ["api", f"repos/{repo}/branches/{branch}"],
        fixture="branch_light_status",
    )
    return bool(result["protected"])


def fetch_protection_detail(repo: str, branch: str = "main") -> dict:
    """Read the FULL protection object -- requires Administration permission.

    `GET /repos/{o}/{r}/branches/{branch}/protection` returns 403 for
    `GITHUB_TOKEN`, even with `permissions: contents: write` declared -- verified
    against this repo's own sandbox while building `gate1-repo-health.yml`. This
    function exists to demonstrate what a PAT/App token *would* see; Gate 1 itself
    never calls this endpoint (see :func:`check_protected_light`).

    Parameters
    ----------
    repo : str
        "owner/name".
    branch : str
        Branch name to check.

    Returns
    -------
    dict
        Full protection detail: required status check contexts, enforce_admins,
        review requirements.

    Raises
    ------
    GhClientError
        In live mode, if the calling token lacks Administration permission
        (this is the expected outcome for `GITHUB_TOKEN`).
    """
    return run_gh(
        ["api", f"repos/{repo}/branches/{branch}/protection"],
        fixture="branch_protection_full",
    )


def required_check_names(detail: dict) -> list[str]:
    """Extract the list of required status check context names from full detail.

    Parameters
    ----------
    detail : dict
        Output of :func:`fetch_protection_detail`.

    Returns
    -------
    list[str]
        Required check names, e.g. ``["test", "gate2-pr-health", "gate3-risk-score"]``.
    """
    return list(detail.get("required_status_checks", {}).get("contexts", []))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Demonstrate both the light and full protection reads, side by side."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section("Light read: GET /branches/{branch} (GITHUB_TOKEN can call this)")
    protected = check_protected_light(repo)
    print(f"protected = {protected}")

    section("Full read: GET /branches/{branch}/protection (needs Administration permission)")
    try:
        detail = fetch_protection_detail(repo)
        checks = required_check_names(detail)
        print(f"required status checks: {checks}")
        print(f"enforce_admins: {detail.get('enforce_admins', {}).get('enabled')}")
    except GhClientError as exc:
        print(f"Failed as predicted for GITHUB_TOKEN in live mode: {exc}")

    print(
        "\nGate 1 (Chapter 14) only ever calls the light endpoint above -- it needs to know\n"
        "IF the branch is protected, not the full detail, and GITHUB_TOKEN can answer that\n"
        "question without ever needing Administration permission."
    )


if __name__ == "__main__":
    main()
