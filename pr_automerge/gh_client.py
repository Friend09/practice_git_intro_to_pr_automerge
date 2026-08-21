"""A thin, testable wrapper around the ``gh`` CLI.

Every lab that talks to GitHub routes through :func:`run_gh` rather than calling
``subprocess.run`` directly, so that (a) no lab ever passes ``shell=True``, (b) fixture
mode is enforced in exactly one place, and (c) nothing ever accidentally logs a token.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class GhClientError(RuntimeError):
    """Raised when a ``gh`` invocation fails or fixture data is missing."""


def _mode() -> str:
    """Return the active mode: ``"fixture"`` (default) or ``"live"``."""
    return os.environ.get("PRA_MODE", "fixture")


def _repo() -> str:
    """Return the configured ``owner/name`` target repo for live calls."""
    repo = os.environ.get("PRA_REPO", "")
    if _mode() == "live" and not repo:
        raise GhClientError("PRA_MODE=live requires PRA_REPO=owner/name to be set")
    return repo


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture by name (without extension) from ``fixtures/``.

    Parameters
    ----------
    name : str
        Fixture filename stem, e.g. ``"pr_small_clean"``.

    Returns
    -------
    dict
        The parsed fixture payload.

    Raises
    ------
    GhClientError
        If the fixture file does not exist.
    """
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():
        raise GhClientError(f"no fixture named {name!r} at {path}")
    return json.loads(path.read_text())


def run_gh(args: list[str], *, fixture: str | None = None) -> dict[str, Any]:
    """Run a ``gh`` subcommand and return its parsed JSON output.

    In ``PRA_MODE=fixture`` (the default), this never touches the network — it loads
    ``fixture`` from ``fixtures/<fixture>.json`` instead. In ``PRA_MODE=live``, it
    shells out to the real ``gh`` binary against ``PRA_REPO``.

    Parameters
    ----------
    args : list[str]
        Arguments to pass to ``gh``, e.g. ``["pr", "view", "5", "--json", "state"]``.
        Never build this list with string interpolation of untrusted input.
    fixture : str, optional
        Fixture name to use in fixture mode. Required when ``PRA_MODE=fixture``.

    Returns
    -------
    dict
        The parsed JSON response.

    Raises
    ------
    GhClientError
        On a non-zero exit code, invalid JSON, or missing fixture.
    """
    if _mode() == "fixture":
        if fixture is None:
            raise GhClientError("fixture mode requires a fixture= name")
        return load_fixture(fixture)

    repo = _repo()
    full_args = ["gh", *args]
    if "--repo" not in args and "-R" not in args:
        full_args += ["--repo", repo]

    try:
        result = subprocess.run(
            full_args,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        # Never echo the full command if a token could have been embedded — it wasn't
        # here (gh reads its token from its own config), but stay defensive.
        raise GhClientError(f"gh exited {exc.returncode}: {exc.stderr.strip()}") from exc
    except FileNotFoundError as exc:
        raise GhClientError("gh CLI not found on PATH") from exc

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GhClientError(f"gh returned non-JSON output: {result.stdout[:200]!r}") from exc
