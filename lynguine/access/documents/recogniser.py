"""Layout recogniser v0 — feature extraction and strategy ranking (CIP-0013)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .model import Document, TextLayer
from .strategy import ensure_builtin_strategies, list_strategies

_PARTICIPANT = re.compile(r"^\s*Participant\s+\d{3,}\s*$", re.I | re.M)
_TRANSCRIPT = re.compile(r"^\s*Conversation Transcript\s*:?\s*$", re.I | re.M)
_SPEAKER = re.compile(r"^\s*(Speaker\s*\d+|S\d+|Facilitator)\s*[:\-–.\t]", re.I | re.M)
_REF_HEADING = re.compile(
    r"^\s*(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$", re.M
)
_FINDINGS = re.compile(r"^\s*Findings\s*$", re.I | re.M)
_RECOMMENDATIONS = re.compile(r"^\s*Recommendations\s*$", re.I | re.M)


@dataclass(frozen=True)
class StrategyCandidate:
    strategy_id: str
    score: float
    rationale: str


def document_features(document: Document) -> dict:
    """Pure feature vector from a document model (no I/O)."""
    full = document.full_text or ""
    ratios: list[float] = []
    for page in document.pages:
        pw = page.width or 1.0
        for block in page.blocks:
            if block.block_type != "text":
                continue
            w = block.x1 - block.x0
            if pw > 0 and w > 0:
                ratios.append(w / pw)
    ratios.sort()
    median_block_width_ratio = ratios[len(ratios) // 2] if ratios else 1.0

    return {
        "reader": document.reader,
        "text_layer": document.text_layer.value,
        "words_per_page": document.words_per_page,
        "page_count": document.page_count,
        "total_words": document.total_words,
        "has_participant_heading": bool(_PARTICIPANT.search(full)),
        "has_conversation_transcript": bool(_TRANSCRIPT.search(full)),
        "has_speaker_labels": bool(_SPEAKER.search(full)),
        "has_references_heading": bool(_REF_HEADING.search(full)),
        "has_findings": bool(_FINDINGS.search(full)),
        "has_recommendations": bool(_RECOMMENDATIONS.search(full)),
        "median_block_width_ratio": median_block_width_ratio,
        "twocolumn_ish": median_block_width_ratio < 0.75,
    }


def _score_strategy(strategy_id: str, aspect: str, feats: dict) -> StrategyCandidate:
    score = 0.0
    reasons: list[str] = []

    layer = feats["text_layer"]
    if layer in ("absent", "sparse"):
        return StrategyCandidate(
            strategy_id,
            0.0,
            f"text_layer={layer} (no viable text-layer strategy)",
        )

    if strategy_id == "pub_dialogue.v1" and aspect == "body_chunks":
        score += 0.4
        reasons.append("body_chunks default")
        if feats["reader"] == "pdf":
            score += 0.2
            reasons.append("pdf reader")
        if feats["has_findings"] or feats["has_recommendations"]:
            score += 0.3
            reasons.append("findings/recommendations")
        if not feats["twocolumn_ish"]:
            score += 0.1
            reasons.append("single-column-ish")

    elif strategy_id == "pmlr_references.v1" and aspect == "references":
        if feats["has_references_heading"]:
            score += 0.8
            reasons.append("references heading")
        else:
            score += 0.05
            reasons.append("no references heading")
        if feats["twocolumn_ish"]:
            score += 0.15
            reasons.append("twocolumn-ish")
        if feats["reader"] == "pdf":
            score += 0.1
            reasons.append("pdf reader")

    elif strategy_id == "docx_chatbot.v1" and aspect == "dialogue_units":
        if feats["reader"] == "docx":
            score += 0.2
            reasons.append("docx reader")
        if feats["has_participant_heading"]:
            score += 0.5
            reasons.append("participant heading")
        if feats["has_conversation_transcript"]:
            score += 0.3
            reasons.append("conversation transcript")

    elif strategy_id == "docx_workshop.v1" and aspect == "dialogue_units":
        if feats["reader"] == "docx":
            score += 0.2
            reasons.append("docx reader")
        if feats["has_speaker_labels"] and not feats["has_participant_heading"]:
            score += 0.55
            reasons.append("speaker/facilitator labels")
        elif feats["has_speaker_labels"]:
            score += 0.25
            reasons.append("speaker labels (also has participant)")
        if not feats["has_conversation_transcript"]:
            score += 0.1
            reasons.append("no chatbot transcript markers")

    else:
        reasons.append("no heuristic match for aspect")

    return StrategyCandidate(
        strategy_id,
        round(score, 3),
        "; ".join(reasons) if reasons else "no signals",
    )


def rank_strategies(
    document: Document,
    *,
    aspect: str,
) -> list[StrategyCandidate]:
    """Return strategy candidates for *aspect*, highest score first."""
    ensure_builtin_strategies()
    feats = document_features(document)
    candidates = [
        _score_strategy(sid, aspect, feats) for sid in list_strategies(aspect=aspect)
    ]
    candidates.sort(key=lambda c: (-c.score, c.strategy_id))
    return candidates


def choose_strategy(
    document: Document,
    *,
    aspect: str,
    strategy: str = "auto",
) -> StrategyCandidate:
    """Pick a strategy: explicit id wins; ``auto`` takes the top ranked score.

    Raises ``UnknownStrategyError`` / ``ValueError`` when auto has no positive
    score (e.g. sparse text or no signals).
    """
    from .strategy import UnknownStrategyError, get_strategy

    ranked = rank_strategies(document, aspect=aspect)
    by_id = {c.strategy_id: c for c in ranked}

    if strategy != "auto":
        get_strategy(strategy)  # validate registration
        if strategy not in by_id:
            # Registered but not for this aspect — still allow override
            return StrategyCandidate(
                strategy,
                0.0,
                "manual override (not ranked for this aspect)",
            )
        chosen = by_id[strategy]
        return StrategyCandidate(
            chosen.strategy_id,
            chosen.score,
            f"manual override; ranked: {chosen.rationale}",
        )

    if not ranked:
        raise UnknownStrategyError(f"No strategies registered for aspect {aspect!r}")

    top = ranked[0]
    if top.score <= 0:
        raise UnknownStrategyError(
            f"strategy='auto' found no positive match for aspect {aspect!r} "
            f"(top was {top.strategy_id!r}: {top.rationale})"
        )
    # Ambiguous if top two are tied
    if len(ranked) > 1 and ranked[1].score == top.score and top.score > 0:
        raise UnknownStrategyError(
            f"strategy='auto' tie between {top.strategy_id!r} and "
            f"{ranked[1].strategy_id!r} (score={top.score}); choose explicitly"
        )
    return top
