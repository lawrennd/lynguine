"""Named segmenter strategies and registry (CIP-0013)."""

from __future__ import annotations

from typing import Callable, Protocol

from .errors import UnknownStrategyError
from .model import Document
from .unit import Unit


class SegmentStrategy(Protocol):
    """Strategy: document model → ordered units for a declared aspect."""

    id: str
    aspects: tuple[str, ...]

    def segment(self, document: Document, **params) -> list[Unit]:
        """Segment *document* into units."""
        ...


_REGISTRY: dict[str, SegmentStrategy] = {}


def register_strategy(strategy: SegmentStrategy) -> SegmentStrategy:
    """Register *strategy* (replaces any prior entry with the same id)."""
    _REGISTRY[strategy.id] = strategy
    return strategy


def get_strategy(strategy_id: str) -> SegmentStrategy:
    if strategy_id not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise UnknownStrategyError(
            f"Unknown segment strategy {strategy_id!r}. Registered: {known}"
        )
    return _REGISTRY[strategy_id]


def list_strategies(*, aspect: str | None = None) -> list[str]:
    ids = []
    for sid, strat in sorted(_REGISTRY.items()):
        if aspect is None or aspect in strat.aspects:
            ids.append(sid)
    return ids


def resolve_strategy_id(
    strategy: str,
    *,
    aspect: str,
    document=None,
) -> str:
    """Resolve ``auto`` or an explicit id to a registered strategy id.

    When *document* is provided, ``auto`` uses the layout recogniser.
    Without a document, ``auto`` only succeeds if exactly one strategy
    is registered for *aspect* (legacy fallback).
    """
    if strategy != "auto":
        get_strategy(strategy)  # validate
        return strategy
    if document is not None:
        from .recogniser import choose_strategy

        return choose_strategy(document, aspect=aspect, strategy="auto").strategy_id
    candidates = list_strategies(aspect=aspect)
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise UnknownStrategyError(
            f"No strategies registered for aspect {aspect!r}"
        )
    raise UnknownStrategyError(
        f"strategy='auto' is ambiguous for aspect {aspect!r} without a document; "
        f"choose one of: {', '.join(candidates)}"
    )


def ensure_builtin_strategies() -> None:
    """Register built-in strategies (idempotent).

    Code strategies are registered first; packaged ``*.yml`` strategies are
    discovered beside ``strategies/`` (YAML config + engine path).
    """
    if "pub_dialogue.v1" not in _REGISTRY:
        from .strategies.pub_dialogue_v1 import PubDialogueV1

        register_strategy(PubDialogueV1())
    if "pmlr_references.v1" not in _REGISTRY:
        from .strategies.pmlr_references_v1 import PmlrReferencesV1

        register_strategy(PmlrReferencesV1())
    if "docx_chatbot.v1" not in _REGISTRY:
        from .strategies.docx_chatbot_v1 import DocxChatbotV1

        register_strategy(DocxChatbotV1())
    if "docx_workshop.v1" not in _REGISTRY:
        from .strategies.docx_workshop_v1 import DocxWorkshopV1

        register_strategy(DocxWorkshopV1())
    if "socratic_markdown.v1" not in _REGISTRY:
        from .strategies.socratic_markdown_v1 import SocraticMarkdownV1

        register_strategy(SocraticMarkdownV1())

    from .strategies.loader import load_packaged_yaml_strategies

    for strat in load_packaged_yaml_strategies():
        if strat.id not in _REGISTRY:
            register_strategy(strat)
