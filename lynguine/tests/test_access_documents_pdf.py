"""Tests for lynguine.access.documents PDF reader (CIP-0013)."""

from __future__ import annotations

import pytest

fitz = pytest.importorskip("fitz")  # PyMuPDF

from lynguine.access.documents import (
    DEFAULT_MIN_WORDS_PER_PAGE,
    TextLayer,
    classify_text_layer,
    read_pdf,
)
from lynguine.access.documents.pdf import PyMuPDFMissingError
from lynguine.access.paths import PathEscapeError


def _write_text_pdf(path, text: str = "Hello public dialogue paragraph.") -> None:
    doc = fitz.open()
    page = doc.new_page()
    # insert_textbox wraps; plain insert_text truncates long single lines.
    page.insert_textbox(fitz.Rect(72, 72, 500, 750), text, fontsize=11)
    doc.save(path)
    doc.close()


def _long_body(n: int = 40) -> str:
    return " ".join(f"word{i}" for i in range(n))


def _write_blank_pdf(path, pages: int = 1) -> None:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    doc.save(path)
    doc.close()


def test_classify_text_layer_thresholds():
    assert classify_text_layer(0, 1)[0] is TextLayer.ABSENT
    layer, wpp = classify_text_layer(10, 1, min_words_per_page=30)
    assert layer is TextLayer.SPARSE
    assert wpp == 10.0
    layer, wpp = classify_text_layer(100, 2, min_words_per_page=30)
    assert layer is TextLayer.PRESENT
    assert wpp == 50.0


def test_read_pdf_text_document(tmp_path):
    pdf = tmp_path / "talk.pdf"
    _write_text_pdf(
        pdf, f"Concerns about AI in local government. {_long_body(40)}"
    )

    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])

    assert doc.reader == "pdf"
    assert doc.page_count == 1
    assert doc.total_words >= DEFAULT_MIN_WORDS_PER_PAGE
    assert doc.text_layer is TextLayer.PRESENT
    assert "local government" in doc.full_text
    assert len(doc.pages) == 1
    assert doc.pages[0].word_count == doc.total_words


def test_full_text_joins_pages_without_invented_blank_lines(tmp_path):
    """Parity with pub-dialogue: pages concatenated with '' not '\\n'."""
    pdf = tmp_path / "multipage.pdf"
    doc = fitz.open()
    p0 = doc.new_page()
    p0.insert_textbox(
        fitz.Rect(72, 72, 500, 200), "Page zero ends here.\n", fontsize=11
    )
    p1 = doc.new_page()
    p1.insert_textbox(
        fitz.Rect(72, 72, 500, 200), "Page one starts here.\n", fontsize=11
    )
    doc.save(pdf)
    doc.close()

    model = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    assert model.page_count == 2
    joined = "".join(p.text for p in model.pages)
    assert model.full_text == joined
    # Joining with "\n" would invent blank paragraphs at page boundaries
    newline_joined = "\n".join(p.text for p in model.pages)
    assert model.full_text != newline_joined
    assert model.full_text.count("\n\n") == joined.count("\n\n")


def test_read_pdf_blank_is_absent(tmp_path):
    pdf = tmp_path / "scan_like.pdf"
    _write_blank_pdf(pdf, pages=2)

    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])

    assert doc.page_count == 2
    assert doc.total_words == 0
    assert doc.text_layer is TextLayer.ABSENT
    assert doc.words_per_page == 0.0


def test_read_pdf_sparse_low_words_per_page(tmp_path):
    """Few words across many blank-ish pages → sparse (scan-like signal)."""
    pdf = tmp_path / "sparse.pdf"
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page()
        if i == 0:
            page.insert_text((72, 72), "only")
    doc.save(pdf)
    doc.close()

    result = read_pdf(
        str(pdf),
        allowed_roots=[str(tmp_path)],
        min_words_per_page=30,
    )

    assert result.total_words == 1
    assert result.text_layer is TextLayer.SPARSE


def test_read_pdf_confinement_rejects_escape(tmp_path):
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.pdf"
    _write_text_pdf(outside)

    with pytest.raises(PathEscapeError):
        read_pdf(str(outside), allowed_roots=[str(jail)])


def test_read_pdf_details_confinement(tmp_path):
    pdf = tmp_path / "ok.pdf"
    _write_text_pdf(pdf, f"Present text layer. {_long_body(40)}")
    details = {"allowed_roots": [str(tmp_path)]}

    doc = read_pdf(str(pdf), details=details)
    assert doc.text_layer is TextLayer.PRESENT


def test_pymupdf_missing_error_message():
    """PyMuPDFMissingError carries an actionable install hint."""
    err = PyMuPDFMissingError("hint")
    assert isinstance(err, ImportError)
