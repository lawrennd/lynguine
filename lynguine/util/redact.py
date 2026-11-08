"""Shared RedactTerms contract and text apply (CIP-001A / REQ-0011).

Identification (collect) lives with producers; this module owns the term
shape, matching, and ``redact_text``. PDF apply is ``redact_pdf``.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Literal, TypedDict

MatchPolicy = Literal["whole_word", "literal"]
TermKind = Literal[
    "name",
    "email",
    "phone",
    "url",
    "linkedin",
    "scholar",
    "orcid",
    "researchgate",
    "github",
    "twitter",
    "website",
    "other",
]


class RedactTerm(TypedDict, total=False):
    """One string to remove or obscure.

    ``value`` is required. ``kind`` selects the text placeholder (and later
    PDF styling). ``match`` defaults to ``whole_word`` for names and
    ``literal`` for everything else.
    """

    value: str
    kind: TermKind | str
    match: MatchPolicy | str
    source: str


_PLACEHOLDER = {
    "name": "[name]",
    "email": "[email]",
    "phone": "[phone]",
    "url": "[url]",
    "linkedin": "[linkedin]",
    "scholar": "[scholar]",
    "orcid": "[orcid]",
    "researchgate": "[researchgate]",
    "github": "[github]",
    "twitter": "[twitter]",
    "website": "[website]",
    "other": "[redacted]",
}

_MAILTO_MD_RE = re.compile(
    r"\[([^\]]*)\]\(mailto:[^)]+\)", re.IGNORECASE
)


def _default_match(kind: str) -> MatchPolicy:
    return "whole_word" if kind == "name" else "literal"


def coerce_terms(terms: Iterable[Any] | None) -> list[RedactTerm]:
    """Normalise caller input into RedactTerm dicts (deduped, longest first).

    Deduplicate by case-folded ``value``. When the same value appears more
    than once, keep the first non-``other`` kind and prefer ``whole_word``
    when either side requests it (name safety).
    """
    by_value: dict[str, RedactTerm] = {}
    order: list[str] = []
    for raw in terms or []:
        if raw is None:
            continue
        if isinstance(raw, str):
            value = raw.strip()
            if not value:
                continue
            kind: str = "other"
            match: str = "literal"
            source = ""
            term: RedactTerm = {"value": value, "kind": kind, "match": match}
        elif isinstance(raw, dict):
            value = str(raw.get("value") or "").strip()
            if not value:
                continue
            kind = str(raw.get("kind") or "other").strip().lower() or "other"
            match = str(raw.get("match") or _default_match(kind)).strip().lower()
            if match not in {"whole_word", "literal"}:
                match = _default_match(kind)
            source = str(raw.get("source") or "").strip()
            term = {"value": value, "kind": kind, "match": match}
            if source:
                term["source"] = source
        else:
            continue
        key = term["value"].casefold()
        if key not in by_value:
            by_value[key] = term
            order.append(key)
            continue
        existing = by_value[key]
        if existing.get("kind") in (None, "", "other") and term.get("kind") not in (
            None,
            "",
            "other",
        ):
            existing["kind"] = term["kind"]
        if term.get("match") == "whole_word" or existing.get("kind") == "name":
            existing["match"] = "whole_word"
        if term.get("source") and not existing.get("source"):
            existing["source"] = term["source"]
    out = [by_value[k] for k in order]
    out.sort(key=lambda t: len(t["value"]), reverse=True)
    return out


def term_search_pattern(term: RedactTerm) -> re.Pattern[str]:
    """Compile a search pattern for one term (shared by text and PDF)."""
    value = term["value"]
    match = str(term.get("match") or _default_match(str(term.get("kind") or "other")))
    if match == "whole_word":
        parts = [re.escape(p) for p in value.split() if p]
        if not parts:
            return re.compile(r"(?!x)x")  # never matches
        body = r"\s+".join(parts)
        return re.compile(rf"\b{body}\b", re.IGNORECASE)
    return re.compile(re.escape(value), re.IGNORECASE)


def placeholder_for(term: RedactTerm) -> str:
    kind = str(term.get("kind") or "other").lower()
    return _PLACEHOLDER.get(kind, _PLACEHOLDER["other"])


def redact_text(text: Any, terms: Iterable[Any] | None = None) -> str:
    """Apply RedactTerms to plain text (no PDF).

    Also collapses leftover ``[label](mailto:…)`` links to the label after
    email placeholders are applied.
    """
    if text is None:
        return ""
    out = str(text)
    if not out:
        return ""
    for term in coerce_terms(terms):
        out = term_search_pattern(term).sub(placeholder_for(term), out)
    out = _MAILTO_MD_RE.sub(r"\1", out)
    return out
