"""
Lab 04: Reading PR Data
=============================================================
Chapter 04 companion script.

Demonstrates the two ways of reading PR data (`gh pr view` for a single PR,
`gh pr list` for many), normalizing a raw pull object into this repo's shared
`PRMetadata` dataclass, and paginating a list larger than one page's worth of
results using `--paginate` semantics.

Usage
-----
Fixture mode (default, offline)::

    python labs/lab_04_pr_data.py

Live mode, against a real PR/repo::

    PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge \\
        python labs/lab_04_pr_data.py --pr 1

Environment Variables (PRA_ prefix)
------------------------------------
PRA_MODE       : "fixture" (default) or "live"
PRA_REPO       : "owner/name" -- required in live mode
PRA_OUTPUT_DIR : Path where output reports are written (default: output/)

References
----------
Chapter 04 — Reading PR Data
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.gh_client import run_gh  # noqa: E402
from pr_automerge.models import PRMetadata  # noqa: E402
from pr_automerge.render import section  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR: Path = Path(os.getenv("PRA_OUTPUT_DIR", "output"))

#: GitHub's per-page cap for list endpoints, and the total-files cap on the
#: paginated `/pulls/{n}/files` endpoint specifically (Chapter 04 §9).
MAX_PAGE_SIZE: int = 100
MAX_FILES_LISTED: int = 300


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def fetch_single_pr(repo: str, pr_number: int) -> dict:
    """Fetch one PR's raw object (Chapter 04 §3, `gh pr view` / `gh api`).

    Parameters
    ----------
    repo : str
        "owner/name".
    pr_number : int
        The PR to fetch.

    Returns
    -------
    dict
        The raw pull request payload.
    """
    return run_gh(["api", f"repos/{repo}/pulls/{pr_number}"], fixture="pr_raw_pull")


def normalize_pr(raw: dict, *, critical_path_hits: int = 0) -> PRMetadata:
    """Convert a raw PR object into this repo's typed :class:`PRMetadata`.

    Parameters
    ----------
    raw : dict
        A raw pull request payload, as returned by :func:`fetch_single_pr`.
    critical_path_hits : int
        Count of changed files matching a critical-path glob -- computed
        separately (Chapter 04 §9) because it requires the paginated
        `/pulls/{n}/files` endpoint, not the single-PR object.

    Returns
    -------
    PRMetadata
        The normalized, gate-ready representation.
    """
    return PRMetadata(
        number=raw["number"],
        title=raw["title"],
        base=raw["base"]["ref"],
        head=raw["head"]["ref"],
        additions=raw["additions"],
        deletions=raw["deletions"],
        changed_files=raw["changed_files"],
        critical_path_hits=critical_path_hits,
        draft=raw.get("draft", False),
    )


def list_open_prs(repo: str, *, limit: int = 100) -> list[dict]:
    """List PRs for a repo, `gh pr list`-style (Chapter 04 §5).

    Parameters
    ----------
    repo : str
        "owner/name".
    limit : int
        Maximum number of PRs to request -- mirrors `gh pr list --limit`.

    Returns
    -------
    list[dict]
        Each item: {"number": ..., "title": ..., "state": ...}.
    """
    result = run_gh(
        ["pr", "list", "--repo", repo, "--limit", str(limit), "--json", "number,title,state"],
        fixture="pr_list_sample",
    )
    return result["prs"] if isinstance(result, dict) else result


def paginate_in_chunks(items: list[dict], *, page_size: int) -> list[list[dict]]:
    """Split a flat list into `page_size`-sized chunks (Chapter 04 §9-10).

    This mirrors, in miniature, what `gh api --paginate` does automatically by
    following the response's `Link: rel="next"` header: fetch a page, check for
    more, fetch the next page, repeat -- until a response has no `next` link.

    Parameters
    ----------
    items : list[dict]
        The full, already-fetched result set (fixture mode has no real HTTP
        pagination to demonstrate, so this simulates the *shape* of paging over
        data GitHub would otherwise hand back one page at a time).
    page_size : int
        Items per page -- GitHub's REST list endpoints cap this at 100.

    Returns
    -------
    list[list[dict]]
        The items split into pages of at most `page_size`.
    """
    return [items[i : i + page_size] for i in range(0, len(items), page_size)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Fetch one PR, normalize it, then list and paginate several PRs."""
    parser = argparse.ArgumentParser(description="Chapter 04 demo: reading PR data.")
    parser.add_argument("--pr", type=int, default=101)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get("PRA_MODE", "fixture")
    repo = os.environ.get("PRA_REPO", "example/example") if mode == "live" else "example/example"

    section(f"Single PR: #{args.pr}, raw -> normalized")
    raw = fetch_single_pr(repo, args.pr)
    metadata = normalize_pr(raw)
    print(f"raw additions/deletions/changed_files: {raw['additions']}/{raw['deletions']}/{raw['changed_files']}")
    print(f"normalized: {metadata}")
    print(f"lines_changed property: {metadata.lines_changed}")

    section("Listing PRs (gh pr list)")
    prs = list_open_prs(repo, limit=100)
    print(f"fetched {len(prs)} PRs (page size cap is {MAX_PAGE_SIZE})")

    section("Paginating the results into page-sized chunks")
    pages = paginate_in_chunks(prs, page_size=5)
    for i, page in enumerate(pages, start=1):
        numbers = ", ".join(f"#{p['number']}" for p in page)
        print(f"  page {i}: {numbers}")

    print(
        f"\nNote: this file-count cap ({MAX_FILES_LISTED}) is separate from the list-endpoint\n"
        f"page-size cap ({MAX_PAGE_SIZE}) -- see Chapter 04 §9 for what happens to Gate 3's\n"
        "critical-path detection on a PR that changes more files than that."
    )


if __name__ == "__main__":
    main()
