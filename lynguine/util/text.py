from __future__ import annotations

import re
from typing import Any

from lynguine.util.misc import remove_nan
from lynguine.util.redact import RedactTerm, coerce_terms, redact_text

_TABLE_CHROME_LINE = re.compile(r"^[\s|:\-]+$")
_EMAIL_RE = re.compile(
    r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b"
)
# Prefer numbers that look like phone contacts (leading +, separators),
# not bare years like 2027.
_PHONE_RE = re.compile(
    r"(?<!\d)(?:"
    r"\+\d{1,3}(?:[\s\-.]?\d){6,14}"  # +91 9971790675 / +1-555-123-4567
    r"|"
    r"\(\d{2,5}\)[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}"  # (01223) 123456
    r"|"
    r"\b\d{3}[\s\-.]\d{3}[\s\-.]\d{4}\b"  # 555-123-4567
    r"|"
    r"\b\d{4,5}[\s\-]\d{5,6}\b"  # 99717 90675
    r")"
    r"(?:\s*(?:ext|x|extension)\.?\s*\d+)?"
    r"(?!\d)"
)
_MAILTO_MD_RE = re.compile(
    r"\[([^\]]*)\]\(mailto:[^)]+\)", re.IGNORECASE
)
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# Profile / personal homepage URLs (raw or inside markdown links).
_PROFILE_URL_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)?"
    r"(?:"
    r"linkedin\.com/in/[^\s\]<>\"']+"
    r"|scholar\.google\.[a-z.]+/citations\?[^\s\]<>\"']+"
    r"|orcid\.org/[0-9Xx\-]+"
    r"|researchgate\.net/(?:profile|scientific-contributions)/[^\s\]<>\"']+"
    # Profile or repo — both expose the username.
    r"|github\.com/[A-Za-z0-9][A-Za-z0-9_.-]+(?:/[^\s\]<>\"']*)?"
    r"|[A-Za-z0-9.-]+\.github\.io(?:/[^\s\]<>\"']*)?"
    r"|sites\.google\.com/(?:view|site)/[^\s\]<>\"']+"
    # Twitter / X profile (not status URLs only — /username is enough).
    r"|(?:twitter|x)\.com/[A-Za-z0-9_]{1,15}(?:/[^\s\]<>\"']*)?"
    r")"
)
_LABELED_WEBSITE_RE = re.compile(
    r"(?i)\b(?:personal\s+)?(?:web\s*site|homepage|home\s*page|portfolio|"
    r"webpage|web\s*page)\s*[:\-]\s*\S+"
)
_FROM_NAME_RE = re.compile(
    r'^\s*(?:"([^"]+)"|([^<]*?))\s*(?:<[^>]+>)?\s*$'
)
# Prefix case-insensitive; the name itself must stay Capitalized so
# "I am at an early stage" is not treated as a self-introduction.
_MY_NAME_IS_RE = re.compile(
    r"\b((?i:my name is))\s+[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3}"
)
# "I'm Ali Ghasemzadeh, a final-year…" / "I am Samarth Kumar and…"
# Apostrophe class covers ASCII and typographic forms (U+2019 / U+2018);
# mail clients often emit I’m rather than I'm.
_IM_APOSTROPHE = r"['\u2019\u2018]"
_IM_NAME_RE = re.compile(
    rf"\b((?i:i{_IM_APOSTROPHE}m|i am))\s+"
    r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3})"
    r"(?=,|\s+a\b|\s+an\b|\s+and\b|\.|$)"
)
# Short / function words must never be used as substring name redactions
# (e.g. "at" inside "Mathematics" / "candidates" / "that").
_NAME_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "am",
        "at",
        "as",
        "be",
        "by",
        "do",
        "for",
        "from",
        "in",
        "is",
        "it",
        "me",
        "my",
        "no",
        "of",
        "on",
        "or",
        "so",
        "the",
        "to",
        "we",
        "and",
        "dr",
        "mr",
        "mrs",
        "ms",
        "prof",
        "professor",
    }
)
_MIN_NAME_TOKEN_LEN = 3


def _is_table_chrome(text: str) -> bool:
    """True when a paragraph is mostly markdown table scaffolding."""
    lines = [ln for ln in str(text).splitlines() if ln.strip()]
    if not lines:
        return True
    chrome = sum(1 for ln in lines if _TABLE_CHROME_LINE.match(ln))
    return chrome / len(lines) >= 0.6


