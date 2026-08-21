"""pr_automerge — shared utilities for the Intro to PR Auto-Merge labs.

This package is the ``PRA_``-prefixed, fixture/live-dual-mode namespace that every
``labs/lab_XX_*.py`` script imports from, so that gate logic is written once and
exercised identically by notebooks, lab scripts, and (eventually) real workflow steps.

Modules
-------
gh_client   : A thin, testable wrapper around the ``gh`` CLI with a fixture-mode escape
              hatch, so every lab can run offline in CI without a GitHub token.
models      : Typed dataclasses shared across gates — ``PRMetadata``, ``GateResult``,
              ``Decision``.
scoring     : The Gate 3 risk-scoring engine (see Chapter 15).
render      : The shared "print a summary table" helper every lab uses for its
              terminal output.
"""

from __future__ import annotations

__version__ = "0.1.0"
