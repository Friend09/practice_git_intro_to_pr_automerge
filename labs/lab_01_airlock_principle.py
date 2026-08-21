"""
Lab 01: Auto-Merge & The Airlock Principle
=============================================================
Chapter 01 companion script.

This module demonstrates the shared Gate/GateResult/Decision model every gate in
this curriculum uses, by running three deliberately simple stub gates and printing
the airlock table from Chapter 01 Section 11.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_01_airlock_principle.py

Or import individual components::

    from labs.lab_01_airlock_principle import run_stub_airlock

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)
PRA_LOG_LEVEL  : Logging level (default: INFO)

References
----------
Chapter 01 — Auto-Merge & The Airlock Principle
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Labs run standalone (`python labs/lab_XX_*.py`), so the repo root -- where the
# pr_automerge package lives -- must be added to sys.path explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.models import Decision, GateResult, GateStatus  # noqa: E402
from pr_automerge.render import decision_line, gate_table, section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))
LOG_LEVEL: str = os.getenv("PRA_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def run_stub_airlock(pr_number: int, *, ready: bool, healthy: bool, safe_size: bool) -> Decision:
    """Run three stub gates (not connected to real GitHub) and compose a Decision.

    This mirrors the shape every real gate in this curriculum follows, without any
    of the GitHub API calls -- useful for understanding the composition pattern in
    isolation before Chapter 14 wires up the real thing.

    Parameters
    ----------
    pr_number : int
        A stand-in PR number for the printed table.
    ready : bool
        Stub verdict for Gate 1 (repo readiness).
    healthy : bool
        Stub verdict for Gate 2 (PR health).
    safe_size : bool
        Stub verdict for Gate 3 (risk scoring).

    Returns
    -------
    Decision
        The composed verdict: merges only if all three stub gates pass.
    """
    gate1 = GateResult(
        gate="gate1_repo_readiness",
        status=GateStatus.PASS if ready else GateStatus.FAIL,
        rationale="stub: repo is ready" if ready else "stub: repo is NOT ready",
    )
    gate2 = GateResult(
        gate="gate2_pr_health",
        status=GateStatus.PASS if healthy else GateStatus.FAIL,
        rationale="stub: CI is green" if healthy else "stub: CI is red or unknown",
    )
    gate3 = GateResult(
        gate="gate3_risk_scoring",
        status=GateStatus.PASS if safe_size else GateStatus.FAIL,
        rationale="stub: diff is small/safe" if safe_size else "stub: diff is too risky",
    )
    gates = [gate1, gate2, gate3]
    merge = all(g.passed for g in gates)
    return Decision(pr_number=pr_number, merge=merge, gates=gates)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run three example airlock scenarios and print each one's decision table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("Scenario 1: everything passes")
    decision = run_stub_airlock(1, ready=True, healthy=True, safe_size=True)
    gate_table(decision.gates)
    decision_line(decision)

    section("Scenario 2: Gate 2 fails (CI red)")
    decision = run_stub_airlock(2, ready=True, healthy=False, safe_size=True)
    gate_table(decision.gates)
    decision_line(decision)

    section("Scenario 3: Gate 1 fails (repo not ready) -- everything downstream is moot")
    decision = run_stub_airlock(3, ready=False, healthy=True, safe_size=True)
    gate_table(decision.gates)
    decision_line(decision)

    print("\nSummary: an airlock only opens when every gate independently passes.")
    print("A single failed gate holds the PR, regardless of the other two.")


if __name__ == "__main__":
    main()
