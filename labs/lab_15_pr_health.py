"""
Lab 15: Gate 2 — PR Health
=============================================================
Chapter 15 companion script.

A thin CLI-facing wrapper around `pr_automerge.gates.evaluate_gate2` -- the gate
engine itself is already implemented and live-verified there. This lab's only job
is to fetch the CI conclusion for a given SHA the way `.github/workflows/gate2-pr-health.yml`
actually does: reading `github.event.workflow_run.conclusion` in the real workflow,
approximated here by reading the `test` check run for the given SHA.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_15_pr_health.py

Live mode, against a real commit::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_15_pr_health.py --sha <full-sha>

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 15 — Gate 2: PR Health
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gates import evaluate_gate2  # noqa: E402
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


def fetch_ci_conclusion(repo: str, head_sha: str, *, check_name: str = "test") -> str | None:
    """Fetch the named check's conclusion for a SHA, or None if it hasn't reported.

    The real `gate2-pr-health.yml` reads `github.event.workflow_run.conclusion`
    directly, since it's triggered by CI's own `workflow_run` completion (Chapter 09
    §7-8) -- reliable because it's the FIRST hop. This lab approximates the same
    fail-closed contract by reading the Checks API for the SHA instead, so it can
    also be exercised standalone against any commit, not just from inside a
    workflow_run-triggered context.

    Parameters
    ----------
    repo : str
        "owner/name".
    head_sha : str
        The PR's real head SHA -- never the synthetic merge commit (Chapter 10 §12).
    check_name : str
        Which check's conclusion to read. Defaults to "test" (this repo's CI job).

    Returns
    -------
    str or None
        The conclusion string, or None if no matching check run exists yet --
        fail-closed input for :func:`pr_automerge.gates.evaluate_gate2`.
    """
    result = run_gh(
        ["api", f"repos/{repo}/commits/{head_sha}/check-runs"],
        fixture="check_runs_for_sha",
    )
    for run in result.get("check_runs", []):
        if run["name"] == check_name:
            return run.get("conclusion")
    return None


def run_gate2(repo: str, head_sha: str) -> GateResult:
    """Fetch the CI conclusion and evaluate Gate 2 for it.

    Parameters
    ----------
    repo : str
        "owner/name".
    head_sha : str
        The PR's real head SHA.

    Returns
    -------
    GateResult
        Gate 2's verdict.
    """
    conclusion = fetch_ci_conclusion(repo, head_sha)
    return evaluate_gate2(conclusion)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Evaluate Gate 2 for a real check-run response, then for a missing one."""
    parser = argparse.ArgumentParser(description="Chapter 15 demo: Gate 2 PR health.")
    parser.add_argument("--sha", default="a1b2c3d4e5f60718293a4b5c6d7e8f9012345678")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section(f"Gate 2 -- PR Health for {args.sha[:12]}")
    result = run_gate2(repo, args.sha)
    gate_table([result])

    section("Fail-closed check: a check name that never reports")
    missing_result = evaluate_gate2(None)
    gate_table([missing_result])

    print(
        "\nNote: a MISSING CI conclusion is a FAIL, never a skip (Chapter 01's fail-closed\n"
        "rule, Chapter 15 §2) -- this is the deliberate inversion of the prior-art POC's\n"
        "engine.py, where a missing signal is skip and a missing blocker does not block."
    )


if __name__ == "__main__":
    main()
