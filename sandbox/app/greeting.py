"""A trivial greeting helper — the thing Gate 2's CI workflow builds and tests."""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a friendly greeting for ``name``.

    Parameters
    ----------
    name : str
        The name to greet. Whitespace is stripped; an empty name greets "World".

    Returns
    -------
    str
        A greeting string, e.g. ``"Hello, World!"``.
    """
    cleaned = name.strip() or "World"
    return f"Hello, {cleaned}!"
