"""Minimal document model for access-stage PDF/DOCX structuring (CIP-0013)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TextLayer(str, Enum):
    """Extractable text-layer quality for a document.

    ``absent`` — no extractable words.
    ``sparse`` — below the words-per-page threshold (likely scan / image-only).
    ``present`` — enough extractable text for text-layer strategies.
    """

    ABSENT = "absent"
    SPARSE = "sparse"
    PRESENT = "present"


@dataclass(frozen=True)
class Block:
    """One layout block on a page (text or image)."""

    page_index: int
    block_index: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_type: str  # "text" | "image" | other
    word_count: int = 0


@dataclass(frozen=True)
class Page:
    """One page of a document."""

    index: int
    width: float
    height: float
    text: str
    word_count: int
    blocks: tuple[Block, ...] = ()


@dataclass
class Document:
    """Normalised document produced by a reader.

    Readers populate geometry and text; they do not decide research-unit
    boundaries. ``text_layer`` records detection only (no OCR).
    """

    path: str
    reader: str
    page_count: int
    total_words: int
    words_per_page: float
    text_layer: TextLayer
    pages: tuple[Page, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        # Concatenate pages with no separator — matches pub-dialogue /
        # ``"".join(page.get_text() …)``. Joining with ``"\\n"`` invents
        # blank-line paragraph breaks at page boundaries and diverges from
        # the seeded chunker.
        return "".join(page.text for page in self.pages)
