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


def make_doi_article_without_abstract_heading(path: str | Path) -> Path:
    """Nature-style first page: DOI and authors, no Abstract heading.

    Synthetic names only. ``strategy: auto`` should still select
    ``academic_paper_front.v1`` because page 0 contains a DOI.
    """
    path = Path(path)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(72, 48, 520, 780),
        "\n".join(
            [
                "Article",
                "https://doi.org/10.0000/example.1",
                "A Synthetic Study of Unheaded Abstracts",
                "Ada Lovelace 1, Alan Turing 2 & Grace Hopper 3",
                "1Example Laboratory  2Example Institute",
                "",
                "We describe a synthetic fixture. The word that usually "
                "heads this paragraph is deliberately absent.",
            ]
        ),
        fontsize=11,
    )
    doc.save(path)
    doc.close()
    return path


def make_middot_two_authors(path: str | Path) -> Path:
    """Springer-style author line joined with a middle dot."""
    path = Path(path)
    doc = fitz.open()
    page = doc.new_page()
    filler = " ".join(f"body{i}" for i in range(80))
    page.insert_textbox(
        fitz.Rect(72, 48, 520, 780),
        "\n".join(
            [
                "https://doi.org/10.0000/example.corner",
                "A Synthetic Short Comment",
                "Ada Lovelace1 · Alan Turing1",
                "",
                "Abstract",
                "Synthetic comment body for the middle-dot author splitter. " + filler,
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
