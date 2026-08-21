"""
Lab 23: Capstone
=============================================================
Chapter 23 companion script.

Fulfills Chapter 01 §9's promise: an auto-merge system that can explain *why* it
merged something needs a durable audit trail, not just an in-the-moment decision.
This lab composes `labs.lab_17_airlock.decide()` -- itself already composing all
three gates -- with a JSON-lines audit log, so "why did PR #N merge?" has a
one-command answer, exactly as Chapter 01's Appendix A promised it would by the
time you reached this chapter.

Usage
-----
Run directly -- this lab composes the gate engines from `labs.lab_17_airlock`
purely in-process, so it never talks to GitHub itself (see Chapter 17's own lab for
the fixture/live-dual-mode enrollment call this one deliberately omits)::

    python labs/lab_23_capstone.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where the audit log and other output is written (default: output/)

References
----------
Chapter 23 — Capstone
Chapter 01 §9 — Designing for an Audit Trail
Chapter 17 — Wiring the Airlock
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from labs.lab_17_airlock import decide  # noqa: E402
from pr_automerge.models import Decision, PRMetadata  # noqa: E402
from pr_automerge.render import gate_table, decision_line, section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))
AUDIT_LOG_FILENAME: str = "audit_log.jsonl"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def build_audit_entry(decision: Decision) -> dict:
    """Convert a Decision into a durable, JSON-serializable audit entry.

    Parameters
    ----------
    decision : Decision
        The composed verdict from :func:`labs.lab_17_airlock.decide`.

    Returns
    -------
    dict
        {"pr_number": ..., "merge": ..., "gates": [{"gate", "status", "rationale"}, ...]}
    """
    return {
        "pr_number": decision.pr_number,
        "merge": decision.merge,
        "gates": [
            {"gate": g.gate, "status": g.status.value, "rationale": g.rationale}
            for g in decision.gates
        ],
    }


def append_audit_log(entry: dict, log_path: Path) -> None:
    """Append one audit entry to a JSON-lines log file.

    Parameters
    ----------
    entry : dict
        An entry from :func:`build_audit_entry`.
    log_path : Path
        The audit log file -- created if it doesn't exist yet.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def explain_decision(pr_number: int, log_path: Path) -> str:
    """The one-command answer to "why did/didn't PR #N merge?" (Chapter 01 §9).

    Parameters
    ----------
    pr_number : int
        Which PR to explain.
    log_path : Path
        The audit log to read -- the MOST RECENT matching entry wins, in case a
        PR was decided more than once (e.g. re-evaluated after a push).

    Returns
    -------
    str
        A human-readable explanation, or a not-found message.
    """
    if not log_path.exists():
        return f"No audit log at {log_path} -- nothing has been decided yet."

    entries = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    matching = [e for e in entries if e["pr_number"] == pr_number]
    if not matching:
        return f"No audit entry found for PR #{pr_number}."

    entry = matching[-1]
    lines = [f"PR #{pr_number}: {'MERGED' if entry['merge'] else 'HELD'}"]
    for gate in entry["gates"]:
        lines.append(f"  {gate['gate']}: {gate['status'].upper()} — {gate['rationale']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full airlock for two sample PRs, log both, then explain each."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / AUDIT_LOG_FILENAME

    safe_pr = PRMetadata(
        number=301, title="fix: correct typo in sandbox README",
        base="main", head="fix/readme-typo",
        additions=2, deletions=1, changed_files=1, critical_path_hits=0,
    )
    risky_pr = PRMetadata(
        number=302, title="migrate: restructure sandbox data layer",
        base="main", head="migrate/sandbox-data-layer",
        additions=700, deletions=200, changed_files=30, critical_path_hits=2,
    )

    section("Running the full airlock, PR #301 (a trivial, safe fix)")
    decision_301 = decide(
        safe_pr, main_exists=True, protection_configured=True,
        required_checks_registered=True, auto_merge_enabled=True, ci_conclusion="success",
    )
    gate_table(decision_301.gates)
    decision_line(decision_301)
    append_audit_log(build_audit_entry(decision_301), log_path)

    section("Running the full airlock, PR #302 (a large migration)")
    decision_302 = decide(
        risky_pr, main_exists=True, protection_configured=True,
        required_checks_registered=True, auto_merge_enabled=True, ci_conclusion="success",
    )
    gate_table(decision_302.gates)
    decision_line(decision_302)
    append_audit_log(build_audit_entry(decision_302), log_path)

    section("The one-command answer: why did each PR merge or not?")
    print(explain_decision(301, log_path))
    print()
    print(explain_decision(302, log_path))

    print(
        f"\nBoth verdicts are now durably recorded in {log_path} -- this is Chapter 01 §9's\n"
        "audit-trail promise, fulfilled: every gate's rationale, not just a bare pass/fail,\n"
        "readable months later with one function call."
    )


if __name__ == "__main__":
    main()
