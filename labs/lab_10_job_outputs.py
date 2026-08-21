"""
Lab 10: Contexts, Expressions, Outputs & `needs`
=============================================================
Chapter 10 companion script.

Simulates three mechanics `${{ }}` expressions rely on: the `github` context's PR
fields, the four job-status functions (`success()`, `failure()`, `always()`,
`cancelled()`), and how one job's step output becomes readable by a downstream job
through `needs.<job_id>.outputs.<name>`.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_10_job_outputs.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 10 — Contexts, Expressions, Outputs & `needs`
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: A representative slice of the `github` context for a pull_request-triggered run.
SAMPLE_GITHUB_CONTEXT: dict = {
    "sha": "9182736450f1e2d3c4b5a69788796a5b4c3d2e1",  # the synthetic merge commit (Ch 02)
    "event": {
        "pull_request": {
            "number": 101,
            "head": {"sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"},
            "base": {"ref": "main"},
        }
    },
    "actor": "pra-bot",
    "run_id": "1234567890",
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def evaluate_status_function(name: str, job_status: str) -> bool:
    """Evaluate one of the four `if:` status functions against a simulated job status.

    Parameters
    ----------
    name : str
        One of ``"success"``, ``"failure"``, ``"cancelled"``, ``"always"``.
    job_status : str
        The simulated status so far: ``"success"``, ``"failure"``, or ``"cancelled"``.

    Returns
    -------
    bool
        Whether a step gated by ``if: <name>()`` would run.

    Raises
    ------
    ValueError
        If `name` isn't one of the four recognized functions.
    """
    if name == "always":
        return True
    if name == "success":
        return job_status == "success"
    if name == "failure":
        return job_status == "failure"
    if name == "cancelled":
        return job_status == "cancelled"
    raise ValueError(f"unrecognized status function: {name!r}")


def resolve_context_path(context: dict, path: str) -> object:
    """Resolve a dotted `github.*`-style path against a context dict.

    Parameters
    ----------
    context : dict
        A context dict, e.g. :data:`SAMPLE_GITHUB_CONTEXT`.
    path : str
        A dotted path with the leading ``github.`` already stripped, e.g.
        ``"event.pull_request.head.sha"``.

    Returns
    -------
    object
        The resolved value.

    Raises
    ------
    KeyError
        If any segment of the path is missing.
    """
    value: object = context
    for segment in path.split("."):
        value = value[segment]  # type: ignore[index]
    return value


def simulate_needs_output_passing(risk_score: float, threshold: float) -> dict:
    """Simulate a Gate-3-style job publishing an output a downstream job reads via `needs`.

    Mirrors::

        # job gate3:
        outputs:
          risk_score: ${{ steps.score.outputs.risk_score }}

        # job automerge, elsewhere:
        needs: gate3
        if: needs.gate3.outputs.risk_score <= 70

    Parameters
    ----------
    risk_score : float
        The value the upstream job's step would have written to `$GITHUB_OUTPUT`.
    threshold : float
        The downstream job's comparison threshold.

    Returns
    -------
    dict
        {"gate3_outputs": {"risk_score": ...}, "downstream_would_run": bool}
    """
    gate3_outputs = {"risk_score": str(risk_score)}
    downstream_would_run = float(gate3_outputs["risk_score"]) <= threshold
    return {"gate3_outputs": gate3_outputs, "downstream_would_run": downstream_would_run}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Demonstrate context resolution, status functions, and needs/outputs passing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("Resolving github.* context paths")
    for path in ["sha", "event.pull_request.head.sha", "event.pull_request.base.ref", "actor"]:
        value = resolve_context_path(SAMPLE_GITHUB_CONTEXT, path)
        print(f"  github.{path:<32} = {value}")

    section("The four if: status functions, evaluated against job_status='failure'")
    for fn in ["success", "failure", "cancelled", "always"]:
        runs = evaluate_status_function(fn, job_status="failure")
        print(f"  if: {fn}()  -> runs = {runs}")

    section("needs.<job>.outputs.<name>: passing Gate 3's score to automerge.yml")
    result = simulate_needs_output_passing(risk_score=66.0, threshold=70.0)
    print(f"  gate3 outputs: {result['gate3_outputs']}")
    print(f"  downstream job would run: {result['downstream_would_run']}")

    print(
        "\nNote: github.sha above is the SYNTHETIC MERGE COMMIT (Chapter 02 §13), not the\n"
        "author's own commit -- github.event.pull_request.head.sha is the one that matches\n"
        "what the PR author actually pushed."
    )


if __name__ == "__main__":
    main()
