"""Unit tests for the Gate 3 risk-scoring engine (Chapter 15).

Pins the exact five-row worked example carried through the chapter, the notebook,
and the README so the numbers can never drift silently.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pr_automerge.models import PRMetadata
from pr_automerge.scoring import RiskConfig, compute_risk, evaluate_gate3


def _pr(lines_add: int, lines_del: int, files: int, critical: int) -> PRMetadata:
    return PRMetadata(
        number=1,
        title="test",
        base="main",
        head="test-branch",
        additions=lines_add,
        deletions=lines_del,
        changed_files=files,
        critical_path_hits=critical,
    )


@pytest.mark.parametrize(
    ("lines_add", "lines_del", "files", "critical", "expected_risk"),
    [
        (2, 1, 1, 0, 5.9),  # typo fix
        (100, 20, 6, 0, 66.0),  # small feature
        (30, 10, 2, 1, 67.0),  # touches a critical path
        (250, 90, 14, 0, 172.0),  # refactor
        (700, 200, 30, 2, 510.0),  # large migration
    ],
)
def test_compute_risk_matches_worked_example(
    lines_add: int, lines_del: int, files: int, critical: int, expected_risk: float
) -> None:
    """The five-row table in Chapter 15 / README must match this engine exactly."""
    pr = _pr(lines_add, lines_del, files, critical)
    assert compute_risk(pr, RiskConfig()) == pytest.approx(expected_risk, abs=0.05)


def test_typo_fix_merges() -> None:
    """A 3-line, 1-file PR is comfortably under threshold."""
    pr = _pr(2, 1, 1, 0)
    result = evaluate_gate3(pr)
    assert result.passed


def test_small_feature_merges_at_default_threshold() -> None:
    """A 120-line, 6-file PR sits just under the default threshold of 70."""
    pr = _pr(100, 20, 6, 0)
    result = evaluate_gate3(pr)
    assert result.passed


def test_refactor_exceeds_threshold() -> None:
    """A 340-line, 14-file refactor exceeds risk 70 and must hold for human review."""
    pr = _pr(250, 90, 14, 0)
    result = evaluate_gate3(pr)
    assert not result.passed


def test_large_migration_hits_hard_ceiling() -> None:
    """A 900-line migration is blocked by the hard ceiling, independent of its score."""
    pr = _pr(700, 200, 30, 2)
    result = evaluate_gate3(pr)
    assert not result.passed
    assert result.details["ceiling_hit"] is True


def test_lowering_threshold_can_flip_a_borderline_pr() -> None:
    """Calibration (Chapter 18): loosening the threshold changes the verdict."""
    pr = _pr(250, 90, 14, 0)  # risk 172.0
    strict = evaluate_gate3(pr, RiskConfig(threshold=70.0))
    loose = evaluate_gate3(pr, RiskConfig(threshold=200.0))
    assert not strict.passed
    assert loose.passed


def test_critical_path_hit_never_skipped() -> None:
    """Unlike the prior-art POC, Gate 3 never returns SKIP — metadata is always present."""
    pr = _pr(30, 10, 2, 1)
    result = evaluate_gate3(pr)
    assert result.status.value in {"pass", "fail"}
