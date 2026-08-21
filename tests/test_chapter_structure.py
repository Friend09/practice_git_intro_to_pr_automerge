"""Structural checks on chapter markdown — enforces chapter-content.instructions.md
mechanically for the chapters that exist, so a header field or callout can't be
silently dropped during an edit.

Only chapters that already exist as full content are checked at required-section
level; stub chapters (header block only) are exempt until authored.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT / "learning_modules"

REQUIRED_HEADER_FIELDS = [
    "**Reading Time:**",
    "**Prerequisites:**",
    "**Practice Notebook:**",
    "**Reference Notebook:**",
    "**Script:**",
    "**Doc Reference:**",
    "**Depth:**",
]

REQUIRED_SECTIONS_FULL_CHAPTER = [
    "## Beginner's Guide",
    "## What You'll Learn",
    "## Table of Contents",
    "## 16. Common Pitfalls",
    "## 17. Key Takeaways",
    "## 18. What's Next",
    "## 19. Additional Resources",
    "## 20. Appendix A",
]

#: Chapters authored at full 20-section depth (see build order step 7). Others are
#: header-only stubs, checked less strictly.
FULL_CHAPTERS = {
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23",
}


def _chapter_files() -> list[Path]:
    if not CHAPTERS_DIR.exists():
        return []
    return sorted(CHAPTERS_DIR.glob("chapter_*.md"))


def _chapter_number(path: Path) -> str:
    match = re.match(r"chapter_(\d+)_", path.name)
    return match.group(1) if match else ""


@pytest.mark.parametrize("path", _chapter_files(), ids=lambda p: p.name)
def test_chapter_has_required_header_fields(path: Path) -> None:
    """Every chapter, full or stub, must declare all seven header fields."""
    text = path.read_text()
    for field in REQUIRED_HEADER_FIELDS:
        assert field in text, f"{path.name}: missing header field {field!r}"


@pytest.mark.parametrize(
    "path",
    [p for p in _chapter_files() if _chapter_number(p) in FULL_CHAPTERS],
    ids=lambda p: p.name,
)
def test_full_chapter_has_required_sections(path: Path) -> None:
    """Fully-authored chapters must carry every mandated section header."""
    text = path.read_text()
    for section in REQUIRED_SECTIONS_FULL_CHAPTER:
        assert section in text, f"{path.name}: missing required section {section!r}"


@pytest.mark.parametrize(
    "path",
    [p for p in _chapter_files() if _chapter_number(p) in FULL_CHAPTERS],
    ids=lambda p: p.name,
)
def test_full_chapter_has_both_callouts(path: Path) -> None:
    """Every full chapter needs both the Automation Engineer's Lens and Native vs
    Custom callouts — these are this repo's structural analogue of the ML repo's
    dual 'lens' callouts, and they directly target the user's stated confusion.
    """
    text = path.read_text()
    assert "🔬 Automation Engineer's Lens:" in text, f"{path.name}: missing lens callout"
    assert "🚦 Native vs Custom:" in text, f"{path.name}: missing native-vs-custom callout"


@pytest.mark.parametrize(
    "path",
    [p for p in _chapter_files() if _chapter_number(p) in FULL_CHAPTERS],
    ids=lambda p: p.name,
)
def test_full_chapter_has_no_star_ratings(path: Path) -> None:
    """Comparison tables must use the word-scale vocabulary, never star ratings."""
    text = path.read_text()
    assert "⭐⭐" not in text.replace("⭐ Optional", ""), (
        f"{path.name}: appears to use a star-rating table"
    )
