"""Gate 3 — the pure-risk PR scoring engine.

Design decision (Chapter 16 §7): this repo scores **risk**, not readiness. Size and
complexity ADD points; a HIGH score means dangerous; a PR merges only when
``risk <= threshold``. This is the deliberate opposite of the prior-art POC at
``proj_AI/dev/pr-auto-approve-poc/src/pr_gate/engine.py``, which computes a readiness
ratio (``score = earned_weight / total_weight``, merge at ``score >= 0.9``). Both are
legitimate designs; what matters is that a repo commits to exactly one and never mixes
the two mid-pipeline. See Chapter 16 for the full comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from pr_automerge.models import GateResult, GateStatus, PRMetadata

#: Points added per unit of each risk dimension. Weights are tuned so a ~100-line,
#: ~5-file PR with no critical-path touches sits comfortably under the default
#: threshold of 70, while a 300+ line PR or any critical-path touch pushes it over.
RISK_WEIGHTS: dict[str, float] = {
    "lines": 30.0,
    "files": 25.0,
    "critical_paths": 45.0,
}

#: Default merge threshold — risk at or below this value is eligible to merge.
DEFAULT_THRESHOLD: float = 70.0

#: Absolute ceiling: no PR above this many changed lines auto-merges, regardless of
#: score. This exists because the linear risk formula alone would let an enormous
#: single-file PR (many lines, one file, no critical paths) slip through with a
#: deceptively low score.
HARD_CEILING_LINES: int = 500


@dataclass(frozen=True)
class RiskConfig:
    """Tunable Gate 3 parameters — read from ``gates.yml`` or ``PRA_THRESHOLD``.

    Keeping these in a config object (rather than bare module constants, as the
    prior-art POC does with ``DEFAULT_THRESHOLD = 0.9``) is what makes Chapter 19's
    threshold calibration possible without editing source.
    """

    weights: dict[str, float] = None  # type: ignore[assignment]
    threshold: float = DEFAULT_THRESHOLD
    hard_ceiling_lines: int = HARD_CEILING_LINES

    def __post_init__(self) -> None:
        if self.weights is None:
            object.__setattr__(self, "weights", dict(RISK_WEIGHTS))


def compute_risk(pr: PRMetadata, config: RiskConfig) -> float:
    """Compute the pure-risk score for a PR.

    Parameters
    ----------
    pr : PRMetadata
        The normalized PR facts (see :mod:`pr_automerge.models`).
    config : RiskConfig
        Weights and thresholds for this repo.

    Returns
    -------
    float
        The risk score. Higher is more dangerous. There is no upper bound.

    Examples
    --------
    A 120-line, 6-file PR with no critical-path touches, under default weights:

    >>> from pr_automerge.models import PRMetadata
    >>> pr = PRMetadata(1, "Small feature", "main", "feat/x", 100, 20, 6)
    >>> round(compute_risk(pr, RiskConfig()), 1)
    66.0
    """
    w = config.weights
    return (
        (pr.lines_changed / 100.0) * w["lines"]
        + (pr.changed_files / 5.0) * w["files"]
        + pr.critical_path_hits * w["critical_paths"]
    )


def evaluate_gate3(pr: PRMetadata, config: RiskConfig | None = None) -> GateResult:
    """Evaluate Gate 3 (risk scoring) for a single PR.

    Parameters
    ----------
    pr : PRMetadata
        The normalized PR facts.
    config : RiskConfig, optional
        Defaults to :data:`RISK_WEIGHTS` / :data:`DEFAULT_THRESHOLD` /
        :data:`HARD_CEILING_LINES` if omitted.

    Returns
    -------
    GateResult
        ``PASS`` if the PR is below both the risk threshold and the hard line
        ceiling; ``FAIL`` otherwise. Gate 3 never returns ``SKIP`` — PR metadata is
        always available once the PR exists, unlike Gate 2's CI signal.
    """
    cfg = config or RiskConfig()
    risk = compute_risk(pr, cfg)

    if pr.lines_changed > cfg.hard_ceiling_lines:
        return GateResult(
            gate="gate3_risk_scoring",
            status=GateStatus.FAIL,
            rationale=(
                f"{pr.lines_changed} lines exceeds the hard ceiling of "
                f"{cfg.hard_ceiling_lines} — never auto-merged regardless of score"
            ),
            details={"risk": round(risk, 1), "threshold": cfg.threshold, "ceiling_hit": True},
        )

    passed = risk <= cfg.threshold
    return GateResult(
        gate="gate3_risk_scoring",
        status=GateStatus.PASS if passed else GateStatus.FAIL,
        rationale=(
            f"risk={risk:.1f} {'<=' if passed else '>'} threshold={cfg.threshold:.0f}"
        ),
        details={"risk": round(risk, 1), "threshold": cfg.threshold, "ceiling_hit": False},
    )
