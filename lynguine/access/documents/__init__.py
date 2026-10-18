"""Document access: readers and models for PDF/DOCX structuring (CIP-0013).

This package turns files into an explicit document model (pages, blocks,
text-layer stats), then optional named strategies emit units. OCR is out of
scope — sparse/absent text layers are detected and refused by default.
"""

from .chrome_filters import (
    apply_chrome_filters,
    is_toc_like,
    resolve_chrome_filter_flags,
    strip_running_chrome,
)
from .errors import DocumentSegmentError, SparseTextLayerError, UnknownStrategyError
from .model import Block, Document, Page, TextLayer
from .docx_reader import PythonDocxMissingError, read_docx
from .pdf import (
    DEFAULT_MIN_WORDS_PER_PAGE,
    PyMuPDFMissingError,
    classify_text_layer,
    read_pdf,
)
from .recogniser import (
    StrategyCandidate,
    choose_strategy,
    document_features,
    rank_strategies,
)
from .segment import (
    document_segment,
    extract_form_fields,
    extract_references,
    segment_document,
    segment_pdf,
    segment_pdf_frame,
    units_to_frame,
)
from .strategies.pmlr_references_v1 import ReferencesRegionNotFoundError
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
    "PythonDocxMissingError",
    "SparseTextLayerError",
    "TextLayer",
    "Unit",
    "UnknownStrategyError",
    "DEFAULT_MIN_WORDS_PER_PAGE",
    "StrategyCandidate",
    "apply_chrome_filters",
    "choose_strategy",
    "classify_text_layer",
    "document_features",
    "document_segment",
    "ensure_builtin_strategies",
    "extract_form_fields",
    "extract_references",
    "get_strategy",
    "is_toc_like",
    "list_strategies",
    "rank_strategies",
    "read_docx",
    "read_pdf",
    "register_strategy",
    "resolve_chrome_filter_flags",
    "resolve_strategy_id",
    "ReferencesRegionNotFoundError",
    "segment_document",
    "segment_pdf",
    "segment_pdf_frame",
    "strip_running_chrome",
    "units_to_frame",
]
