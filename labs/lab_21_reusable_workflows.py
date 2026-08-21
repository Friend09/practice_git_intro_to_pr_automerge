"""
Lab 21: Reusable Workflows & Composite Actions
=============================================================
Chapter 21 companion script.

Parses this repo's real `gate2-pr-health.yml` and `gate3-score.yml` (read-only) to
find their duplicated scaffold steps -- checkout + setup-python -- as a concrete
case study for what a composite action could extract, and builds representative
`action.yml` (composite action) and reusable-workflow structures to compare.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_21_reusable_workflows.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 21 — Reusable Workflows & Composite Actions
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR: Path = REPO_ROOT / ".github" / "workflows"

#: A representative composite action -- the extraction this repo COULD make (not
#: applied to the live workflows; those stay out of scope for this curriculum's
#: content edits). Composite actions are STEP-level reuse: invoked with `uses:`
#: inside a job's `steps:` list, never defining their own jobs.
EXAMPLE_COMPOSITE_ACTION: dict = {
    "name": "Setup Python Gate Environment",
    "description": "Checkout + Python setup shared by every gate workflow.",
    "runs": {
        "using": "composite",
        "steps": [
            {"name": "Checkout", "uses": "actions/checkout@v4"},
            {
                "name": "Set up Python",
                "uses": "actions/setup-python@v5",
                "with": {"python-version": "3.12"},
            },
        ],
    },
}

#: A representative reusable workflow -- JOB-level reuse: invoked with `uses:` at
#: the JOB level (not inside a steps: list), can define multiple jobs, and
#: exchanges typed inputs/secrets/outputs via `workflow_call`.
EXAMPLE_REUSABLE_WORKFLOW: dict = {
    "name": "Reusable Gate Check Publisher",
    "on": {
        "workflow_call": {
            "inputs": {"check_name": {"type": "string", "required": True}},
            "secrets": {"token": {"required": True}},
            "outputs": {"conclusion": {"value": "${{ jobs.publish.outputs.conclusion }}"}},
        }
    },
    "jobs": {"publish": {"runs-on": "ubuntu-latest", "steps": []}},
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def find_shared_scaffold_steps(*workflow_paths: Path) -> list[str]:
    """Find step `uses:`/`name:` values shared across multiple real workflow files.

    Parameters
    ----------
    *workflow_paths : Path
        One or more real `.github/workflows/*.yml` files to compare (read-only).

    Returns
    -------
    list[str]
        Step identifiers (the `uses:` value, or `name:` if no `uses:`) that
        appear in the steps of EVERY given workflow's first job.
    """
    step_sets = []
    for path in workflow_paths:
        doc = yaml.safe_load(path.read_text())
        first_job = next(iter(doc["jobs"].values()))
        identifiers = {step.get("uses") or step.get("name") for step in first_job.get("steps", [])}
        step_sets.append(identifiers)

    shared = step_sets[0]
    for s in step_sets[1:]:
        shared &= s
    return sorted(i for i in shared if i)


def describe_reuse_mechanism(mechanism: str) -> dict:
    """Return the defining properties of "composite action" or "reusable workflow".

    Parameters
    ----------
    mechanism : str
        Either ``"composite_action"`` or ``"reusable_workflow"``.

    Returns
    -------
    dict
        {"invoked_from": ..., "can_define_jobs": bool, "typed_io": bool}

    Raises
    ------
    ValueError
        For any other input.
    """
    if mechanism == "composite_action":
        return {"invoked_from": "inside a job's steps: list", "can_define_jobs": False, "typed_io": False}
    if mechanism == "reusable_workflow":
        return {"invoked_from": "at the job level (uses: on the job itself)", "can_define_jobs": True, "typed_io": True}
    raise ValueError(f"unrecognized mechanism: {mechanism!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Find real shared scaffold steps and compare the two reuse mechanisms."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("Shared scaffold steps: gate2-pr-health.yml vs gate3-score.yml")
    shared = find_shared_scaffold_steps(
        WORKFLOWS_DIR / "gate2-pr-health.yml", WORKFLOWS_DIR / "gate3-score.yml"
    )
    for step in shared:
        print(f"  {step}")
    print(f"\n  {len(shared)} step(s) duplicated verbatim across both real workflows.")

    section("Composite action vs reusable workflow")
    for mechanism in ["composite_action", "reusable_workflow"]:
        props = describe_reuse_mechanism(mechanism)
        print(f"  {mechanism}:")
        for key, value in props.items():
            print(f"    {key}: {value}")

    section("Example composite action structure (not applied to this repo's live workflows)")
    print(yaml.safe_dump(EXAMPLE_COMPOSITE_ACTION, sort_keys=False))

    print(
        "Note: this lab only READS the real workflow files to find duplication -- it never\n"
        "writes to .github/workflows/, which is out of scope for this curriculum's own content."
    )


if __name__ == "__main__":
    main()
