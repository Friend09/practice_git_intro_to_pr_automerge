"""Enforce the reference/practice notebook pairing contract.

Adapted from proj_ml_intro_to_ml's tests/test_notebook_pairs.py, with one deliberate
fix: that repo's byte-identical-markdown rule made the practice copy's own title cell
read "(Reference)" — a leak nobody intended. Here, cell 0 (the title cell) is exempt
from the identical-markdown check so it may legitimately differ ("(Reference)" vs
nothing), and every other markdown cell must still match exactly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT / "notebooks"

#: chapter number -> reference notebook filename stem (without .ipynb), for pairs
#: that exist. Extend this as chapters are backfilled.
PAIRED_NOTEBOOKS: dict[str, str] = {
    "01": "lab_01_airlock_principle",
    "15": "lab_15_risk_scoring",
}


def normalize_source(source) -> str:
    """Normalize a notebook cell's `source` field (list[str] or str) to one string."""
    if isinstance(source, list):
        return "".join(source).strip()
    return (source or "").strip()


def _load(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data.get("cells", [])


@pytest.mark.parametrize("chapter", sorted(PAIRED_NOTEBOOKS), ids=lambda c: f"ch{c}")
def test_notebook_pairs_have_matching_structure(chapter: str) -> None:
    """Reference and practice notebooks should differ only in code content (and the
    title cell, which is allowed to say "(Reference)")."""
    ref_path = NOTEBOOKS_DIR / f"{PAIRED_NOTEBOOKS[chapter]}.ipynb"
    practice_path = NOTEBOOKS_DIR / f"practice_{chapter}.ipynb"

    if not ref_path.exists() or not practice_path.exists():
        pytest.skip(f"chapter {chapter} notebook pair not yet generated")

    reference_cells = _load(ref_path)
    practice_cells = _load(practice_path)

    assert len(reference_cells) == len(practice_cells), (
        f"Cell count mismatch for chapter {chapter}: "
        f"{len(reference_cells)} != {len(practice_cells)}"
    )

    for index, (reference_cell, practice_cell) in enumerate(
        zip(reference_cells, practice_cells)
    ):
        assert reference_cell["cell_type"] == practice_cell["cell_type"], (
            f"Cell type mismatch for chapter {chapter} at cell {index}"
        )

        if reference_cell["cell_type"] == "markdown":
            ref_text = normalize_source(reference_cell.get("source"))
            prac_text = normalize_source(practice_cell.get("source"))
            if index == 0:
                # Title cell: allowed to differ only by a trailing "(Reference)".
                stripped_ref = re.sub(r"\s*\(Reference\)\s*$", "", ref_text)
                assert stripped_ref == prac_text, (
                    f"Title cell for chapter {chapter} differs beyond '(Reference)'"
                )
                continue
            assert ref_text == prac_text, f"Markdown mismatch for chapter {chapter} at cell {index}"
            continue

        assert normalize_source(
            reference_cell.get("source")
        ).strip(), f"Reference code cell unexpectedly empty for chapter {chapter} at cell {index}"
        assert not normalize_source(
            practice_cell.get("source")
        ).strip(), f"Practice code cell must be empty for chapter {chapter} at cell {index}"
