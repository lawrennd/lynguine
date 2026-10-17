"""Segmented unit rows produced by document strategies (CIP-0013)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Unit:
    """One exploded segment (body chunk, dialogue unit, …)."""

    unit_id: str
    text: str
    segment_strategy: str
    aspect: str
    chunk_index: int
    word_count: int
    chunking_method: str
    was_truncated: bool
    source_path: str
    extras: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        extras = d.pop("extras") or {}
        d.update(extras)
        return d
