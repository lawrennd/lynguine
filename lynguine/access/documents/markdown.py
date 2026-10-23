"""Markdown reader into the document model (CIP-0013).

Plain UTF-8 files — no PDF/DOCX extra. YAML frontmatter (if present) is
parsed into ``Document.metadata['frontmatter']`` and stripped from the
body so segmenters see the dialogue text only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from lynguine.access.paths import confine_configured_path, resolve_under_roots

from .model import Block, Document, Page, TextLayer
from .pdf import classify_text_layer

_FRONTMATTER = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)


def _split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER.match(raw)
    if not match:
        return {}, raw
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    body = raw[match.end() :]
    return data, body.lstrip("\n")


def _blocks_from_body(body: str) -> list[Block]:
    blocks: list[Block] = []
    for i, para in enumerate(body.split("\n")):
        text = para.replace("\xa0", " ").strip()
        if not text:
            continue
        blocks.append(
            Block(
                page_index=0,
                block_index=i,
                x0=0.0,
                y0=float(i),
                x1=1.0,
                y1=float(i) + 1.0,
                text=text,
                block_type="text",
                word_count=len(text.split()),
            )
        )
    return blocks


def read_markdown(
    path: str,
    *,
    allowed_roots: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> Document:
    """Open a markdown file under path confinement and return a :class:`Document`.

    The whole file is one logical page. Non-empty lines become text blocks.
    """
    if details is not None:
        resolved = confine_configured_path(path, details)
    elif allowed_roots is not None:
        resolved = resolve_under_roots(path, allowed_roots)
    else:
        resolved = path

    raw = Path(resolved).read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(raw)
    blocks = _blocks_from_body(body)
    total_words = len(body.split()) if body.strip() else 0
    text_layer, words_per_page = classify_text_layer(total_words, page_count=1)
    page = Page(
        index=0,
        width=1.0,
        height=float(max(len(blocks), 1)),
        text=body,
        word_count=total_words,
        blocks=tuple(blocks),
    )
    return Document(
        path=resolved,
        reader="markdown",
        page_count=1,
        total_words=total_words,
        words_per_page=words_per_page,
        text_layer=text_layer,
        pages=(page,),
        metadata={
            "frontmatter": frontmatter,
            "line_count": len(blocks),
        },
    )
