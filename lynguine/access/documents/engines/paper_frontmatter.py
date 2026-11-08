"""``paper_frontmatter`` engine — title/authors from academic PDF first pages.

Algorithms live here; stop headings and page bounds come from YAML strategy
``params`` (CIP-0013). Strategy id ``academic_paper_front.v1`` names a typical
digital paper layout, not a publisher.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..model import Document
from ..unit import Unit

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

_DEFAULT_STOP = (
    "Abstract",
    "ABSTRACT",
    "Introduction",
    "INTRODUCTION",
    "Keywords",
    "KEYWORDS",
    "1 Introduction",
    "1. Introduction",
)

_AFFILIATION_HINT = re.compile(
    r"(?i)\b("
    r"university|université|universität|college|institute|department|"
    r"laboratory|lab\b|school of|faculty of|centre for|center for|"
    r"affiliation|correspondence"
    r")\b"
)

_SKIP_LINE = re.compile(
    r"(?i)^\s*("
    r"arxiv:|doi:|https?://|www\.|"
    r"proceedings of|copyright|©|"
    r"preprint|under review"
    r")"
)

_AUTHOR_SPLIT = re.compile(
    r"\s+and\s+|,"
    r"|\s*&\s*",
    re.IGNORECASE,
)


def _joined_front_pages(document: Document, max_pages: int) -> str:
    pages = document.pages[: max(1, max_pages)]
    return "\n".join(page.text for page in pages)


def _stop_pattern(stop_headings: list[str]) -> re.Pattern[str]:
    escaped = [re.escape(h.strip()) for h in stop_headings if h and str(h).strip()]
    if not escaped:
        escaped = [re.escape(h) for h in _DEFAULT_STOP]
    # Line-oriented: optional leading numbering like "1 " / "1. "
    body = "|".join(escaped)
    return re.compile(rf"(?im)^\s*(?:\d+\.?\s*)?(?:{body})\b")


def _front_region(text: str, stop_headings: list[str]) -> str:
    if not text:
        return ""
    stop = _stop_pattern(stop_headings)
    m = stop.search(text)
    if m:
        return text[: m.start()].strip()
    return text.strip()


def _nonempty_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line:
            lines.append(line)
    return lines


def _looks_like_affiliation(line: str) -> bool:
    if EMAIL_RE.search(line):
        return True
    if _AFFILIATION_HINT.search(line):
        return True
    # Superscript-heavy affiliation markers (e.g. "1,2" alone)
    if re.fullmatch(r"[\d,\s\*†‡§¶]+", line):
        return True
    return False


def _looks_like_author_line(line: str) -> bool:
    if _SKIP_LINE.search(line):
        return False
    if _looks_like_affiliation(line):
        return False
    # Prefer lines with letters; reject pure numbers / punctuation
    letters = sum(c.isalpha() for c in line)
    if letters < 2:
        return False
    # Long prose paragraphs are not author lines
    if len(line.split()) > 20:
        return False
    return True


def split_author_names(raw: str) -> list[str]:
    """Split a raw author string into individual names."""
    if not raw or not str(raw).strip():
        return []
    text = str(raw).strip()
    # Drop trailing superscripts common after names: "Ada Lovelace1"
    text = re.sub(r"(?<=[A-Za-z])[\d\*†‡§¶]+(?=,|\s+and\s+|&|$)", "", text)
    parts = _AUTHOR_SPLIT.split(text)
    names: list[str] = []
    for part in parts:
        name = part.strip(" ,;")
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            continue
        # Skip leftover "and" fragments
        if name.casefold() in {"and", "&"}:
            continue
        names.append(name)
    return names


def extract_frontmatter(document: Document, params: dict[str, Any]) -> dict[str, Any]:
    """Return structured title/authors for *document* using *params*."""
    params = params or {}
    max_pages = int(params.get("max_pages") or 1)
    stop_headings = list(params.get("stop_headings") or _DEFAULT_STOP)
    text = _joined_front_pages(document, max_pages)
    region = _front_region(text, stop_headings)
    lines = [ln for ln in _nonempty_lines(region) if not _SKIP_LINE.search(ln)]

    title: str | None = None
    author_lines: list[str] = []
    emails = EMAIL_RE.findall(region)

    if lines:
        title = lines[0]
        for line in lines[1:]:
            if _looks_like_affiliation(line):
                break
            if not _looks_like_author_line(line):
                # Stop at first non-author, non-empty content after title
                if author_lines:
                    break
                continue
            author_lines.append(line)

    authors_raw = ", ".join(author_lines) if author_lines else None
    authors: list[str] = []
    for aline in author_lines:
        authors.extend(split_author_names(aline))
    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for name in authors:
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(name)
    authors = uniq

    return {
        "title": title,
        "authors": authors,
        "authors_raw": authors_raw,
        "emails": emails,
    }


class PaperFrontmatterEngine:
    """Emit one ``paper_frontmatter`` unit per document (fields in ``extras``)."""

    name = "paper_frontmatter"

    def run(
        self,
        document: Document,
        params: dict[str, Any],
        *,
        strategy_id: str,
        aspects: tuple[str, ...],
    ) -> list[Unit]:
        aspect = (
            "paper_frontmatter"
            if "paper_frontmatter" in aspects
            else aspects[0]
        )
        fields = extract_frontmatter(document, params or {})
        stem = Path(document.path).name
        summary_parts = [
            fields.get("title") or "",
            fields.get("authors_raw") or "",
        ]
        text = " — ".join(p for p in summary_parts if p).strip()
        extras = {
            **fields,
            "segment_engine": self.name,
            "paper_frontmatter": fields,
        }
        return [
            Unit(
                unit_id=f"{stem}::front0",
                text=text,
                segment_strategy=strategy_id,
                aspect=aspect,
                chunk_index=0,
                word_count=len(text.split()) if text else 0,
                chunking_method="paper_frontmatter",
                was_truncated=False,
                source_path=document.path,
                extras=extras,
            )
        ]
