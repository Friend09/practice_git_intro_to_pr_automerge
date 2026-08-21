"""
Lab 17: Wiring the Airlock
=============================================================
Chapter 17 companion script.

Composes `pr_automerge.gates` and `pr_automerge.scoring` into a single
`decide(pr, ...) -> Decision` entry point -- what this repo's `automerge.yml`
achieves in practice through required status checks plus native auto-merge,
expressed here as one Python call so the composition is visible directly, not
implicit across three separate workflow files.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_17_airlock.py

Live mode, attempting the real enrollment call::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_17_airlock.py --pr 1

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 17 — Wiring the Airlock
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gates import evaluate_gate1, evaluate_gate2  # noqa: E402
from pr_automerge.gh_client import GhClientError, run_gh  # noqa: E402
from pr_automerge.models import Decision, PRMetadata  # noqa: E402
from pr_automerge.render import decision_line, gate_table, section  # noqa: E402
from pr_automerge.scoring import RiskConfig, evaluate_gate3  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def decide(
    pr: PRMetadata,
    *,
    main_exists: bool,
    protection_configured: bool,
    required_checks_registered: bool,
    auto_merge_enabled: bool,
    ci_conclusion: str | None,
    risk_config: RiskConfig | None = None,
) -> Decision:
    """Evaluate all three gates and compose one final airlock verdict.

    Mirrors what this repo's five real workflows achieve collectively through
    required status checks plus native auto-merge (Chapter 17 §3-5) -- Gate 1's
    readiness, Gate 2's CI health, and Gate 3's risk score, composed exactly the
    way `pr_automerge.models.Decision.merge` is defined: `all(g.passed for g in
    gates)`.

    Parameters
    ----------
    pr : PRMetadata
        The PR under evaluation.
    main_exists, protection_configured, required_checks_registered, auto_merge_enabled : bool
        Gate 1's four inputs (Chapter 14 §2).
    ci_conclusion : str or None
        Gate 2's input (Chapter 15 §2) -- `None` fails closed.
    risk_config : RiskConfig, optional
        Gate 3's weights/threshold/ceiling. Defaults to `RiskConfig()`.

    Returns
    -------
    Decision
        The composed, final verdict across all three gates.
    """
    gate1 = evaluate_gate1(
        main_exists=main_exists,
        protection_configured=protection_configured,
        required_checks_registered=required_checks_registered,
        auto_merge_enabled=auto_merge_enabled,
    )
    gate2 = evaluate_gate2(ci_conclusion)
    gate3 = evaluate_gate3(pr, risk_config or RiskConfig())

    gates = [gate1, gate2, gate3]
    merge = all(g.passed for g in gates)
    return Decision(pr_number=pr.number, merge=merge, gates=gates)


def enqueue_for_automerge(repo: str, pr_number: int, decision: Decision) -> dict:
    """Enroll a PASSING decision in native auto-merge (Chapter 06, Chapter 17 §6-7).

    Mirrors `automerge.yml`'s own logic: try `gh pr merge --auto` with the default
    token first; the real workflow additionally falls back to `PRA_BOT_TOKEN` if
    that fails (Chapter 07/11) -- omitted here since this lab has no such secret to
    fall back to, so a `GITHUB_TOKEN`-style failure is reported honestly rather than
    silently retried.

    Parameters
    ----------
    repo : str
        "owner/name".
    pr_number : int
        The PR to enroll.
    decision : Decision
        This PR's composed verdict -- refuses to even attempt enrollment if
        `decision.merge` is False.

    Returns
    -------
    dict
        {"attempted": bool, "enrolled": bool, "detail": str}
    """
    if not decision.merge:
        blocked_by = ", ".join(g.gate for g in decision.failed_gates())
        return {"attempted": False, "enrolled": False, "detail": f"blocked by: {blocked_by}"}

    try:
        run_gh(["pr", "merge", str(pr_number), "--repo", repo, "--auto", "--squash"], fixture="pr_small_feature")
        return {"attempted": True, "enrolled": True, "detail": "queued via GITHUB_TOKEN"}
    except GhClientError as exc:
        return {"attempted": True, "enrolled": False, "detail": str(exc)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Compose all three gates for a sample PR and attempt enrollment."""
    parser = argparse.ArgumentParser(description="Chapter 17 demo: the composed airlock.")
    parser.add_argument("--pr", type=int, default=102)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    pr = PRMetadata(
        number=args.pr,
        title="feat: add greeting helper to sandbox app",
        base="main",
        head="feat/greeting-helper",
        additions=100,
        deletions=20,
        changed_files=6,
        critical_path_hits=0,
    )

    section(f"Deciding PR #{pr.number}: all three gates ready, healthy, and safe")
    decision = decide(
        pr,
        main_exists=True,
        protection_configured=True,
        required_checks_registered=True,
        auto_merge_enabled=True,
        ci_conclusion="success",
    )
    gate_table(decision.gates)
    decision_line(decision)

    section("Attempting enrollment")
    result = enqueue_for_automerge(repo, pr.number, decision)
    print(f"attempted={result['attempted']} enrolled={result['enrolled']}")
    print(f"  {result['detail']}")

    section(f"Deciding PR #{pr.number}: same PR, but CI is red (Gate 2 fails)")
    decision2 = decide(
        pr,
        main_exists=True,
        protection_configured=True,
        required_checks_registered=True,
        auto_merge_enabled=True,
        ci_conclusion="failure",
    )
    gate_table(decision2.gates)
    decision_line(decision2)
    result2 = enqueue_for_automerge(repo, pr.number, decision2)
    print(f"\nattempted={result2['attempted']} enrolled={result2['enrolled']}")
    print(f"  {result2['detail']}")


if __name__ == "__main__":
    main()
