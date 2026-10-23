"""``socratic_markdown.v1`` — markdown Socratic dialogue → exchange units.

Expects ``## Exchange N`` headings with ``### User`` / ``### LLM``
subsections (L172 worksheet template). One unit per exchange. Supports
``dialogue_units`` and ``body_chunks`` so existing catalogue configs can
keep ``aspect: body_chunks``.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Document
from ..unit import Unit

MIN_CHUNK_WORDS = 40

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_EXCHANGE_HEAD = re.compile(r"^##\s+Exchange\s+(\d+)\b.*$", re.I)
_USER_HEAD = re.compile(r"^###\s+User\s*$", re.I)
_LLM_HEAD = re.compile(r"^###\s+LLM\s*$", re.I)


def _strip_comments(text: str) -> str:
    return _HTML_COMMENT.sub("", text)


def _section_text(lines: list[str]) -> str:
    return "\n".join(lines).strip()


def parse_exchanges(body: str) -> list[tuple[int, str, str]]:
    """Return ``(exchange_index, user_text, llm_text)`` in document order."""
    cleaned = _strip_comments(body).replace("\r\n", "\n").replace("\r", "\n")
    exchanges: list[tuple[int, str, str]] = []
    index: int | None = None
    mode: str | None = None
    user_lines: list[str] = []
    llm_lines: list[str] = []

    def flush() -> None:
        nonlocal index, mode, user_lines, llm_lines
        if index is None:
            return
        exchanges.append(
            (index, _section_text(user_lines), _section_text(llm_lines))
        )
        index = None
        mode = None
        user_lines = []
        llm_lines = []

    for raw in cleaned.split("\n"):
        line = raw.replace("\xa0", " ")
        m = _EXCHANGE_HEAD.match(line.strip())
        if m:
            flush()
            index = int(m.group(1))
            continue
        if index is None:
            continue
        if _USER_HEAD.match(line.strip()):
            mode = "user"
            continue
        if _LLM_HEAD.match(line.strip()):
            mode = "llm"
            continue
        if mode == "user":
            user_lines.append(line)
        elif mode == "llm":
            llm_lines.append(line)
    flush()
    return exchanges


class SocraticMarkdownV1:
    id = "socratic_markdown.v1"
    aspects = ("dialogue_units", "body_chunks")

    def segment(self, document: Document, **params) -> list[Unit]:
        min_words = int(params.get("min_chunk_words", MIN_CHUNK_WORDS) or MIN_CHUNK_WORDS)
        body = document.full_text or ""
        stem = Path(document.path).name
        units: list[Unit] = []
        for n, (ex_i, user, llm) in enumerate(parse_exchanges(body)):
            parts = []
            if user:
                parts.append(f"### User\n{user}")
            if llm:
                parts.append(f"### LLM\n{llm}")
            text = "\n\n".join(parts).strip()
            if not text:
                continue
            words = len(text.split())
            if words < min_words:
                continue
            units.append(
                Unit(
                    unit_id=f"{stem}::ex{ex_i:02d}",
                    text=text,
                    segment_strategy=self.id,
                    aspect="dialogue_units",
                    chunk_index=n,
                    word_count=words,
                    chunking_method="socratic_exchange",
                    was_truncated=False,
                    source_path=document.path,
                    extras={
                        "format": "socratic",
                        "exchange_index": ex_i,
                        "user_text": user,
                        "llm_text": llm,
                    },
                )
            )
        return units
