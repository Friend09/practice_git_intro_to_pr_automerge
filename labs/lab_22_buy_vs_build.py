"""
Lab 22: Buy vs Build
=============================================================
Chapter 22 companion script.

Encodes the feature comparison between this repo's custom-built three-gate airlock
and typical third-party PR-automation tools (Mergify, Kodiak, Renovate) as
structured data, and implements a weighted decision heuristic -- mirroring this
curriculum's own recurring pattern of a typed decision object with a rationale,
applied here to the buy-vs-build question itself rather than a merge verdict.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_22_buy_vs_build.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 22 — Buy vs Build
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: Feature comparison between this repo's custom build and typical third-party
#: PR-automation tools (Mergify, Kodiak-style config-driven merge bots).
FEATURE_COMPARISON: list[dict] = [
    {
        "dimension": "Setup effort",
        "custom_build": "High — this entire 23-chapter curriculum's worth of work",
        "third_party": "Minimal — install the GitHub App, write a YAML policy file",
    },
    {
        "dimension": "Hosting",
        "custom_build": "Self-hosted (your own GitHub Actions minutes)",
        "third_party": "Vendor-hosted (their infrastructure evaluates your PRs)",
    },
    {
        "dimension": "Custom risk-scoring logic",
        "custom_build": "Fully custom — any formula, any weight, any language",
        "third_party": "Limited to the vendor's configuration DSL",
    },
    {
        "dimension": "Multi-repo rollout",
        "custom_build": "Copy/adapt workflow files per repo, or build reusable workflows (Chapter 21)",
        "third_party": "Native — one GitHub App install covers every repo in an org",
    },
    {
        "dimension": "Vendor lock-in / dependency risk",
        "custom_build": "None — you own every line",
        "third_party": "Real — pricing changes, feature deprecation, or the vendor shutting down",
    },
    {
        "dimension": "Cost",
        "custom_build": "Actions minutes only (often free-tier for public repos)",
        "third_party": "Often free for open source, paid tiers for private/org use",
    },
    {
        "dimension": "Debuggability when something goes wrong",
        "custom_build": "Full visibility — your own code, your own logs",
        "third_party": "Limited to whatever the vendor's own UI/logs expose",
    },
]


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BuyBuildFactors:
    """Inputs to the buy-vs-build heuristic.

    Attributes
    ----------
    needs_custom_risk_model : bool
        Does the team need scoring logic a config-driven DSL can't express (this
        repo's own Gate 3, Chapter 16, is exactly this case)?
    rolling_out_to_many_repos : bool
        Is this being deployed across more than a handful of repositories?
    has_in_house_actions_expertise : bool
        Does the team already have the skills this curriculum teaches?
    budget_for_a_paid_tool : bool
        Is a paid third-party tier acceptable, if the free tier doesn't fit?
    """

    needs_custom_risk_model: bool
    rolling_out_to_many_repos: bool
    has_in_house_actions_expertise: bool
    budget_for_a_paid_tool: bool


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def recommend(factors: BuyBuildFactors) -> dict:
    """Produce a weighted buy-vs-build recommendation with a rationale.

    Mirrors this curriculum's `GateResult`/`Decision` pattern (Chapter 01 §11) --
    a typed verdict with an explicit rationale, never a bare recommendation with
    no explanation.

    Parameters
    ----------
    factors : BuyBuildFactors
        The team's own situation.

    Returns
    -------
    dict
        {"recommendation": "build" | "buy", "build_score": int, "buy_score": int,
         "reasons": list[str]}
    """
    build_score = 0
    buy_score = 0
    reasons: list[str] = []

    if factors.needs_custom_risk_model:
        build_score += 2
        reasons.append("Custom risk model needed -> build (third-party DSLs rarely express this)")
    else:
        buy_score += 1
        reasons.append("No custom risk model needed -> mild point toward buy")

    if factors.rolling_out_to_many_repos:
        buy_score += 2
        reasons.append("Rolling out to many repos -> buy (native multi-repo install)")
    else:
        build_score += 1
        reasons.append("Single or few repos -> mild point toward build")

    if factors.has_in_house_actions_expertise:
        build_score += 1
        reasons.append("In-house Actions expertise already exists -> mild point toward build")
    else:
        buy_score += 1
        reasons.append("No in-house Actions expertise yet -> mild point toward buy")

    if not factors.budget_for_a_paid_tool:
        build_score += 1
        reasons.append("No budget for a paid tier -> mild point toward build (Actions minutes are often free)")

    recommendation = "build" if build_score >= buy_score else "buy"
    return {
        "recommendation": recommendation,
        "build_score": build_score,
        "buy_score": buy_score,
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Print the feature comparison, then run the heuristic on two example teams."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("Feature comparison: custom build vs typical third-party tools")
    for row in FEATURE_COMPARISON:
        print(f"  {row['dimension']}:")
        print(f"    custom_build: {row['custom_build']}")
        print(f"    third_party:  {row['third_party']}")

    section("Recommendation: a team like this repo's own curriculum sandbox")
    like_this_repo = BuyBuildFactors(
        needs_custom_risk_model=True,
        rolling_out_to_many_repos=False,
        has_in_house_actions_expertise=True,
        budget_for_a_paid_tool=False,
    )
    result = recommend(like_this_repo)
    print(f"  recommendation: {result['recommendation'].upper()} (build={result['build_score']}, buy={result['buy_score']})")
    for reason in result["reasons"]:
        print(f"    - {reason}")

    section("Recommendation: a team rolling a simple policy out org-wide")
    org_wide_simple_policy = BuyBuildFactors(
        needs_custom_risk_model=False,
        rolling_out_to_many_repos=True,
        has_in_house_actions_expertise=False,
        budget_for_a_paid_tool=True,
    )
    result2 = recommend(org_wide_simple_policy)
    print(f"  recommendation: {result2['recommendation'].upper()} (build={result2['build_score']}, buy={result2['buy_score']})")
    for reason in result2["reasons"]:
        print(f"    - {reason}")


if __name__ == "__main__":
    main()