def _usable_person_name(name: str) -> bool:
    """True when *name* is safe to redact as a whole-word person name."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip(" ,;"))
    if not cleaned or "@" in cleaned:
        return False
    lower = cleaned.lower()
    if lower in _NAME_STOPWORDS or lower in {
        "noreply",
        "no-reply",
        "mailer-daemon",
    }:
        return False
    tokens = [t for t in re.split(r"[\s.]+", cleaned) if t]
    if not tokens:
        return False
    # Reject bare-email local parts that are not human names.
    if any(any(ch.isdigit() for ch in t) for t in tokens):
        return False
    if all(len(t) < _MIN_NAME_TOKEN_LEN or t.lower() in _NAME_STOPWORDS for t in tokens):
        return False
    return True


def _name_variants(name: str) -> list[str]:
    """Full name plus safe individual tokens (never stopwords / short crumbs)."""
    cleaned = re.sub(r"\s+", " ", name.strip(" ,;"))
    if not _usable_person_name(cleaned):
        return []
    out = [cleaned]
    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            swapped = f"{parts[1]} {parts[0]}"
            if _usable_person_name(swapped):
                out.append(swapped)
            cleaned = swapped
    for token in re.split(r"[\s.]+", cleaned):
        token = token.strip(" ,;")
        if (
            len(token) >= _MIN_NAME_TOKEN_LEN
            and token.lower() not in _NAME_STOPWORDS
            and not any(ch.isdigit() for ch in token)
        ):
            out.append(token)
    # De-dupe, longest first for replacement order.
    return list(dict.fromkeys(out))


def names_from_sender(sender: Any) -> list[str]:
    """Extract display-name tokens from a From header for body redaction."""
    if sender is None:
        return []
    raw = str(sender).strip()
    if not raw or raw.lower() in {"nan", "nat", "none", "<na>"}:
        return []
    match = _FROM_NAME_RE.match(raw)
    name = ""
    if match:
        name = (match.group(1) or match.group(2) or "").strip()
    if not name:
        # Bare email local-parts are usually not safe display names
        # (e.g. "at@…" would otherwise redact every word "at").
        return []
    return _name_variants(name)


def names_from_body(text: Any) -> list[str]:
    """Pull self-identified names from intro lines for cross-paragraph redact."""
    if text is None:
        return []
    raw = str(text)
    found: list[str] = []
    for match in _MY_NAME_IS_RE.finditer(raw):
        span = match.group(0)
        name = re.sub(r"^(?i:my name is)\s+", "", span).strip()
        found.extend(_name_variants(name))
    for match in _IM_NAME_RE.finditer(raw):
        found.extend(_name_variants((match.group(2) or "").strip()))
    return list(dict.fromkeys(found))


def _profile_kind(url: str) -> str:
    lower = (url or "").lower()
    if "linkedin.com" in lower:
        return "linkedin"
    if "scholar.google" in lower:
        return "scholar"
    if "orcid.org" in lower:
        return "orcid"
    if "researchgate.net" in lower:
        return "researchgate"
    if "github.com" in lower or "github.io" in lower:
        return "github"
    if "twitter.com" in lower or "x.com/" in lower or lower.startswith("x.com"):
        return "twitter"
    if "sites.google.com" in lower:
        return "website"
    return "website"


def collect_contact_pii_terms(
    text: Any = None,
    *,
    names: list[str] | None = None,
    sender: Any = None,
) -> list[RedactTerm]:
    """Identify contact-PII RedactTerms without applying them (CIP-001A).

    Sources: emails, phones, profile/personal URLs, labeled websites, and
    person-name variants from ``names``, ``sender``, and intro lines in
    ``text``.
    """
    raw = "" if text is None else str(text)
    found: list[RedactTerm] = []

    for match in _EMAIL_RE.finditer(raw):
        found.append(
            {
                "value": match.group(0),
                "kind": "email",
                "match": "literal",
                "source": "contact_pii",
            }
        )
    for match in _PHONE_RE.finditer(raw):
        found.append(
            {
                "value": match.group(0),
                "kind": "phone",
                "match": "literal",
                "source": "contact_pii",
            }
        )
    for match in _MD_LINK_RE.finditer(raw):
        url = match.group(2) or ""
        if "mailto:" in url.lower():
            continue
        if _PROFILE_URL_RE.search(url):
            found.append(
                {
                    "value": url,
                    "kind": _profile_kind(url),
                    "match": "literal",
                    "source": "contact_pii",
                }
            )
    for match in _PROFILE_URL_RE.finditer(raw):
        url = match.group(0)
        found.append(
            {
                "value": url,
                "kind": _profile_kind(url),
                "match": "literal",
                "source": "contact_pii",
            }
        )
    for match in _LABELED_WEBSITE_RE.finditer(raw):
        found.append(
            {
                "value": match.group(0),
                "kind": "website",
                "match": "literal",
                "source": "contact_pii",
            }
        )

    all_names: list[str] = []
    for name in list(names or []):
        all_names.extend(_name_variants(name))
    if sender is not None:
        all_names.extend(names_from_sender(sender))
    all_names.extend(names_from_body(raw))
    for name in dict.fromkeys(all_names):
        found.append(
            {
                "value": name,
                "kind": "name",
                "match": "whole_word",
                "source": "contact_pii",
            }
        )
    return coerce_terms(found)


def redact_contact_pii(text: Any, *, names: list[str] | None = None) -> str:
    """Remove emails, phones, profile URLs, and known personal names.

    Thin collect+apply wrapper for callers that have not migrated to
    ``collect_contact_pii_terms`` + ``redact_text`` (CIP-001A).
    """
    if text is None:
        return ""
    out = str(text)
    if not out:
        return ""
    # Strip mailto markdown labels before collect so emails in hrefs remain.
    prep = _MAILTO_MD_RE.sub(r"\1", out)
    terms = collect_contact_pii_terms(prep, names=names)
    out = redact_text(prep, terms)
    # Residual intro lines if a Capitalized phrase slipped past name collect.
    out = _MY_NAME_IS_RE.sub(r"\1 [name]", out)
    out = _IM_NAME_RE.sub(r"\1 [name]", out)
    return out


def render_liquid(compute, template, **kwargs):
    """
    Wrapper to liquid renderer.

    :param template: The template to be rendered.
    :type template: str
    :return: The rendered template.
    :rtype: str
    """
    return compute._liquid_env.from_string(template).render(**remove_nan(kwargs))


def split_paragraph_units(
    text: Any = None,
    *,
    message_id: Any = None,
    mail_key: Any = None,
    candidate: Any = None,
    only_candidates: Any = True,
    min_chars: int = 40,
    max_units: int = 12,
    subject: Any = None,
    sender: Any = None,
    date: Any = None,
    redact_pii: Any = True,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Split body text into paragraph dicts for CIP-0014 ``explode``.

    Returns mappings with ``unit_id``, ``unit_index``, ``text`` (raw),
    ``extract_text`` (PII-redacted), plus listing ``title`` / ``description``
    from subject and sender so the UI does not show ``unit_id``.

    When ``only_candidates`` is true, only messages with an explicit truthy
    ``candidate`` are split — unscored (None) and rejected (False) rows
    yield no units.
    """

    def _blank(val: Any) -> bool:
        if val is None:
            return True
        try:
            import math

            if isinstance(val, float) and math.isnan(val):
                return True
        except (TypeError, ValueError):
            pass
        text_v = str(val).strip()
        return not text_v or text_v.lower() in {"nan", "nat", "none", "<na>"}

    def _is_candidate(val: Any) -> bool:
        if val is True or val == 1:
            return True
        if isinstance(val, str) and val.strip().lower() in {"true", "1", "yes"}:
            return True
        return False

    if only_candidates in (True, "true", "True", 1, "1"):
        if not _is_candidate(candidate):
            return []

    raw = "" if _blank(text) else str(text)
    min_n = int(min_chars) if min_chars is not None else 40
    max_n = int(max_units) if max_units is not None else 12
    do_redact = redact_pii in (True, "true", "True", 1, "1")
    parts = re.split(r"\n\s*\n+", raw.strip())
    paragraphs = [
        p.strip()
        for p in parts
        if len(p.strip()) >= min_n and not _is_table_chrome(p)
    ]
    if not paragraphs and raw.strip() and not _is_table_chrome(raw):
        paragraphs = [raw.strip()]
    paragraphs = paragraphs[:max_n]

    # Prefer mail_key so the same Message-ID in two candidacy slices
    # (e.g. phd + boards) does not collide on unit_id.
    key = "" if _blank(mail_key) else str(mail_key)
    if not key:
        key = "" if _blank(message_id) else str(message_id)

    subj = "" if _blank(subject) else str(subject).strip()
    from_hdr = "" if _blank(sender) else str(sender).strip()
    # Accept legacy row_args alias ``from`` via kwargs.
    if not from_hdr and not _blank(kwargs.get("from")):
        from_hdr = str(kwargs.get("from")).strip()
    date_s = "" if _blank(date) else str(date).strip()

    # Collect once per message; apply per paragraph (CIP-001A).
    terms: list[RedactTerm] = []
    if do_redact:
        terms = collect_contact_pii_terms(raw, sender=from_hdr)

    units: list[dict[str, Any]] = []
    for i, para in enumerate(paragraphs):
        if do_redact:
            prep = _MAILTO_MD_RE.sub(r"\1", para)
            extract = redact_text(prep, terms)
            extract = _MY_NAME_IS_RE.sub(r"\1 [name]", extract)
            extract = _IM_NAME_RE.sub(r"\1 [name]", extract)
        else:
            extract = para
        title = subj or key or f"unit {i}"
        if len(paragraphs) > 1:
            title = f"{title} · ¶{i + 1}"
        # Listing shows title + date chip + description (sender).
        units.append(
            {
                "unit_id": f"{key}::{i}",
                "unit_index": i,
                "text": para,
                "extract_text": extract,
                "title": title,
                "description": from_hdr,
                "date": date_s,
            }
        )
    return units
