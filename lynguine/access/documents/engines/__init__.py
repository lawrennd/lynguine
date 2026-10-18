"""Shared strategy engines that interpret YAML params (CIP-0013)."""

from __future__ import annotations

from typing import Any, Protocol

from ..errors import DocumentSegmentError
from ..model import Document
from ..unit import Unit


class SegmentEngine(Protocol):
    """Engine: document + params → units for a declared aspect."""

    name: str

    def run(
        self,
        document: Document,
        params: dict[str, Any],
        *,
        strategy_id: str,
        aspects: tuple[str, ...],
    ) -> list[Unit]:
        ...


_ENGINES: dict[str, SegmentEngine] = {}


def register_engine(engine: SegmentEngine) -> SegmentEngine:
    _ENGINES[engine.name] = engine
    return engine


def get_engine(name: str) -> SegmentEngine:
    ensure_builtin_engines()
    if name not in _ENGINES:
        known = ", ".join(sorted(_ENGINES)) or "(none)"
        raise DocumentSegmentError(
            f"Unknown segment engine {name!r}. Registered: {known}"
        )
    return _ENGINES[name]


def ensure_builtin_engines() -> None:
    if "form_fields" not in _ENGINES:
        from .form_fields import FormFieldsEngine

        register_engine(FormFieldsEngine())


__all__ = [
    "SegmentEngine",
    "ensure_builtin_engines",
    "get_engine",
    "register_engine",
]
