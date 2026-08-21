"""
Lab 11: Tokens & Permissions
=============================================================
Chapter 11 companion script.

Encodes the token/permission matrix from `resources/token_permission_matrix.md` as
structured data, and demonstrates the `-f` vs `-F` encoding trap in `gh api` --
`-f` always sends a string, `-F` sends a typed field, and a boolean setting given
the string `"true"` can silently no-op.

Usage
-----
Run directly for a demo walkthrough::

    python labs/lab_11_tokens_and_permissions.py

Environment Variables (PRA_ prefix)
------------------------------------
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 11 — Tokens & Permissions
resources/token_permission_matrix.md
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

#: Matches resources/token_permission_matrix.md's "Can GITHUB_TOKEN Do This?" table,
#: as structured data -- every row verified live against this repo's own sandbox.
PERMISSION_OPERATIONS: list[dict] = [
    {"operation": "read_pr_metadata", "github_token_works": True, "needs_instead": None},
    {"operation": "read_pr_files_paginated", "github_token_works": True, "needs_instead": None},
    {"operation": "publish_check_run", "github_token_works": True, "needs_instead": None},
    {"operation": "post_pr_comment", "github_token_works": True, "needs_instead": None},
    {"operation": "patch_allow_auto_merge_setting", "github_token_works": True, "needs_instead": None},
    {
        "operation": "read_branch_protection_detail",
        "github_token_works": False,
        "needs_instead": "PAT or GitHub App with Administration access",
    },
    {
        "operation": "enable_auto_merge",
        "github_token_works": False,
        "needs_instead": "PAT or GitHub App with pull_requests: write",
    },
    {
        "operation": "push_to_protected_branch_as_bot",
        "github_token_works": False,
        "needs_instead": "push to an unprotected branch, or a PAT belonging to an admin",
    },
]

#: The three token identities, as structured data (mirrors the matrix's second table).
TOKEN_IDENTITIES: dict[str, dict] = {
    "GITHUB_TOKEN": {
        "exists_automatically": True,
        "lifetime": "one workflow run",
        "can_read_branch_protection": False,
        "can_enable_auto_merge": False,
    },
    "PAT": {
        "exists_automatically": False,
        "lifetime": "until revoked or expiry",
        "can_read_branch_protection": True,
        "can_enable_auto_merge": True,
    },
    "GitHub App": {
        "exists_automatically": False,
        "lifetime": "~1 hour per installation token, auto-renewed",
        "can_read_branch_protection": True,
        "can_enable_auto_merge": True,
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def check_operation(name: str) -> dict:
    """Look up one operation's row in the permission matrix.

    Parameters
    ----------
    name : str
        Operation key, e.g. ``"enable_auto_merge"``.

    Returns
    -------
    dict
        The matching matrix row.

    Raises
    ------
    KeyError
        If the operation isn't in :data:`PERMISSION_OPERATIONS`.
    """
    for row in PERMISSION_OPERATIONS:
        if row["operation"] == name:
            return row
    raise KeyError(f"no matrix entry for operation {name!r}")


def encode_gh_api_field(flag: str, value: str) -> object:
    """Simulate how `gh api -f`/`-F` encode a field value (Chapter 11 §9's trap).

    Parameters
    ----------
    flag : str
        Either ``"-f"`` (always a string) or ``"-F"`` (typed: bool/int/string).
    value : str
        The raw CLI argument value, e.g. ``"true"``.

    Returns
    -------
    object
        What actually gets sent: a `str` for `-f`, or a coerced `bool`/`int`/`str`
        for `-F`.

    Raises
    ------
    ValueError
        If `flag` isn't ``"-f"`` or ``"-F"``.
    """
    if flag == "-f":
        return value
    if flag == "-F":
        if value in ("true", "false"):
            return value == "true"
        if value.lstrip("-").isdigit():
            return int(value)
        return value
    raise ValueError(f"unrecognized flag: {flag!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Print the permission matrix, the identity comparison, and the -f/-F trap."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section("GITHUB_TOKEN operation matrix")
    for row in PERMISSION_OPERATIONS:
        works = "yes" if row["github_token_works"] else "NO"
        needs = f" (needs: {row['needs_instead']})" if row["needs_instead"] else ""
        print(f"  {row['operation']:<32} works={works}{needs}")

    section("The three token identities")
    for name, props in TOKEN_IDENTITIES.items():
        print(f"  {name:<14} lifetime={props['lifetime']!r}, can_enable_auto_merge={props['can_enable_auto_merge']}")

    section("The -f vs -F trap: encoding allow_auto_merge=true")
    wrong = encode_gh_api_field("-f", "true")
    right = encode_gh_api_field("-F", "true")
    print(f"  gh api -X PATCH ... -f allow_auto_merge=true  -> sends {wrong!r} ({type(wrong).__name__}) -- WRONG, often a silent no-op")
    print(f"  gh api -X PATCH ... -F allow_auto_merge=true  -> sends {right!r} ({type(right).__name__}) -- RIGHT")

    print(
        "\nThis exact mistake was caught building this repo's Gate 1 workflow. Default to\n"
        "-F for anything that isn't obviously text."
    )


if __name__ == "__main__":
    main()
