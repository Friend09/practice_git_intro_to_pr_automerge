"""
Lab 13: Debugging Workflows That Didn't Fire
=============================================================
Chapter 13 companion script.

Encodes the diagnostic checklist for "why didn't my workflow run" as runnable
checks: YAML syntax validation, path-filter matching (does this PR's changed-file
set actually match a `paths:` glob), and event-type matching against an `on:` block.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_13_why_no_trigger.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 13 — Debugging Workflows That Didn't Fire
"""

from __future__ import annotations

import fnmatch
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

#: The ordered diagnostic checklist from Chapter 13 §14, as structured data.
DIAGNOSTIC_CHECKLIST: list[str] = [
    "Does the workflow file parse as valid YAML at all?",
    "Is the workflow file on the DEFAULT branch? (schedule/workflow_dispatch need this)",
    "Does the fired event type match anything under on:?",
    "If on: has a paths: filter, does the changed-file set actually match a glob?",
    "If on: has a branches: filter, does the target branch match?",
    "Is the workflow disabled in the repo's Actions settings?",
    "Is this a fork PR hitting a restriction on secrets/workflow runs?",
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def diagnose_yaml_syntax(yaml_text: str) -> dict:
    """Attempt to parse a workflow file, reporting a syntax error's location if any.

    A YAML/schema error in a workflow file typically means the ENTIRE workflow
    fails to register at all -- not just the malformed step (Chapter 08 §16.2).

    Parameters
    ----------
    yaml_text : str
        Raw workflow YAML text.

    Returns
    -------
    dict
        {"valid": bool, "error": str | None, "line": int | None}
    """
    try:
        yaml.safe_load(yaml_text)
        return {"valid": True, "error": None, "line": None}
    except yaml.YAMLError as exc:
        line = None
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            line = mark.line + 1
        return {"valid": False, "error": str(exc).splitlines()[0], "line": line}


def check_path_filter_match(changed_files: list[str], path_globs: list[str]) -> bool:
    """Check whether any changed file matches any `paths:` glob (Chapter 13 §7).

    Parameters
    ----------
    changed_files : list[str]
        Repo-relative paths a PR touched.
    path_globs : list[str]
        The workflow's `on.pull_request.paths` list, e.g. ``["sandbox/**"]``.

    Returns
    -------
    bool
        Whether the trigger would fire for this PR at all.
    """
    return any(
        fnmatch.fnmatch(path, glob) for path in changed_files for glob in path_globs
    )


def check_event_type_match(fired_event: str, on_block: dict) -> bool:
    """Check whether a fired event type is even declared under `on:`.

    Parameters
    ----------
    fired_event : str
        The event GitHub fired, e.g. ``"pull_request"``.
    on_block : dict
        The workflow's parsed `on:` mapping.

    Returns
    -------
    bool
        Whether this workflow subscribes to that event at all.
    """
    return fired_event in on_block


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all three diagnostics against representative examples."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("1. YAML syntax check")
    broken_yaml = "on:\n  pull_request:\n  paths:\n   - 'sandbox/**'\n  bad indent here"
    result = diagnose_yaml_syntax(broken_yaml)
    print(f"  valid={result['valid']}, line={result['line']}, error={result['error']}")

    good_yaml = "on:\n  pull_request:\n    paths:\n      - 'sandbox/**'\n"
    result = diagnose_yaml_syntax(good_yaml)
    print(f"  valid={result['valid']} (well-formed example)")

    section("2. Path-filter matching")
    changed = ["learning_modules/chapter_13_debugging_workflows.md"]
    matches = check_path_filter_match(changed, ["sandbox/**"])
    print(f"  changed files: {changed}")
    print(f"  matches 'sandbox/**'? {matches}  (a curriculum-only PR correctly never triggers a gate)")

    changed = ["sandbox/generated/pr_120.py"]
    matches = check_path_filter_match(changed, ["sandbox/**"])
    print(f"  changed files: {changed}")
    print(f"  matches 'sandbox/**'? {matches}  (a sandbox PR correctly triggers the gate)")

    section("3. Event-type matching")
    on_block = {"pull_request": {"paths": ["sandbox/**"]}, "workflow_dispatch": {}}
    for event in ["pull_request", "push", "workflow_dispatch"]:
        print(f"  fired={event!r} in on: block? {check_event_type_match(event, on_block)}")

    section("The full diagnostic checklist")
    for i, item in enumerate(DIAGNOSTIC_CHECKLIST, start=1):
        print(f"  [{i}] {item}")


if __name__ == "__main__":
    main()
