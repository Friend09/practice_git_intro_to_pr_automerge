"""Typed data models shared across the three gates.

Every gate returns a :class:`GateResult`, never a bare bool or string — the curriculum's
teaching point at every stage is *why* a gate decided what it decided, and a plain
boolean throws that reasoning away.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GateStatus(str, Enum):
    """The three-valued outcome of a single gate.

    ``SKIP`` exists so a gate can honestly report "I had no data to evaluate" — but
    unlike the prior-art POC (``pr-auto-approve-poc``), this repo treats a ``SKIP`` on
    a required gate as equivalent to ``FAIL`` when computing the final merge decision.
    See Chapter 14 for the fail-closed vs fail-open discussion.
    """

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class PRMetadata:
    """Normalized facts about a single pull request — the input to Gate 3.

    Attributes
    ----------
    number : int
        The PR number.
    title : str
        The PR title.
    base : str
        The branch this PR merges into (almost always ``"main"``).
    head : str
        The branch this PR merges from.
    additions : int
        Lines added, from the PR's ``additions`` field.
    deletions : int
        Lines deleted, from the PR's ``deletions`` field.
    changed_files : int
        Number of files touched.
    critical_path_hits : int
        Count of changed files matching a configured "critical path" glob
        (e.g. ``.github/workflows/**``, ``pr_automerge/scoring.py``).
    draft : bool
        Whether the PR is still a draft.
    """

    number: int
    title: str
    base: str
    head: str
    additions: int
    deletions: int
    changed_files: int
    critical_path_hits: int = 0
    draft: bool = False

    @property
    def lines_changed(self) -> int:
        """Total lines touched (additions + deletions)."""
        return self.additions + self.deletions


@dataclass(frozen=True)
class GateResult:
    """The outcome of evaluating one gate.

    Attributes
    ----------
    gate : str
        Which gate produced this result, e.g. ``"gate1_repo_readiness"``.
    status : GateStatus
        pass / fail / skip.
    rationale : str
        A one-sentence, human-readable explanation — this is what gets printed in
        the job summary and the PR comment.
    details : dict
        Optional structured data backing the rationale (e.g. the raw score).
    """

    gate: str
    status: GateStatus
    rationale: str
    details: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """True only for an explicit PASS — SKIP is not treated as a pass."""
        return self.status is GateStatus.PASS


@dataclass(frozen=True)
class Decision:
    """The final airlock verdict, composed from all three gate results.

    Attributes
    ----------
    pr_number : int
        The PR under evaluation.
    merge : bool
        Whether the airlock opens.
    gates : list[GateResult]
        Every gate's individual result, in evaluation order.
    """

    pr_number: int
    merge: bool
    gates: list[GateResult]

    def failed_gates(self) -> list[GateResult]:
        """Return every gate that did not pass (fail or skip)."""
        return [g for g in self.gates if not g.passed]
