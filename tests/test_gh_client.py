"""Tests for the ``pr_automerge.gh_client`` wrapper -- all offline (subprocess is mocked).

The one behavioral contract worth pinning: ``gh api`` accepts no ``--repo`` flag, so the
wrapper must not append one to REST calls (it did until 2026-09-06, which broke every
lab's live mode for ``run_gh(["api", ...])`` with ``unknown flag: --repo``).
"""

from __future__ import annotations

import json
from unittest import mock

import pytest

from pr_automerge import gh_client


def _fake_run(captured: list[list[str]]):
    """Build a ``subprocess.run`` stand-in that records argv and returns ``{}``."""

    def _run(argv, **_kwargs):
        """Record ``argv`` and return a successful, JSON-bodied fake process result."""
        captured.append(list(argv))
        return mock.Mock(stdout=json.dumps({"ok": True}), stderr="", returncode=0)

    return _run


def test_fixture_mode_never_shells_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture mode loads from ``fixtures/`` and never touches ``subprocess``."""
    monkeypatch.setenv("PRA_MODE", "fixture")
    with mock.patch.object(gh_client.subprocess, "run", side_effect=AssertionError):
        data = gh_client.run_gh(["api", "repos/x/y/pulls/101"], fixture="pr_raw_pull")
    assert data["number"] == 101


def test_fixture_mode_requires_a_fixture_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fixture-mode call without ``fixture=`` is a programming error, not a silent pass."""
    monkeypatch.setenv("PRA_MODE", "fixture")
    with pytest.raises(gh_client.GhClientError):
        gh_client.run_gh(["pr", "view", "1"])


def test_live_api_call_does_not_get_repo_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """``gh api`` has no ``--repo`` flag; the wrapper must not append one."""
    monkeypatch.setenv("PRA_MODE", "live")
    monkeypatch.setenv("PRA_REPO", "owner/name")
    captured: list[list[str]] = []
    with mock.patch.object(gh_client.subprocess, "run", side_effect=_fake_run(captured)):
        gh_client.run_gh(["api", "repos/owner/name/actions/runs"])
    assert captured == [["gh", "api", "repos/owner/name/actions/runs"]]


def test_live_porcelain_call_gets_repo_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Porcelain subcommands (``pr``, ``run``, ...) still receive ``--repo``."""
    monkeypatch.setenv("PRA_MODE", "live")
    monkeypatch.setenv("PRA_REPO", "owner/name")
    captured: list[list[str]] = []
    with mock.patch.object(gh_client.subprocess, "run", side_effect=_fake_run(captured)):
        gh_client.run_gh(["pr", "view", "101", "--json", "state"])
    assert captured[0][-2:] == ["--repo", "owner/name"]


def test_live_mode_requires_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live mode without ``PRA_REPO`` fails closed before any subprocess call."""
    monkeypatch.setenv("PRA_MODE", "live")
    monkeypatch.delenv("PRA_REPO", raising=False)
    with pytest.raises(gh_client.GhClientError):
        gh_client.run_gh(["pr", "view", "1"])
