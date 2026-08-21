"""Gate 1 (repo readiness) and Gate 2 (PR health) evaluators.

Gate 3 lives in :mod:`pr_automerge.scoring` because it has enough of its own surface
(weights, thresholds, calibration) to earn a dedicated module. Gates 1 and 2 are
simpler pass/fail checks and share this file.
"""

from __future__ import annotations

from pr_automerge.models import GateResult, GateStatus


def evaluate_gate1(
    *,
    main_exists: bool,
    protection_configured: bool,
    required_checks_registered: bool,
    auto_merge_enabled: bool,
) -> GateResult:
    """Evaluate Gate 1 — is this repository even eligible for auto-merge?

    Parameters
    ----------
    main_exists : bool
        Whether a branch named ``main`` exists.
    protection_configured : bool
        Whether branch protection (or a ruleset) is configured on ``main``.
    required_checks_registered : bool
        Whether at least one required status check is registered.
    auto_merge_enabled : bool
        Whether the repo-level ``allow_auto_merge`` setting is on.

    Returns
    -------
    GateResult
        ``PASS`` only if every readiness condition holds; ``FAIL`` otherwise, naming
        the first missing condition in the rationale.
    """
    checks: list[tuple[bool, str]] = [
        (main_exists, "no 'main' branch found"),
        (protection_configured, "branch protection / ruleset not configured on main"),
        (required_checks_registered, "no required status checks registered"),
        (auto_merge_enabled, "repo setting allow_auto_merge is off"),
    ]
    missing = [reason for ok, reason in checks if not ok]

    if missing:
        return GateResult(
            gate="gate1_repo_readiness",
            status=GateStatus.FAIL,
            rationale="; ".join(missing),
            details={"missing_count": len(missing)},
        )
    return GateResult(
        gate="gate1_repo_readiness",
        status=GateStatus.PASS,
        rationale="main exists, protection configured, checks registered, auto-merge enabled",
    )


def evaluate_gate2(ci_conclusion: str | None) -> GateResult:
    """Evaluate Gate 2 — did this PR's CI/build succeed?

    Fail-closed by design (Chapter 14): a missing or unknown CI conclusion is treated
    as a **fail**, never skipped past. This is the deliberate inversion of the
    prior-art POC's ``engine.py``, where a missing signal is ``skip`` and a missing
    *blocker* therefore does not block auto-approval
    (``test_missing_signal_skips_rule_without_failing`` asserts ``auto_approve is
    True`` there). An airlock that opens when its sensor is silent is not an airlock.

    Parameters
    ----------
    ci_conclusion : str or None
        The GitHub Checks API ``conclusion`` field for the PR's head SHA — one of
        ``"success"``, ``"failure"``, ``"cancelled"``, ``"timed_out"``, etc., or
        ``None`` if no check run exists yet.

    Returns
    -------
    GateResult
        ``PASS`` only when ``ci_conclusion == "success"``. Every other value,
        including ``None``, is ``FAIL`` — never ``SKIP``.
    """
    if ci_conclusion == "success":
        return GateResult(
            gate="gate2_pr_health",
            status=GateStatus.PASS,
            rationale="CI conclusion is 'success'",
        )

    reason = "no CI conclusion found yet" if ci_conclusion is None else f"CI conclusion is {ci_conclusion!r}"
    return GateResult(
        gate="gate2_pr_health",
        status=GateStatus.FAIL,  # fail-closed: missing data is not treated as a skip
        rationale=f"{reason} — fail-closed",
    )
