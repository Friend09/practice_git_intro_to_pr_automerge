"""Tests for sandbox/app/greeting.py — this is what Gate 2's CI workflow runs."""

from __future__ import annotations

from sandbox.app.greeting import greet


def test_greet_with_name() -> None:
    """A normal name is greeted directly."""
    assert greet("Raghu") == "Hello, Raghu!"


def test_greet_strips_whitespace() -> None:
    """Leading/trailing whitespace is stripped before greeting."""
    assert greet("  Raghu  ") == "Hello, Raghu!"


def test_greet_empty_name_defaults_to_world() -> None:
    """An empty or whitespace-only name defaults to 'World'."""
    assert greet("") == "Hello, World!"
    assert greet("   ") == "Hello, World!"
