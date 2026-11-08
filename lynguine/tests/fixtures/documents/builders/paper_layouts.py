"""Synthetic academic paper first-page PDFs for paper_frontmatter tests."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def make_academic_paper_front(path: str | Path) -> Path:
    """Build a single-column paper with title, authors, affiliation, Abstract.

    Uses only synthetic names and emails — not a real paper.
    """
    path = Path(path)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(72, 48, 520, 780),
        "\n".join(
            [
                "A Synthetic Study of Document Front-Matter Extraction",
                "Ada Lovelace and Alan Turing",
                "University of Example",
                "ada.lovelace@example.com",
                "",
                "Abstract",
                "We describe a synthetic fixture used only for layout tests. "
                "It must not be treated as a real scholarly work.",
                "",
                "1 Introduction",
                "Further body text for the fixture appears here.",
            ]
        ),
        fontsize=11,
    )
    doc.save(path)
    doc.close()
    return path


def make_academic_paper_three_authors(path: str | Path) -> Path:
    """Title plus comma-and list of three synthetic authors."""
    path = Path(path)
    doc = fitz.open()
    page = doc.new_page()
    filler = " ".join(f"body{i}" for i in range(80))
    page.insert_textbox(
        fitz.Rect(72, 48, 520, 780),
        "\n".join(
            [
                "Another Synthetic Proceedings Title",
                "Grace Hopper, Katherine Johnson, and Margaret Hamilton",
                "Example Laboratory",
                "",
                "ABSTRACT",
                "Short abstract for recogniser and stop-heading tests. " + filler,
                "",
                "1 Introduction",
                "Further synthetic introduction text. " + filler,
            ]
        ),
        fontsize=11,
    )
    doc.save(path)
    doc.close()
    return path
