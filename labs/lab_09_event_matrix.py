"""
Lab 09: The Event Model
=============================================================
Chapter 09 companion script.

Encodes the event comparison matrix from `resources/gha_event_reference.md` as
structured data, and simulates the `workflow_run` chaining trap this repo's own
`automerge.yml` build hit for real -- `head_sha` stays correct on the first hop of a
`workflow_run` chain, then collapses to the default branch's SHA on the second hop.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_09_event_matrix.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 09 — The Event Model
resources/gha_event_reference.md
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: The event comparison matrix, matching resources/gha_event_reference.md exactly --
#: kept as structured data here so a lab/notebook can query it instead of only
#: reading it in prose.
EVENT_MATRIX: list[dict] = [
    {
        "event": "pull_request",
        "checked_out_ref": "the PR's synthetic merge commit (Chapter 02)",
        "secrets_available": "no (fork PRs)",
        "fork_prs_reach_it": True,
        "fires_from_automation_authored_events": False,
    },
    {
        "event": "pull_request_target",
        "checked_out_ref": "the BASE branch's code, not the PR's",
        "secrets_available": "yes, always",
        "fork_prs_reach_it": True,
        "fires_from_automation_authored_events": False,
    },
    {
        "event": "schedule",
        "checked_out_ref": "default branch only",
        "secrets_available": "yes",
        "fork_prs_reach_it": False,
        "fires_from_automation_authored_events": False,
    },
    {
        "event": "workflow_dispatch",
        "checked_out_ref": "whatever ref specified at dispatch time",
        "secrets_available": "yes",
        "fork_prs_reach_it": False,
        "fires_from_automation_authored_events": False,
    },
    {
        "event": "workflow_run",
        "checked_out_ref": "the default branch's copy of the LISTENING workflow's own file",
        "secrets_available": "yes",
        "fork_prs_reach_it": "indirectly",
        "fires_from_automation_authored_events": True,
    },
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def describe_event(name: str) -> dict:
    """Look up one event's row in the comparison matrix.

    Parameters
    ----------
    name : str
        Event name, e.g. ``"pull_request_target"``.

    Returns
    -------
    dict
        The matching matrix row.

    Raises
    ------
    KeyError
        If the event isn't in :data:`EVENT_MATRIX`.
    """
    for row in EVENT_MATRIX:
        if row["event"] == name:
            return row
    raise KeyError(f"no matrix entry for event {name!r}")


def print_event_matrix() -> None:
    """Print the full event comparison matrix as a fixed-width table."""
    header = f"{'EVENT':<22}{'SECRETS':<14}{'FORK PRs':<12}{'FROM AUTOMATION'}"
    print(header)
    print("-" * len(header))
    for row in EVENT_MATRIX:
        print(
            f"{row['event']:<22}"
            f"{str(row['secrets_available']):<14}"
            f"{str(row['fork_prs_reach_it']):<12}"
            f"{row['fires_from_automation_authored_events']}"
        )


def simulate_workflow_run_chain(hops: int) -> list[str]:
    """Simulate `head_sha` fidelity across a chain of `workflow_run` triggers.

    Verified live building this repo's `automerge.yml` (Chapter 17): `head_sha` is
    reliable on the FIRST hop of a `workflow_run` chain (the listening workflow reads
    the SHA of the workflow that directly triggered it, e.g. a `pull_request`-
    triggered workflow). On a SECOND hop -- a `workflow_run` listening to another
    `workflow_run`-triggered workflow -- that SHA collapses to the default branch's
    SHA, because the second listener's own trigger context no longer traces back to
    the original PR.

    Parameters
    ----------
    hops : int
        Number of `workflow_run` hops to simulate (1 = a single workflow_run
        listening directly to a pull_request-triggered workflow).

    Returns
    -------
    list[str]
        One entry per hop: either the (correct) PR head SHA or the string
        ``"COLLAPSED_TO_DEFAULT_BRANCH_SHA"``.
    """
    pr_head_sha = "a1b2c3d4e5f6"
    results = []
    for hop in range(1, hops + 1):
        results.append(pr_head_sha if hop == 1 else "COLLAPSED_TO_DEFAULT_BRANCH_SHA")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Print the event matrix, then simulate the workflow_run chaining trap."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("Event comparison matrix")
    print_event_matrix()

    section("The workflow_run chaining trap, simulated")
    for hop, sha in enumerate(simulate_workflow_run_chain(3), start=1):
        print(f"  hop {hop}: head_sha = {sha}")

    print(
        "\nThis is exactly what this repo's own automerge.yml build hit: Gate 3 (directly\n"
        "pull_request-triggered) always sees the real SHA. Gate 2 (workflow_run off CI) sees\n"
        "it correctly at hop 1. Anything listening a SECOND hop deep collapses to the wrong\n"
        "commit -- the architectural fix was to stop chaining past one hop (Chapter 17)."
    )


if __name__ == "__main__":
    main()
