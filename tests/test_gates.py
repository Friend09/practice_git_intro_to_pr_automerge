"""Unit tests for Gate 1 (repo readiness) and Gate 2 (PR health)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pr_automerge.gates import evaluate_gate1, evaluate_gate2


def test_gate1_passes_when_everything_configured() -> None:
    """All four readiness conditions true -> PASS."""
    result = evaluate_gate1(
        main_exists=True,
        protection_configured=True,
        required_checks_registered=True,
        auto_merge_enabled=True,
    )
    assert result.passed


def test_gate1_fails_and_names_the_missing_condition() -> None:
    """A single missing condition is named in the rationale, not swallowed."""
    result = evaluate_gate1(
        main_exists=True,
        protection_configured=False,
        required_checks_registered=True,
        auto_merge_enabled=True,
    )
    assert not result.passed
    assert "protection" in result.rationale


def test_gate2_passes_on_success() -> None:
    """A CI conclusion of 'success' passes Gate 2."""
    assert evaluate_gate2("success").passed


def test_gate2_fails_on_explicit_failure() -> None:
    """A CI conclusion of 'failure' fails Gate 2."""
    assert not evaluate_gate2("failure").passed


def test_gate2_fails_closed_on_missing_conclusion() -> None:
    """The critical inversion of the prior-art POC: missing data is FAIL, not SKIP.

    ``pr-auto-approve-poc``'s engine treats a missing signal as ``skip``, which
    removes it from both the numerator and denominator of its readiness ratio — so a
    missing *blocker* rule does not block approval
    (``test_missing_signal_skips_rule_without_failing`` there asserts
    ``auto_approve is True``). This repo is fail-closed: a gate with no data never
    passes.
    """
    result = evaluate_gate2(None)
    assert not result.passed
    assert result.status.value == "fail"
    assert "fail-closed" in result.rationale
