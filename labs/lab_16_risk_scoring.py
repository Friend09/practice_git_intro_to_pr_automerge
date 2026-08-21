"""
Lab 16: Gate 3 — Risk Scoring
=============================================================
Chapter 16 companion script.

Runs the Chapter 16 worked example (five PRs of increasing size) through the real
pr_automerge.scoring engine in PRA_MODE=fixture (offline, using fixtures/*.json),
or against a real PR in PRA_MODE=live.

Usage
-----
Fixture mode (default, offline, matches the chapter's worked example table)::

    python labs/lab_16_risk_scoring.py

Live mode, against a real PR on the sandbox repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_16_risk_scoring.py --pr 5

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_THRESHOLD  : override the default risk threshold (default: 70.0)
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 16 — Gate 3: Risk Scoring
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Labs run standalone; the repo root (where pr_automerge lives) must be on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import load_fixture  # noqa: E402
from pr_automerge.models import PRMetadata  # noqa: E402
from pr_automerge.render import section  # noqa: E402
from pr_automerge.scoring import RiskConfig, DEFAULT_THRESHOLD, evaluate_gate3  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))
THRESHOLD: float = float(os.getenv("PRA_THRESHOLD", str(DEFAULT_THRESHOLD)))

#: The five worked-example fixtures from Chapter 16 Section 8, in table order.
WORKED_EXAMPLE_FIXTURES: list[str] = [
    "pr_typo_fix",
    "pr_small_feature",
    "pr_workflow_touch",
    "pr_refactor",
    "pr_large_migration",
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def pr_from_fixture(name: str) -> PRMetadata:
    """Load one of the fixtures/*.json PR payloads as a typed PRMetadata.

    Parameters
    ----------
    name : str
        Fixture filename stem, e.g. "pr_typo_fix".

    Returns
    -------
    PRMetadata
        The typed PR record for the scoring engine.
    """
    data = load_fixture(name)
    return PRMetadata(**data)


def run_worked_example(config: RiskConfig) -> None:
    """Score all five Chapter 16 worked-example PRs and print the verdict table.

    Parameters
    ----------
    config : RiskConfig
        Weights/threshold/ceiling to score against.
    """
    header = f"{'PR':<24}{'Lines':>7}{'Files':>7}{'Crit':>6}{'Risk':>8}  Verdict"
    print(header)
    print("-" * len(header))
    for fixture_name in WORKED_EXAMPLE_FIXTURES:
        pr = pr_from_fixture(fixture_name)
        result = evaluate_gate3(pr, config)
        verdict = "MERGE" if result.passed else "HOLD"
        print(
            f"{pr.title[:23]:<24}{pr.lines_changed:>7}{pr.changed_files:>7}"
            f"{pr.critical_path_hits:>6}{result.details['risk']:>8.1f}  {verdict}"
        )
        print(f"  {result.rationale}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI args and run either the worked example or a single live PR."""
    parser = argparse.ArgumentParser(description="Score PRs with the Gate 3 risk engine.")
    parser.add_argument("--pr", type=int, default=None, help="PR number (PRA_MODE=live only)")
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = RiskConfig(threshold=args.threshold)

    mode = os.environ.get("PRA_MODE", "fixture")

    if mode == "fixture":
        section("Chapter 16 worked example (fixture mode)")
        run_worked_example(config)
        return

    if args.pr is None:
        raise SystemExit("PRA_MODE=live requires --pr <number>")

    from pr_automerge.gh_client import run_gh  # local import: only needed in live mode

    section(f"Scoring live PR #{args.pr}")
    data = run_gh(
        ["pr", "view", str(args.pr), "--json", "additions,deletions,changedFiles,title,baseRefName,headRefName"]
    )
    pr = PRMetadata(
        number=args.pr,
        title=data["title"],
        base=data["baseRefName"],
        head=data["headRefName"],
        additions=data["additions"],
        deletions=data["deletions"],
        changed_files=data["changedFiles"],
    )
    result = evaluate_gate3(pr, config)
    print(json.dumps({"pr": pr.number, "risk": result.details["risk"], "status": result.status.value}, indent=2))
    print(result.rationale)


if __name__ == "__main__":
    main()
