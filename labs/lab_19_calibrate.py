"""
Lab 19: Calibrating the Threshold
=============================================================
Chapter 19 companion script.

Sweeps Gate 3's threshold against the five worked-example PR fixtures (Chapter 16's
running example) to show how many would auto-merge at each threshold, and loads
`gates.yml` via `pr_automerge.scoring.load_config` to demonstrate that
recalibration is a config-file edit, never a source-code change.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_19_calibrate.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 19 — Calibrating the Threshold
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import load_fixture  # noqa: E402
from pr_automerge.models import PRMetadata  # noqa: E402
from pr_automerge.render import section  # noqa: E402
from pr_automerge.scoring import RiskConfig, compute_risk, load_config  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
GATES_CONFIG_PATH: Path = REPO_ROOT / "gates.yml"

#: The five worked-example PR fixtures from Chapter 16's running example.
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


def load_worked_example() -> list[PRMetadata]:
    """Load the five worked-example fixtures as :class:`PRMetadata` objects.

    Returns
    -------
    list[PRMetadata]
        In the same order as :data:`WORKED_EXAMPLE_FIXTURES`.
    """
    prs = []
    for name in WORKED_EXAMPLE_FIXTURES:
        data = load_fixture(name)
        prs.append(
            PRMetadata(
                number=data["number"],
                title=data["title"],
                base=data["base"],
                head=data["head"],
                additions=data["additions"],
                deletions=data["deletions"],
                changed_files=data["changed_files"],
                critical_path_hits=data["critical_path_hits"],
                draft=data.get("draft", False),
            )
        )
    return prs


def sweep_thresholds(prs: list[PRMetadata], thresholds: list[float], config: RiskConfig) -> dict:
    """Count how many PRs would pass Gate 3 at each candidate threshold.

    Parameters
    ----------
    prs : list[PRMetadata]
        The PR set to evaluate -- usually :func:`load_worked_example`'s output.
    thresholds : list[float]
        Candidate threshold values to sweep, e.g. ``[40, 55, 70, 85, 100]``.
    config : RiskConfig
        Weights and ceiling to use -- only `threshold` varies across the sweep.

    Returns
    -------
    dict
        {threshold: [(pr.title, risk_score, passes), ...]}
    """
    results = {}
    for threshold in thresholds:
        swept_config = RiskConfig(
            weights=config.weights, threshold=threshold, hard_ceiling_lines=config.hard_ceiling_lines
        )
        rows = []
        for pr in prs:
            risk = compute_risk(pr, swept_config)
            within_ceiling = pr.lines_changed <= swept_config.hard_ceiling_lines
            passes = (risk <= threshold) and within_ceiling
            rows.append((pr.title, round(risk, 1), passes))
        results[threshold] = rows
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Load the config, sweep thresholds against the worked example, print results."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section(f"Loaded config from {GATES_CONFIG_PATH.name}")
    config = load_config(GATES_CONFIG_PATH)
    print(f"  weights: {config.weights}")
    print(f"  threshold: {config.threshold}")
    print(f"  hard_ceiling_lines: {config.hard_ceiling_lines}")

    prs = load_worked_example()

    section("Threshold sweep across the five worked-example PRs")
    sweep = sweep_thresholds(prs, [40.0, 55.0, 70.0, 85.0, 100.0], config)
    for threshold, rows in sweep.items():
        passing = sum(1 for _, _, passes in rows if passes)
        print(f"\n  threshold={threshold:>5.0f}  ({passing}/{len(rows)} PRs would auto-merge)")
        for title, risk, passes in rows:
            verdict = "MERGE" if passes else "HOLD"
            print(f"    risk={risk:>6.1f}  {verdict:<5}  {title}")

    print(
        "\nNote: raising the threshold merges more PRs unattended (fewer human reviews, but a\n"
        "higher chance a risky diff slips through); lowering it does the opposite. This sweep --\n"
        "not intuition -- is how you pick a number, and gates.yml is where you commit the choice."
    )


if __name__ == "__main__":
    main()
