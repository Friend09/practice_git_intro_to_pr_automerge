"""
Lab 14: Gate 1 — Repo Readiness
=============================================================
Chapter 14 companion script.

A thin CLI-facing wrapper around `pr_automerge.gates.evaluate_gate1` -- the gate
engine itself is already implemented and live-verified there. This lab's only job
is to fetch the four readiness inputs the way `.github/workflows/gate1-repo-health.yml`
actually does (the light `branches/{branch}` read, never the 403'ing full protection
endpoint -- Chapter 05 §8) and hand them to the engine.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_14_repo_health.py

Live mode, against a real repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_14_repo_health.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 14 — Gate 1: Repo Readiness
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gates import evaluate_gate1  # noqa: E402
from pr_automerge.gh_client import run_gh  # noqa: E402
from pr_automerge.models import GateResult  # noqa: E402
from pr_automerge.render import gate_table, section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def fetch_readiness_inputs(repo: str, branch: str = "main") -> dict:
    """Fetch Gate 1's four readiness inputs, the same way the real workflow does.

    Mirrors `gate1-repo-health.yml` exactly: reads the light `branches/{branch}`
    endpoint for `protected` (never the full protection endpoint, which 403s for
    `GITHUB_TOKEN` -- Chapter 05 §8), and treats `required_checks_registered` as
    mirroring `protection_configured` since which SPECIFIC checks are required
    can't be read without a PAT/App token either.

    Parameters
    ----------
    repo : str
        "owner/name".
    branch : str
        Branch to check -- almost always "main".

    Returns
    -------
    dict
        Keyword-ready for :func:`pr_automerge.gates.evaluate_gate1`.
    """
    branch_data = run_gh(["api", f"repos/{repo}/branches/{branch}"], fixture="branch_light_status")
    main_exists = bool(branch_data.get("name") == branch)
    protection_configured = bool(branch_data.get("protected", False))

    settings = run_gh(["api", f"repos/{repo}"], fixture="repo_settings")
    auto_merge_enabled = bool(settings.get("allow_auto_merge", False))

    return {
        "main_exists": main_exists,
        "protection_configured": protection_configured,
        "required_checks_registered": protection_configured,
        "auto_merge_enabled": auto_merge_enabled,
    }


def run_gate1(repo: str, branch: str = "main") -> GateResult:
    """Fetch inputs and evaluate Gate 1 for a repo.

    Parameters
    ----------
    repo : str
        "owner/name".
    branch : str
        Branch to check.

    Returns
    -------
    GateResult
        Gate 1's verdict.
    """
    inputs = fetch_readiness_inputs(repo, branch)
    return evaluate_gate1(**inputs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Evaluate Gate 1 and print its verdict table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section(f"Gate 1 -- Repo Readiness for {repo}")
    result = run_gate1(repo)
    gate_table([result])
    print(f"\nrationale: {result.rationale}")

    print(
        "\nNote: this lab never calls repos/{repo}/branches/{branch}/protection -- that\n"
        "endpoint 403s for GITHUB_TOKEN regardless of permissions: (Chapter 05 §8). Gate 1\n"
        "only needs to know IF protection exists, which the light endpoint answers fully."
    )


if __name__ == "__main__":
    main()
