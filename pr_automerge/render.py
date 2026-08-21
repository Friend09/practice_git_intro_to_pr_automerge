"""Shared terminal-output helpers — every lab prints a summary table this way."""

from __future__ import annotations

from pr_automerge.models import Decision, GateResult


def section(title: str) -> None:
    """Print a ``"=" * 60`` banner with a centered title, per lab output conventions.

    Parameters
    ----------
    title : str
        Section name, e.g. ``"Phase 1: Fetching PR data"``.
    """
    print("=" * 60)
    print(title)
    print("=" * 60)


def gate_table(results: list[GateResult]) -> None:
    """Print a fixed-width summary table of gate results.

    Parameters
    ----------
    results : list[GateResult]
        The gates to summarize, in evaluation order.
    """
    header = f"{'GATE':<24}{'STATUS':<8}{'RATIONALE'}"
    print(header)
    print("-" * len(header) if len(header) < 100 else "-" * 100)
    for r in results:
        print(f"{r.gate:<24}{r.status.value.upper():<8}{r.rationale}")


def decision_line(decision: Decision) -> None:
    """Print the final one-line verdict for a :class:`~pr_automerge.models.Decision`."""
    verdict = "MERGE" if decision.merge else "HOLD"
    print(f"\nPR #{decision.pr_number}: {verdict}")
    if not decision.merge:
        for g in decision.failed_gates():
            print(f"  blocked by: {g.gate} — {g.rationale}")
