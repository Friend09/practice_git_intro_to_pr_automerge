"""
Lab 20: Merge Queues
=============================================================
Chapter 20 companion script.

Simulates the exact failure auto-merge alone can't catch: two PRs that each pass
CI independently against the current `main`, but conflict with EACH OTHER once
both are applied. Compares "naive parallel auto-merge" (this repo's actual design)
against a "merge queue" simulation that serializes and re-tests each PR against the
cumulative result of every PR ahead of it in the queue.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_20_merge_queues.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 20 — Merge Queues
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QueuedPR:
    """A simplified PR for merge-queue simulation purposes.

    Attributes
    ----------
    number : int
        PR number.
    resources_touched : set[str]
        Conceptual "resources" this PR modifies (e.g. a shared config key, a
        migration slot) -- two PRs touching the same resource conflict when
        combined, even if each individually passes CI against the ORIGINAL base.
    passes_ci_alone : bool
        Whether this PR's own CI run (against the original base, before any
        sibling PR merges) passes.
    """

    number: int
    resources_touched: set[str] = field(default_factory=set)
    passes_ci_alone: bool = True


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def simulate_parallel_automerge(prs: list[QueuedPR]) -> dict:
    """Simulate this repo's actual design: independent auto-merge, no re-testing.

    Every PR whose OWN CI passed merges, with no awareness of what any sibling PR
    in the same batch is doing (Chapter 06, Chapter 17 -- this repo's three gates
    never coordinate). Detects, after the fact, whether the merged set actually
    conflicts.

    Parameters
    ----------
    prs : list[QueuedPR]
        The batch of simultaneously-ready PRs.

    Returns
    -------
    dict
        {"merged": [pr.number, ...], "conflict_detected_after_merge": bool,
         "conflicting_resources": set[str]}
    """
    merged = [pr for pr in prs if pr.passes_ci_alone]
    seen: dict[str, int] = {}
    conflicting_resources: set[str] = set()
    for pr in merged:
        for resource in pr.resources_touched:
            if resource in seen:
                conflicting_resources.add(resource)
            seen[resource] = pr.number
    return {
        "merged": [pr.number for pr in merged],
        "conflict_detected_after_merge": bool(conflicting_resources),
        "conflicting_resources": conflicting_resources,
    }


def simulate_merge_queue(prs: list[QueuedPR]) -> list[dict]:
    """Simulate a merge queue: process PRs one at a time, re-testing cumulatively.

    Each PR is tested not just against its own CI result, but against every
    resource already claimed by a PR earlier in the queue -- exactly what a real
    merge queue's speculative re-test against the updated base achieves.

    Parameters
    ----------
    prs : list[QueuedPR]
        The queue, in the order they'd be processed.

    Returns
    -------
    list[dict]
        One entry per PR: {"number": ..., "merged": bool, "reason": str | None}.
    """
    results = []
    claimed: set[str] = set()
    for pr in prs:
        conflict = pr.resources_touched & claimed
        if not pr.passes_ci_alone:
            results.append({"number": pr.number, "merged": False, "reason": "CI failed"})
        elif conflict:
            results.append({"number": pr.number, "merged": False, "reason": f"conflicts with queue: {conflict}"})
        else:
            results.append({"number": pr.number, "merged": True, "reason": None})
            claimed |= pr.resources_touched
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the same conflicting PR batch through both strategies and compare."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prs = [
        QueuedPR(201, resources_touched={"config/feature_flags.yml"}, passes_ci_alone=True),
        QueuedPR(202, resources_touched={"config/feature_flags.yml"}, passes_ci_alone=True),
        QueuedPR(203, resources_touched={"sandbox/app/greeting.py"}, passes_ci_alone=True),
    ]

    section("Naive parallel auto-merge (this repo's actual design)")
    parallel_result = simulate_parallel_automerge(prs)
    print(f"  merged: {parallel_result['merged']}")
    print(f"  conflict detected AFTER merge: {parallel_result['conflict_detected_after_merge']}")
    print(f"  conflicting resources: {parallel_result['conflicting_resources']}")

    section("Merge queue: serialized, cumulatively re-tested")
    queue_result = simulate_merge_queue(prs)
    for row in queue_result:
        status = "MERGED" if row["merged"] else f"HELD ({row['reason']})"
        print(f"  PR #{row['number']}: {status}")

    print(
        "\nBoth PR #201 and #202 individually pass CI against the ORIGINAL main -- naive\n"
        "parallel auto-merge lets both through and only discovers the conflict after the\n"
        "fact. The queue catches it: #202 is held because #201, ahead of it in the queue,\n"
        "already claimed the same resource. This is exactly the gap auto-merge alone\n"
        "cannot close (Chapter 06 §10) -- it answers 'should THIS PR merge,' never\n"
        "'in what order, against what every other ready PR is also doing.'"
    )


if __name__ == "__main__":
    main()
