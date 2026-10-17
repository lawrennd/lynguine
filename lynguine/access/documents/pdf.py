"""PDF reader via PyMuPDF (optional extra) with text-layer detection (CIP-0013).

No OCR: image-only / low-text PDFs are classified as ``absent`` or ``sparse``.
"""

from __future__ import annotations

import re
from typing import Any

from lynguine.access.paths import resolve_under_roots

from .model import Block, Document, Page, TextLayer

# Seeded from pub-dialogue MIN_WORDS_PER_PAGE: below this → likely image-only.
DEFAULT_MIN_WORDS_PER_PAGE: int = 30

_PYMUPDF_INSTALL = (
    "PyMuPDF is required for PDF reading. "
    "Install with: pip install 'lynguine[documents]' "
    "or: poetry install --extras documents"
)


class PyMuPDFMissingError(ImportError):
    """Raised when PDF reading is requested but PyMuPDF is not installed."""


def _import_fitz():
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError as exc:
        raise PyMuPDFMissingError(_PYMUPDF_INSTALL) from exc
    return fitz


def _word_count(text: str) -> int:
    return len(text.split()) if text and text.strip() else 0


def classify_text_layer(
    total_words: int,
    page_count: int,
    *,
    min_words_per_page: int = DEFAULT_MIN_WORDS_PER_PAGE,
) -> tuple[TextLayer, float]:
    """Classify extractable text quality without OCR.

    Returns ``(text_layer, words_per_page)``.
    """
    pages = max(1, int(page_count))
    words_per_page = total_words / pages
    if total_words <= 0:
        return TextLayer.ABSENT, words_per_page
    if words_per_page < min_words_per_page:
        return TextLayer.SPARSE, words_per_page
    return TextLayer.PRESENT, words_per_page


def _block_type_name(block_type: int) -> str:
    if block_type == 0:
        return "text"
    if block_type == 1:
        return "image"
    return "other"


def _pages_from_doc(doc) -> tuple[Page, ...]:
    pages: list[Page] = []
    for page_index, page in enumerate(doc):
        raw_text = page.get_text() or ""
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        blocks: list[Block] = []
        try:
            raw_blocks = page.get_text("blocks") or []
        except Exception:
            raw_blocks = []
        for block_index, block in enumerate(raw_blocks):
            # (x0, y0, x1, y1, text, block_no, block_type)
            if len(block) < 7:
                continue
            x0, y0, x1, y1, block_text, _bno, btype = block[:7]
            cleaned = re.sub(r"\s+", " ", str(block_text or "")).strip()
            blocks.append(
                Block(
                    page_index=page_index,
                    block_index=block_index,
                    x0=float(x0),
                    y0=float(y0),
                    x1=float(x1),
                    y1=float(y1),
                    text=cleaned,
                    block_type=_block_type_name(int(btype)),
                    word_count=_word_count(cleaned),
                )
            )
        rect = page.rect
        pages.append(
            Page(
                index=page_index,
                width=float(rect.width),
                height=float(rect.height),
                text=text,
                word_count=_word_count(text),
                blocks=tuple(blocks),
            )
        )
    return tuple(pages)


def read_pdf(
    path: str,
    *,
    allowed_roots: list[str] | None = None,
    details: dict[str, Any] | None = None,
    min_words_per_page: int = DEFAULT_MIN_WORDS_PER_PAGE,
) -> Document:
    """Open a PDF under path confinement and return a :class:`Document`.

    Parameters
    ----------
    path:
        Path to the PDF file.
    allowed_roots:
        If given, ``path`` must resolve under one of these roots
        (:func:`resolve_under_roots`). Ignored when ``details`` already
        confines via ``allowed_roots`` / ``unbounded_paths``.
    details:
        Optional flow details dict; when it contains ``allowed_roots`` and
        is not unbounded, the path is confined the same way as other access
        IO (``confine_configured_path``).
    min_words_per_page:
        Threshold for ``TextLayer.SPARSE`` (default matches pub-dialogue).
    """
    fitz = _import_fitz()

    from lynguine.access.paths import confine_configured_path

    if details is not None:
        resolved = confine_configured_path(path, details)
    elif allowed_roots is not None:
        resolved = resolve_under_roots(path, allowed_roots)
    else:
        resolved = path

    doc = fitz.open(resolved)
    try:
        pages = _pages_from_doc(doc)
        page_count = len(pages)
        total_words = sum(p.word_count for p in pages)
        text_layer, words_per_page = classify_text_layer(
            total_words,
            page_count,
            min_words_per_page=min_words_per_page,
        )
        meta: dict[str, Any] = {
            "min_words_per_page": min_words_per_page,
        }
        try:
            meta["pdf_metadata"] = dict(doc.metadata or {})
        except Exception:
            pass
        return Document(
            path=resolved,
            reader="pdf",
            page_count=page_count,
            total_words=total_words,
            words_per_page=words_per_page,
            text_layer=text_layer,
            pages=pages,
            metadata=meta,
        )
    finally:
        doc.close()
