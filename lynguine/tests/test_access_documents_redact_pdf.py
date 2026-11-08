"""PDF term redaction (CIP-001A / REQ-0011)."""

from __future__ import annotations

import pytest

fitz = pytest.importorskip("fitz")  # PyMuPDF

from lynguine.access.documents import redact_pdf
from lynguine.access.documents.pdf import read_pdf


def _write_text_pdf(path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 500, 750), text, fontsize=11)
    doc.save(path)
    doc.close()


def test_redact_pdf_removes_planted_author_string(tmp_path):
    src = tmp_path / "paper.pdf"
    dst = tmp_path / "paper_redacted.pdf"
    body = (
        "Alice Example and Bob Example study machine learning. "
        + " ".join(f"word{i}" for i in range(40))
    )
    _write_text_pdf(src, body)

    result = redact_pdf(
        src,
        dst,
        [
            {"value": "Alice Example", "kind": "name", "match": "whole_word"},
            {"value": "Bob Example", "kind": "name", "match": "whole_word"},
        ],
    )
    assert result["matches"] >= 1
    assert result["warnings"] == []
    assert dst.is_file()

    redacted = read_pdf(str(dst), allowed_roots=[str(tmp_path)])
    assert "Alice Example" not in redacted.full_text
    assert "Bob Example" not in redacted.full_text
    assert "machine learning" in redacted.full_text


def test_redact_pdf_zero_match_warning(tmp_path):
    src = tmp_path / "plain.pdf"
    dst = tmp_path / "plain_out.pdf"
    _write_text_pdf(src, "No identity strings here. " + " ".join(f"w{i}" for i in range(40)))

    result = redact_pdf(
        src,
        dst,
        [{"value": "Missing Author", "kind": "name", "match": "whole_word"}],
    )
    assert result["matches"] == 0
    assert result["warnings"]
    assert "No matches" in result["warnings"][0]
    assert dst.is_file()


def test_redact_pdf_empty_terms_no_warning(tmp_path):
    src = tmp_path / "copy.pdf"
    dst = tmp_path / "copy_out.pdf"
    _write_text_pdf(src, "Keep this text visible.")
    result = redact_pdf(src, dst, [])
    assert result["matches"] == 0
    assert result["warnings"] == []
    assert "Keep this text visible" in read_pdf(
        str(dst), allowed_roots=[str(tmp_path)]
    ).full_text
