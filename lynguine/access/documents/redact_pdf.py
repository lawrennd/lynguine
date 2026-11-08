"""Apply RedactTerms to a PDF (CIP-001A / REQ-0011).

Uses PyMuPDF redaction annotations. Does not discover terms — callers pass
an explicit list (from extract, contact collect, or manual entry).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from lynguine.util.redact import RedactTerm, coerce_terms, term_search_pattern

from .pdf import _import_fitz


def redact_pdf(
    source: str | Path,
    dest: str | Path,
    terms: Iterable[Any] | None,
    *,
    pages: Sequence[int] | None = None,
    max_pages: int | None = None,
) -> dict[str, Any]:
    """Redact ``terms`` from ``source`` into ``dest``.

    Parameters
    ----------
    source, dest:
        Filesystem paths.
    terms:
        RedactTerms (or bare strings). Empty terms → copy-like save with
        ``matches=0`` and no warning.
    pages:
        0-based page indices to search. If omitted, all pages up to
        ``max_pages`` (when set) or the whole document.
    max_pages:
        When ``pages`` is omitted, only the first N pages (1-based count).

    Returns
    -------
    dict with ``matches``, ``warnings``, ``dest``, ``terms``, ``pages``.
    """
    fitz = _import_fitz()
    src = Path(source)
    dst = Path(dest)
    if not src.is_file():
        raise FileNotFoundError(f"PDF not found: {src}")

    coerced = coerce_terms(terms)
    page_indices: list[int] = []
    matches = 0
    doc = fitz.open(src)
    try:
        page_indices = _resolve_pages(doc.page_count, pages=pages, max_pages=max_pages)
        for i in page_indices:
            page = doc[i]
            page_text = page.get_text("text") or ""
            for term in coerced:
                if not term_search_pattern(term).search(page_text):
                    continue
                for rect in _search_rects(page, term):
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    matches += 1
            page.apply_redactions()
        dst.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dst, garbage=4, deflate=True)
    finally:
        doc.close()

    warnings: list[str] = []
    if coerced and matches == 0:
        warnings.append(
            "No matches for configured redaction terms; "
            "output may still expose identity strings."
        )
    return {
        "matches": matches,
        "warnings": warnings,
        "dest": str(dst),
        "terms": len(coerced),
        "pages": list(page_indices),
    }


def _resolve_pages(
    page_count: int,
    *,
    pages: Sequence[int] | None,
    max_pages: int | None,
) -> list[int]:
    if pages is not None:
        return [int(p) for p in pages if 0 <= int(p) < page_count]
    limit = page_count if max_pages is None else min(page_count, max(0, int(max_pages)))
    return list(range(limit))


def _search_rects(page: Any, term: RedactTerm) -> list[Any]:
    """PyMuPDF boxes for ``term.value``; empty if the text layer has no hit."""
    value = term["value"]
    try:
        hits = page.search_for(value)
    except Exception:
        hits = []
    if hits:
        return list(hits)
    # Multi-word names may be stored with different whitespace in the PDF.
    collapsed = " ".join(value.split())
    if collapsed != value:
        try:
            hits = page.search_for(collapsed)
        except Exception:
            hits = []
        if hits:
            return list(hits)
    return []
