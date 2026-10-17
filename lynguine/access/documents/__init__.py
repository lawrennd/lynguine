"""Document access: readers and models for PDF/DOCX structuring (CIP-0013).

This package turns files into an explicit document model (pages, blocks,
text-layer stats). Segmentation strategies and aspect extractors build on
top in later CIP-0013 tasks. OCR is out of scope here — sparse/absent text
layers are detected only.
"""

from .model import Block, Document, Page, TextLayer
from .pdf import (
    DEFAULT_MIN_WORDS_PER_PAGE,
    PyMuPDFMissingError,
    classify_text_layer,
    read_pdf,
)

__all__ = [
    "Block",
    "Document",
    "Page",
    "TextLayer",
    "DEFAULT_MIN_WORDS_PER_PAGE",
    "PyMuPDFMissingError",
    "classify_text_layer",
    "read_pdf",
]
