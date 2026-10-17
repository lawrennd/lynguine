"""``pub_dialogue.v1`` — paragraph/sentence chunking seeded from pub-dialogue.

Ports the access-stage behaviour of ``pub_dialogue.access.extract_chunks_from_pdf``
onto lynguine's :class:`~lynguine.access.documents.model.Document` (no OCR).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Document, TextLayer
from ..unit import Unit

# Defaults match pub-dialogue.access constants.
MIN_CHUNK_WORDS = 40
MIN_CHUNK_CHARS = 80
MAX_CHUNK_WORDS = 500
SENTENCE_FALLBACK_TARGET_WORDS = 300
SENTENCE_FALLBACK_MIN_PARAGRAPHS = 3
MIN_TEXT_COVERAGE = 0.5


def _word_count(text: str) -> int:
    return len(text.split()) if text and text.strip() else 0


def _coverage(
    paragraphs: list[str],
    total_words: int,
    min_chunk_words: int,
    min_chunk_chars: int,
) -> float:
    if total_words == 0:
        return 0.0
    kept = sum(
        _word_count(p)
        for p in paragraphs
        if _word_count(p) >= min_chunk_words and len(p) >= min_chunk_chars
    )
    return kept / total_words


def _split_into_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\d])", text)
    return [p.strip() for p in parts if p.strip()]


def _repack_sentences_into_chunks(sentences: list[str], target_words: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sent in sentences:
        sent_words = len(sent.split())
        if sent_words >= target_words:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_words = 0
            chunks.append(sent)
            continue
        if current_words + sent_words > target_words and current:
            chunks.append(" ".join(current))
            current = [sent]
            current_words = sent_words
        else:
            current.append(sent)
            current_words += sent_words
    if current:
        chunks.append(" ".join(current))
    return chunks


def _paragraph_split(full_text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", full_text)
    out = []
    for para in paragraphs:
        para = re.sub(r"\s+", " ", para).strip()
        if para:
            out.append(para)
    return out


def _block_paragraphs(document: Document) -> list[str]:
    paras = []
    for page in document.pages:
        for block in page.blocks:
            if block.block_type != "text":
                continue
            text = re.sub(r"\s+", " ", block.text).strip()
            if text:
                paras.append(text)
    return paras


class PubDialogueV1:
    """Chunk a PDF document model into ``body_chunks`` units."""

    id = "pub_dialogue.v1"
    aspects = ("body_chunks",)

    def segment(
        self,
        document: Document,
        *,
        min_chunk_words: int = MIN_CHUNK_WORDS,
        min_chunk_chars: int = MIN_CHUNK_CHARS,
        max_chunk_words: int = MAX_CHUNK_WORDS,
        sentence_fallback_target_words: int = SENTENCE_FALLBACK_TARGET_WORDS,
        sentence_fallback_min_paragraphs: int = SENTENCE_FALLBACK_MIN_PARAGRAPHS,
        min_text_coverage: float = MIN_TEXT_COVERAGE,
        **_ignored,
    ) -> list[Unit]:
        full_text = document.full_text
        total_words = document.total_words or _word_count(full_text)
        block_paragraphs = _block_paragraphs(document)
        newline_paragraphs = _paragraph_split(full_text)

        def _n_substantive(paras: list[str]) -> int:
            return sum(
                1
                for p in paras
                if _word_count(p) >= min_chunk_words and len(p) >= min_chunk_chars
            )

        def _acceptable(paras: list[str], coverage: float) -> bool:
            return (
                _n_substantive(paras) >= sentence_fallback_min_paragraphs
                and coverage >= min_text_coverage
            )

        block_cov = _coverage(
            block_paragraphs, total_words, min_chunk_words, min_chunk_chars
        )
        newline_cov = _coverage(
            newline_paragraphs, total_words, min_chunk_words, min_chunk_chars
        )
        candidates = [
            ("blocks", block_paragraphs, block_cov),
            ("newline", newline_paragraphs, newline_cov),
        ]
        chosen = next(
            ((n, p, c) for n, p, c in candidates if _acceptable(p, c)), None
        )

        if chosen is not None:
            segmentation, paragraphs, _ = chosen
        else:
            segmentation, paragraphs = "sentence", []

        if segmentation == "sentence":
            sentences = _split_into_sentences(full_text)
            packed = _repack_sentences_into_chunks(
                sentences, sentence_fallback_target_words
            )
            chunk_inputs: list[tuple[str, str]] = [
                (c, "sentence_fallback") for c in packed
            ]
        else:
            chunk_inputs = []
            for para in paragraphs:
                para = re.sub(r"\s+", " ", para).strip()
                if not para:
                    continue
                if len(para.split()) > max_chunk_words:
                    sentences = _split_into_sentences(para)
                    for sc in _repack_sentences_into_chunks(
                        sentences, sentence_fallback_target_words
                    ):
                        chunk_inputs.append((sc, "sentence_split"))
                else:
                    chunk_inputs.append((para, "paragraph"))

        stem = Path(document.path).name
        units: list[Unit] = []
        for i, (text, method) in enumerate(chunk_inputs):
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            if len(text.split()) < min_chunk_words:
                continue
            if len(text) < min_chunk_chars:
                continue
            words = text.split()
            was_truncated = False
            if len(words) > max_chunk_words:
                text = " ".join(words[:max_chunk_words])
                was_truncated = True
            units.append(
                Unit(
                    unit_id=f"{stem}::c{i:04d}",
                    text=text,
                    segment_strategy=self.id,
                    aspect="body_chunks",
                    chunk_index=i,
                    word_count=len(text.split()),
                    chunking_method=method,
                    was_truncated=was_truncated,
                    source_path=document.path,
                    extras={
                        "segmentation": segmentation,
                        "text_layer": document.text_layer.value,
                    },
                )
            )
        return units
