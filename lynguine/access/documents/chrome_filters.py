"""Post-segment filters for PDF chrome in body_chunks (CIP-0013).

Default is off (legacy parity with pub-dialogue). Enable via explicit flags
on ``pub_dialogue.v1`` / ``filter_chrome=True``.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace
from typing import Iterable

from .errors import DocumentSegmentError
from .unit import Unit

# Page chrome commonly woven into extracted text.
_PAGE_OF = re.compile(r"\bPage\s+\d+\s+of\s+\d+\b", re.I)
_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_PRINT_TIMESTAMP = re.compile(
    r"\b\d{1,2}/\d{1,2}/\d{4},?\s+\d{1,2}:\d{2}\b"
)
_LEADER_DOTS = re.compile(r"\.{3,}")
_CONTENTS_HEAD = re.compile(
    r"^\s*(contents|table of contents)\b", re.I
)

DEFAULT_MIN_FOOTER_REPEATS = 3


def normalize_for_duplicate(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def strip_running_chrome(text: str) -> tuple[str, list[str]]:
    """Remove page-X-of-Y, URLs, and print timestamps from *text*."""
    reasons: list[str] = []
    out = text
    if _PAGE_OF.search(out):
        out = _PAGE_OF.sub(" ", out)
        reasons.append("page_of")
    if _URL.search(out):
        out = _URL.sub(" ", out)
        reasons.append("url")
    if _PRINT_TIMESTAMP.search(out):
        out = _PRINT_TIMESTAMP.sub(" ", out)
        reasons.append("print_timestamp")
    out = re.sub(r"\s+", " ", out).strip()
    return out, reasons


def is_toc_like(text: str) -> bool:
    """Conservative TOC / contents-list detector.

    Requires leader-dot density or a Contents heading plus numbered entries.
    Avoids flagging ordinary bullet findings (e.g. AICAM arrow lists).
    """
    if not text or not text.strip():
        return False
    leaders = len(_LEADER_DOTS.findall(text))
    if leaders >= 3:
        return True
    if _CONTENTS_HEAD.search(text.strip()):
        numbered = len(re.findall(r"\b\d+(\.\d+)*\b", text))
        if leaders >= 1 or numbered >= 5:
            return True
    return False


def _word_count(text: str) -> int:
    return len(text.split()) if text and text.strip() else 0


def resolve_chrome_filter_flags(
    *,
    filter_chrome: bool = False,
    drop_duplicate_footers: bool | None = None,
    strip_running_headers: bool | None = None,
    skip_toc: bool | None = None,
) -> dict[str, bool]:
    """Resolve explicit flags; ``filter_chrome`` turns all three on when True.

    Per-flag overrides win when not ``None``.
    """
    base = bool(filter_chrome)
    return {
        "drop_duplicate_footers": (
            base if drop_duplicate_footers is None else bool(drop_duplicate_footers)
        ),
        "strip_running_headers": (
            base if strip_running_headers is None else bool(strip_running_headers)
        ),
        "skip_toc": base if skip_toc is None else bool(skip_toc),
    }


def apply_chrome_filters(
    units: Iterable[Unit],
    *,
    drop_duplicate_footers: bool = False,
    strip_running_headers: bool = False,
    skip_toc: bool = False,
    min_footer_repeats: int = DEFAULT_MIN_FOOTER_REPEATS,
    min_chunk_words: int = 40,
    min_chunk_chars: int = 80,
    empty_after_filter: str = "error",
) -> list[Unit]:
    """Filter chrome from body_chunk units.

    Parameters
    ----------
    empty_after_filter:
        ``error`` raises if filters remove every unit; ``empty`` returns [].
    """
    units_list = list(units)
    flags = {
        "drop_duplicate_footers": drop_duplicate_footers,
        "strip_running_headers": strip_running_headers,
        "skip_toc": skip_toc,
        "min_footer_repeats": min_footer_repeats,
    }
    if not any((drop_duplicate_footers, strip_running_headers, skip_toc)):
        # Parity path: leave units untouched
        return units_list

    dup_keys: set[str] = set()
    if drop_duplicate_footers:
        counts = Counter(
            normalize_for_duplicate(u.text) for u in units_list if u.text.strip()
        )
        dup_keys = {k for k, n in counts.items() if n >= min_footer_repeats and k}

    kept: list[Unit] = []
    for u in units_list:
        text = u.text

        if skip_toc and is_toc_like(text):
            continue

        if drop_duplicate_footers and normalize_for_duplicate(text) in dup_keys:
            continue

        stripped_reasons: list[str] = []
        if strip_running_headers:
            text, stripped_reasons = strip_running_chrome(text)

        if _word_count(text) < min_chunk_words or len(text) < min_chunk_chars:
            continue

        extras = dict(u.extras or {})
        extras["chrome_filters"] = {**flags, "applied": True}
        if stripped_reasons:
            extras["chrome_stripped"] = stripped_reasons
        kept.append(
            replace(
                u,
                text=text,
                word_count=_word_count(text),
                extras=extras,
            )
        )

    if not kept and units_list:
        msg = (
            "chrome filters removed all body_chunks "
            f"(started with {len(units_list)} units; flags={flags})"
        )
        if empty_after_filter == "error":
            raise DocumentSegmentError(msg)
        return []

    # Reindex for a clean exploded grain after drops
    out: list[Unit] = []
    for i, u in enumerate(kept):
        stem = u.unit_id.rsplit("::", 1)[0] if "::" in u.unit_id else u.unit_id
        out.append(
            replace(
                u,
                unit_id=f"{stem}::c{i:04d}",
                chunk_index=i,
            )
        )
    return out
