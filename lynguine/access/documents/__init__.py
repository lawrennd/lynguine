"""Document access: readers and models for PDF/DOCX structuring (CIP-0013).

This package turns files into an explicit document model (pages, blocks,
text-layer stats), then optional named strategies emit units. OCR is out of
scope — sparse/absent text layers are detected and refused by default.
"""

from .errors import DocumentSegmentError, SparseTextLayerError, UnknownStrategyError
from .model import Block, Document, Page, TextLayer
from .pdf import (
    DEFAULT_MIN_WORDS_PER_PAGE,
    PyMuPDFMissingError,
    classify_text_layer,
    read_pdf,
)
from .segment import (
    document_segment,
    segment_document,
    segment_pdf,
    segment_pdf_frame,
    units_to_frame,
)
from .strategy import (
    ensure_builtin_strategies,
    get_strategy,
    list_strategies,
    register_strategy,
    resolve_strategy_id,
)
from .unit import Unit

__all__ = [
    "Block",
    "Document",
    "DocumentSegmentError",
    "Page",
    "PyMuPDFMissingError",
    "SparseTextLayerError",
    "TextLayer",
    "Unit",
    "UnknownStrategyError",
    "DEFAULT_MIN_WORDS_PER_PAGE",
    "classify_text_layer",
    "document_segment",
    "ensure_builtin_strategies",
    "get_strategy",
    "list_strategies",
    "read_pdf",
    "register_strategy",
    "resolve_strategy_id",
    "segment_document",
    "segment_pdf",
    "segment_pdf_frame",
    "units_to_frame",
]
