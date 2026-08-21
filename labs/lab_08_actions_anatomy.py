"""
Lab 08: Actions Anatomy
=============================================================
Chapter 08 companion script.

Parses a GitHub Actions workflow file into the four layers Chapter 08 names --
workflow, trigger, jobs, steps -- and prints a structured summary. Fixture mode
parses a small embedded example (stable regardless of future edits to this repo's
real workflows); live mode parses this repo's actual `.github/workflows/ci.yml`.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_08_actions_anatomy.py

Live mode -- parses the real ci.yml from this repo::

    PRA_MODE=live python labs/lab_08_actions_anatomy.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 08 — Actions Anatomy
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
CI_WORKFLOW_PATH: Path = REPO_ROOT / ".github" / "workflows" / "ci.yml"

#: A small, stable example workflow -- deliberately not this repo's real ci.yml, so
#: this lab's fixture-mode output never drifts if that file is edited later.
SAMPLE_WORKFLOW_YAML: str = """
name: Sample CI

on:
  pull_request:
    paths:
      - 'sandbox/**'
  workflow_dispatch: {}

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
      - name: Run tests
        run: python -m pytest
"""


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def parse_workflow(yaml_text: str) -> dict:
    """Parse a workflow YAML document into a plain dict.

    Parameters
    ----------
    yaml_text : str
        The raw YAML text of a `.github/workflows/*.yml` file.

    Returns
    -------
    dict
        The parsed workflow document.
    """
    return yaml.safe_load(yaml_text)


def summarize_workflow(workflow: dict) -> dict:
    """Reduce a parsed workflow into the four-layer anatomy Chapter 08 describes.

    Parameters
    ----------
    workflow : dict
        A parsed workflow document, from :func:`parse_workflow`.

    Returns
    -------
    dict
        {"name": ..., "triggers": [...], "permissions": {...},
         "jobs": [{"job_id": ..., "runs_on": ..., "steps": [...]}]}
    """
    # PyYAML parses the bare `on:` key as the boolean True in YAML 1.1 -- this repo's
    # workflow files always quote or structure it so that doesn't happen, but a
    # defensive lookup covers both spellings.
    triggers_raw = workflow.get("on") or workflow.get(True) or {}
    triggers = list(triggers_raw.keys()) if isinstance(triggers_raw, dict) else [triggers_raw]

    jobs = []
    for job_id, job in (workflow.get("jobs") or {}).items():
        steps = [step.get("name", step.get("uses", step.get("run", "")[:30])) for step in job.get("steps", [])]
        jobs.append({"job_id": job_id, "runs_on": job.get("runs-on"), "steps": steps})

    return {
        "name": workflow.get("name", "(unnamed)"),
        "triggers": triggers,
        "permissions": workflow.get("permissions", {}),
        "jobs": jobs,
    }


def load_real_ci_workflow() -> dict:
    """Load and parse this repo's actual `.github/workflows/ci.yml` (read-only).

    Returns
    -------
    dict
        The parsed real workflow document.
    """
    return parse_workflow(CI_WORKFLOW_PATH.read_text())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse and summarize a workflow's anatomy, fixture or the real ci.yml."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")

    if mode == "live":
        section(f"Parsing the REAL workflow: {CI_WORKFLOW_PATH.relative_to(REPO_ROOT)}")
        workflow = load_real_ci_workflow()
    else:
        section("Parsing a sample workflow (fixture)")
        workflow = parse_workflow(SAMPLE_WORKFLOW_YAML)

    summary = summarize_workflow(workflow)
    print(f"name: {summary['name']}")
    print(f"triggers: {summary['triggers']}")
    print(f"permissions: {summary['permissions']}")
    for job in summary["jobs"]:
        print(f"\njob '{job['job_id']}' runs-on={job['runs_on']}:")
        for i, step in enumerate(job["steps"], start=1):
            print(f"  step {i}: {step}")

    print(
        "\nFour layers, always in this order: a workflow contains one or more jobs,\n"
        "each job runs on its own fresh runner and contains an ordered list of steps."
    )


if __name__ == "__main__":
    main()
