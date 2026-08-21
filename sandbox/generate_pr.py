"""Generate a working-tree diff of a known, controllable size for gate practice.

This module writes filler content under ``sandbox/generated/`` so that opening a PR
afterward produces a diff of approximately the requested line and file counts —
letting you verify Gate 3's risk-scoring verdicts against real GitHub PRs rather than
only fixtures (Chapter 15's hands-on section, and the verification table in the
project plan).

Usage
-----
Run directly::

    python sandbox/generate_pr.py --lines 120 --files 6

This only edits the working tree. Commit, push, and open the PR yourself::

    git checkout -b test/small-feature
    python sandbox/generate_pr.py --lines 120 --files 6
    git add sandbox/generated/
    git commit -m "test: small feature (120 lines, 6 files)"
    git push -u origin HEAD
    gh pr create --fill --base main
"""

from __future__ import annotations

import argparse
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parent / "generated"


def _filler_lines(n: int, seed_label: str) -> list[str]:
    """Build ``n`` deterministic, readable filler lines for one generated file.

    Parameters
    ----------
    n : int
        Number of lines to generate.
    seed_label : str
        A label embedded in each line so generated files are easy to distinguish.

    Returns
    -------
    list[str]
        The generated lines, without trailing newlines.
    """
    return [f"# {seed_label} filler line {i:04d}" for i in range(n)]


def generate(lines: int, files: int, output_dir: Path = GENERATED_DIR) -> list[Path]:
    """Write ``files`` filler files whose combined line count is ``lines``.

    Parameters
    ----------
    lines : int
        Total lines to distribute across the generated files.
    files : int
        Number of files to create. Must be at least 1.
    output_dir : Path
        Directory to write into (default: ``sandbox/generated/``).

    Returns
    -------
    list[Path]
        The files that were written.

    Raises
    ------
    ValueError
        If ``files`` is less than 1 or ``lines`` is negative.
    """
    if files < 1:
        raise ValueError("files must be at least 1")
    if lines < 0:
        raise ValueError("lines must be non-negative")

    output_dir.mkdir(parents=True, exist_ok=True)
    base_lines, remainder = divmod(lines, files)

    written: list[Path] = []
    for i in range(files):
        n = base_lines + (1 if i < remainder else 0)
        path = output_dir / f"filler_{i:02d}.py"
        label = f"generated/filler_{i:02d}"
        path.write_text("\n".join(_filler_lines(n, label)) + "\n")
        written.append(path)

    return written


def main() -> None:
    """CLI entrypoint: parse --lines/--files and write the generated files."""
    parser = argparse.ArgumentParser(
        description="Generate a diff of a known size under sandbox/generated/."
    )
    parser.add_argument("--lines", type=int, required=True, help="total lines to generate")
    parser.add_argument("--files", type=int, required=True, help="number of files to spread across")
    args = parser.parse_args()

    written = generate(args.lines, args.files)

    print(f"Wrote {args.lines} lines across {len(written)} file(s):")
    for path in written:
        print(f"  {path.relative_to(Path.cwd()) if path.is_absolute() else path}")
    print("\nNext steps:")
    print("  git add sandbox/generated/")
    print(f'  git commit -m "test: sandbox PR ({args.lines} lines, {args.files} files)"')
    print("  git push -u origin HEAD")
    print("  gh pr create --fill --base main")


if __name__ == "__main__":
    main()
