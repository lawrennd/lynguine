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
    "CCS Concepts",
    "Additional Key Words",
    "ACM Reference Format",
)

_AFFILIATION_HINT = re.compile(
    r"(?i)\b("
    r"university|université|universität|college|institute|department|"
    r"laboratory|lab\b|school of|faculty of|centre for|center for|"
    r"affiliation|correspondence|united kingdom|united states|\busa\b|"
    r"cambridge|oxford|princeton|harvard|stanford|\bmit\b|"
    r"technion|blavatnik|google research|max planck|"
    r"microsoft research|nyu\b|turing institute"
    r")\b"
)
_INSTITUTIONAL_ADDRESS = re.compile(
    r"(?i)(\bUSA\.|\bUK\.|\bIsrael\.|\bGermany\.|\bSpain\.|"
    r"School of |Faculty of |Department of |Institute of )"
)
_TITLE_FUNCTION_WORDS = re.compile(
    r"(?i)\b(the|a|an|of|for|from|with|that|than|into|onto|via|on|in|to)\b"
)

# Publisher running titles / headers and bibliographic front matter.
_RUNNING_HEADER_LINE = re.compile(
    r"(?i)^\s*("
    r"arxiv:|doi:|https?://|www\.|"
    r"proceedings of|copyright|©|"
    r"preprint|under review|"
    r"articles?|article|research article|"
    r"ieee transactions?\b|acm transactions?\b|"
    r"nature machine intelligence\b|nature neuroscience\b|nature communications\b|"
    r"plos one\b|open access\b|citation:|"
    r"vol\.?\s*\d|volume\s+\d|"
    r"journal title here|"
    r"published as a conference paper|"
    r"e-?mail:|✉|"
    r"editor:|received:|accepted:|published:|peer review|"
    r"contents lists available|sciencedirect|advance access publication|"
    r"\d+\s*/\s*\d+"  # "1 / 19" page number header
    r")"
)
# Journal + volume/year/pages style: "Neurocomputing 275 (2018) 2251–2263 …"
_JOURNAL_BIBLIO_LINE = re.compile(
    r"(?i)^(?:"
    r"[A-Z][^()]{2,80}\(\d{4}\)\s*[\d:\-–—, ]{2,}"  # Name … (year) pages
    r"|[A-Z][^,]{5,100},\s*VOL\.?\s*\d+"  # IEEE …, VOL. n
    r"|.+\bDOI\s*:?\s*10\.\d+"
    r"|skip to\b.+"
    r"|math(?:ematics)? and statistics online"
    r")"
)
# Leading publisher metadata glued before a real title on the same line.
_LEADING_PUBLISHER_FM = re.compile(
    r"(?i)^(?:"
    r"(?:ieee|acm)\b[^,]{0,80},\s*VOL\.?\s*\d+(?:\s*,\s*NO\.?\s*\d+)?(?:\s*,\s*[A-Z]+\s+\d{4})?\s+"
    r"|(?:[A-Z][^()]{2,60}\(\d{4}\)\s*[\d:\-–—, ]{2,60})\s+"
    r")"
)
_WEB_SHELL_LINE = re.compile(
    r"(?i)^(skip to\b|accept (all )?cookies|sign in\b|subscribe\b)"
)
# BibTeX-ish parses from publisher running titles / bibliographic headers.
_PARSE_IEEE_VOL = re.compile(
    r"(?i)^(?P<journal>(?:ieee|acm)\b[^,]{2,120}?)\s*,\s*"
    r"VOL\.?\s*(?P<volume>\d+)"
    r"(?:\s*,\s*NO\.?\s*(?P<number>\d+))?"
    r"(?:\s*,\s*(?P<month>[A-Z]{3,9})\.?\s+(?P<year>\d{4}))?"
)
_PARSE_JOURNAL_YEAR_PAGES = re.compile(
    r"(?i)^(?P<journal>[A-Z][^()]{2,80}?)\s+"
    r"(?P<volume>\d+)\s+"
    r"\((?P<year>\d{4})\)\s*"
    r"(?P<pages>[\d]+(?:\s*[-–—]\s*[\d]+)?)"
)
_PARSE_DOI = re.compile(
    r"(?i)(?:doi\s*:?\s*|https?://(?:dx\.)?doi\.org/)"
    r"(?P<doi>10\.\d{4,9}/[^\s]+)"
)
_CITATION_LINE = re.compile(
    r"^[A-Z][A-Za-z'’\-]+(?:\s+[A-Z]\.?)?(?:\s*,\s*[A-Z][A-Za-z'’\-]+(?:\s+[A-Z]\.?)?)+\s*\(\d{4}\)\s*$"
)
_NAME_PART = re.compile(
    r"^(?:"
    r"[A-Z]\.|"  # initial "A."
    r"[A-Z][A-Za-z'’\-]+"
    r")"
    r"(?:(?:\s+[A-Z]\.)?(?:\s+[A-Z][A-Za-z'’\-]+)){0,3}$"
)

_PAGE_NUM = re.compile(r"^\d{1,4}$")
_EQUAL_CONTRIB = re.compile(
    r"(?i)(?:\d+)?\s*these authors contributed equally:\s*(.+?)(?:\.?\s*(?:✉|e-?mail:)|$)"
)
_AUTHOR_SPLIT = re.compile(
    r"\s+and\s+|\s*&\s*|,",
    re.IGNORECASE,
)
# ACM PACM / TOCHI style: "GEORGI KARADZHOV, University of Cambridge, United Kingdom"
_ACM_AUTHOR = re.compile(
    r"^([A-Z][A-Z .'\-]{2,}),\s+(.+)$"
)
_NUMBERED_AFFIL = re.compile(r"^\d+\s*[A-Za-z]")
_PERSON_NAME = re.compile(
    r"^(?:"
    r"[A-Z]\.|"
    r"[A-Z][A-Za-z'’\-]+"
    r")"
    r"(?:(?:\s+[A-Z]\.)?(?:\s+[A-Z][A-Za-z'’\-]+))+$"
)


def _joined_front_pages(document: Document, max_pages: int) -> str:
    pages = document.pages[: max(1, max_pages)]
    return "\n".join(page.text for page in pages)


def _stop_pattern(stop_headings: list[str]) -> re.Pattern[str]:
    escaped = [re.escape(h.strip()) for h in stop_headings if h and str(h).strip()]
    if not escaped:
        escaped = [re.escape(h) for h in _DEFAULT_STOP]
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
        line = (
            raw.replace("\u2009", " ")
            .replace("\u200a", " ")
            .replace("\u2002", " ")
            .replace("\u00a0", " ")
        )
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def _looks_like_journal_name_only(line: str) -> bool:
    """True for short journal/venue names mistaken for titles after a strip."""
    text = str(line).strip()
    words = text.split()
    if not words or len(words) > 8:
        return False
    # Venue phrase ending in a series noun, or a known short venue name.
    if re.search(
        r"(?i)\b(journal|transactions|proceedings|letters|magazine)\s*$",
        text,
    ):
        return True
    if re.fullmatch(
        r"(?i)("
        r"neurocomputing|sciencedirect|nature(?:\s+\w+){0,3}|"
        r"science(?:\s+\w+){0,2}|plos\s+one|"
        r"applied soft computing(?:\s+journal)?"
        r")",
        text,
    ):
        return True
    return False


def is_publisher_front_matter(line: str) -> bool:
    """True when *line* is publisher metadata, not a paper title.

    Covers running titles/headers, journal+volume/biblio lines, DOI-only
    lines, and publisher web-shell navigation. Absence of such lines is
    fine — this is a filter, not a requirement.
    """
    if not line or not str(line).strip():
        return False
    text = str(line).strip()
    if _PAGE_NUM.fullmatch(text):
        return True
    if _WEB_SHELL_LINE.search(text):
        return True
    if _RUNNING_HEADER_LINE.search(text):
        return True
    if _JOURNAL_BIBLIO_LINE.match(text):
        return True
    if _CITATION_LINE.match(text):
        return True
    # Journal running header with pipe separators / page ranges
    if "|" in text and re.search(r"(?i)volume|vol\.|pages?\s+\d", text):
        return True
    # Lowercase journal name repeats ("nature machine intelligence")
    if (
        text.islower()
        and len(text.split()) <= 4
        and not text.endswith(".")
        and re.search(
            r"(?i)\b(nature|science|ieee|acm|proceedings|transactions|journal)\b",
            text,
        )
    ):
        return True
    if _looks_like_journal_name_only(text):
        return True
    # Lone superscript crumbs / page markers
    if re.fullmatch(r"[\d,\s\*†‡§¶✉]+", text):
        return True
    # Short generic section labels that are not titles
    if re.fullmatch(r"(?i)journal|report|paper|original article|methodology", text):
        return True
    return False


def strip_leading_publisher_front_matter(line: str) -> str | None:
    """Return title remainder after leading publisher metadata, or None if none.

    Whole-line publisher front matter → ``None``.
    No leading metadata → original line.
    Header glued before title → remainder only.
    """
    if not line or not str(line).strip():
        return None
    text = str(line).strip()
    if is_publisher_front_matter(text):
        # Glued case: metadata prefix then a longer title remnant
        m = _LEADING_PUBLISHER_FM.match(text)
        if m:
            rest = text[m.end() :].strip(" -–—|,")
            if (
                rest
                and not is_publisher_front_matter(rest)
                and not _looks_like_journal_name_only(rest)
                and len(rest.split()) >= 3
            ):
                return rest
        return None
    # Leading-header prefixes always classify as publisher FM above, so a
    # non-FM line is returned unchanged.
    return text


def _empty_publisher_fields() -> dict[str, Any]:
    return {
        "journal": None,
        "volume": None,
        "number": None,
        "pages": None,
        "year": None,
        "doi": None,
        "publisher_front_matter_lines": [],
    }


def _set_first(out: dict[str, Any], key: str, value: str | None) -> None:
    """Keep the first confident value; do not overwrite."""
    if value is None:
        return
    cleaned = str(value).strip().rstrip(".,;")
    if not cleaned:
        return
    if out.get(key):
        return
    out[key] = cleaned


def _parse_one_publisher_line(line: str, out: dict[str, Any]) -> None:
    """Best-effort BibTeX-ish fill from a single tagged publisher line."""
    text = str(line).strip()
    if not text or _WEB_SHELL_LINE.search(text):
        return
    if _PAGE_NUM.fullmatch(text):
        return

    doi_m = _PARSE_DOI.search(text)
    if doi_m:
        doi = doi_m.group("doi").rstrip(").,]")
        _set_first(out, "doi", doi)

    ieee = _PARSE_IEEE_VOL.match(text)
    if ieee:
        _set_first(out, "journal", ieee.group("journal"))
        _set_first(out, "volume", ieee.group("volume"))
        _set_first(out, "number", ieee.group("number"))
        _set_first(out, "year", ieee.group("year"))
        return

    # Truncate glued title before year-pages parse when possible
    parse_text = text
    lead = _LEADING_PUBLISHER_FM.match(text)
    if lead:
        parse_text = text[: lead.end()].strip()

    jyp = _PARSE_JOURNAL_YEAR_PAGES.match(parse_text) or _PARSE_JOURNAL_YEAR_PAGES.match(
        text
    )
    if jyp:
        journal = jyp.group("journal").strip()
        # Drop trailing repeated venue token ("Neurocomputing 275 … Neurocomputing")
        words = journal.split()
        if len(words) >= 2 and words[-1].casefold() == words[0].casefold():
            journal = " ".join(words[:-1]).strip()
        # "Applied Soft Computing Journal 91 … Applied Soft Computing Journal"
        # may leave "Applied Soft Computing Journal 91" if volume captured — ok
        # Strip a trailing volume digit accidentally left in journal name
        journal = re.sub(r"\s+\d+$", "", journal).strip()
        _set_first(out, "journal", journal)
        _set_first(out, "volume", jyp.group("volume"))
        _set_first(out, "year", jyp.group("year"))
        pages = jyp.group("pages")
        if pages:
            pages = re.sub(r"\s*[-–—]\s*", "--", pages)
            _set_first(out, "pages", pages)
        return

    # Short journal-name-only running header
    if _looks_like_journal_name_only(text) or (
        text.islower()
        and re.search(
            r"(?i)\b(nature|science|ieee|acm|proceedings|transactions|journal)\b",
            text,
        )
    ):
        _set_first(out, "journal", text)


def parse_publisher_front_matter(lines: list[str]) -> dict[str, Any]:
    """Parse BibTeX-ish fields from tagged publisher front-matter lines.

    Returns ``journal``, ``volume``, ``number``, ``pages``, ``year``, ``doi``,
    and ``publisher_front_matter_lines`` (audit copy of *lines*, deduped).
    First confident value wins per field. Web-shell-only lines stay in the
    audit list but do not invent bibliographic fields.
    """
    out = _empty_publisher_fields()
    seen: set[str] = set()
    audit: list[str] = []
    for raw in lines:
        text = str(raw).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        audit.append(text)
        _parse_one_publisher_line(text, out)
    out["publisher_front_matter_lines"] = audit
    return out


def _is_running_header_or_noise(line: str) -> bool:
    """Backward-compatible alias for :func:`is_publisher_front_matter`."""
    return is_publisher_front_matter(line)

def _looks_like_affiliation_only(line: str) -> bool:
    """True when the line is affiliation text without a leading personal name."""
    if EMAIL_RE.search(line) and not re.search(
        r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", line.split("@")[0]
    ):
        return True
    lowered = line.lower()
    if lowered.startswith("e-mail") or lowered.startswith("email"):
        return True
    # Numbered affiliation markers — including short orgs ("1MIT", "6Microsoft Research")
    if _NUMBERED_AFFIL.match(line):
        if "these authors contributed equally" in lowered:
            return False
        if _AFFILIATION_HINT.search(line) or _INSTITUTIONAL_ADDRESS.search(line):
            return True
        # Short numbered line is almost always an affiliation key
        if len(line.split()) <= 5:
            return True
    # Wrapped institutional address without leading number
    if _INSTITUTIONAL_ADDRESS.search(line) and not _PERSON_NAME.match(
        line.split(",")[0].strip()
    ):
        if not re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+,", line):
            return True
    if _AFFILIATION_HINT.search(line) and not _ACM_AUTHOR.match(line):
        before = line
        m = _AFFILIATION_HINT.search(line)
        if m:
            before = line[: m.start()].strip(" ,;")
        tokens = [t for t in before.split() if t[:1].isalpha()]
        if len(tokens) <= 1:
            return True
        # Author list: "Ramon Viñas 1, Chaitanya..." — personal names before hint
        if (
            sum(1 for t in tokens if _NAME_PART.match(t) or t[:1].isupper()) >= 2
            and "," in before
            and not _INSTITUTIONAL_ADDRESS.search(before)
        ):
            return False
        if _PERSON_NAME.match(before):
            return False
        # "Industrial Engineering and Management, Technion..."
        if _INSTITUTIONAL_ADDRESS.search(line) or re.search(
            r"(?i)\b(school|faculty|department|institute|university)\b", before
        ):
            return True
        return True
    return False


def _acm_author_name(line: str) -> str | None:
    m = _ACM_AUTHOR.match(line)
    if not m:
        return None
    name = m.group(1).strip()
    rest = m.group(2)
    if not _AFFILIATION_HINT.search(rest):
        return None
    # Title-case shouted ACM names
    if name.isupper() and len(name) > 3:
        name = name.title()
    return name


def _looks_like_prose(line: str) -> bool:
    """Body/abstract sentences — not title or author metadata."""
    words = line.split()
    if len(words) >= 18:
        return True
    if line[:1].islower() and len(words) >= 6:
        return True
    if line.endswith(".") and len(words) >= 10 and "," in line:
        return True
    # Sentence starters common in abstracts
    if re.match(
        r"(?i)^(we |this (paper|work|article)|group |in this |here we )",
        line,
    ):
        return True
    return False


def _name_like_part(part: str) -> bool:
    """True if a comma/and segment looks like a personal name."""
    cleaned = re.sub(r"[∗\d\*†‡§¶]+", "", part).strip(" ,;")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned or not cleaned[0].isupper():
        return False
    if _TITLE_FUNCTION_WORDS.search(cleaned):
        return False
    # Reject common non-name title vocabulary
    if re.search(
        r"(?i)\b(paper|title|study|network|dataset|learning|model|framework|"
        r"approach|analysis|system|method|proceedings|synthetic)\b",
        cleaned,
    ):
        return False
    tokens = cleaned.split()
    # Personal names are typically 1–3 tokens (optionally with initials)
    if not tokens or len(tokens) > 3:
        return False
    for tok in tokens:
        if re.fullmatch(r"[A-Z]\.", tok):
            continue
        core = tok.replace("'", "").replace("’", "").replace("-", "")
        # Unicode-aware: Viñas, Liò, etc.
        if not core or not core[0].isupper() or not all(c.isalpha() for c in core):
            return False
    return True


def _looks_like_author_line(line: str) -> bool:
    if _is_running_header_or_noise(line):
        return False
    if _acm_author_name(line):
        return True
    if _looks_like_affiliation_only(line):
        return False
    if _looks_like_prose(line):
        return False
    letters = sum(c.isalpha() for c in line)
    if letters < 2:
        return False
    words = line.split()
    if len(words) > 16:
        return False
    # Titles often contain "and" / "with" — require name-like parts.
    # Leading "& …" / "and …" continuations are handled here via the same split.
    if re.search(r"(?i)\band\b|&|,", line):
        parts = [
            p.strip()
            for p in re.split(r",|\band\b|&", line)
            if p.strip() and not re.fullmatch(r"\d+", p.strip())
        ]
        if not parts:
            return False
        nameish = sum(1 for p in parts if _name_like_part(p))
        return nameish / len(parts) >= 0.5
    # Single short personal name (not a title-cased phrase)
    if 2 <= len(words) <= 4 and _name_like_part(line):
        return True
    return False


def _looks_like_title_line(line: str) -> bool:
    if _is_running_header_or_noise(line):
        return False
    if _acm_author_name(line):
        return False
    if _looks_like_affiliation_only(line):
        return False
    if EMAIL_RE.search(line):
        return False
    if _INSTITUTIONAL_ADDRESS.search(line):
        return False
    if _looks_like_prose(line) and len(line.split()) > 20:
        return False
    letters = sum(c.isalpha() for c in line)
    if letters < 4:
        return False
    return True


def _reject_publisher_title(title: str | None) -> str | None:
    """Drop a candidate title that is still publisher front matter."""
    if title and is_publisher_front_matter(title):
        return None
    return title


def split_author_names(raw: str) -> list[str]:
    """Split a raw author string into individual names."""
    if not raw or not str(raw).strip():
        return []
    text = str(raw).strip()
    acm = _acm_author_name(text)
    if acm:
        return [acm]
    # Drop footnote / affiliation markers: "Ada Lovelace1", "Collins∗1"
    text = re.sub(r"[∗†‡§¶]+", "", text)
    text = re.sub(r"(?<=[A-Za-z])\d+(?=,|\s+and\s+|&|$)", "", text)
    # Collapse "Name 1, Name 2" superscripts left as separate tokens
    text = re.sub(r"\s+\d{1,2}(?=,|\s|&|$)", "", text)
    # Drop leading orphaned affiliation digits: "1, Chaitanya..."
    text = re.sub(r"^\d+\s*,\s*", "", text)
    parts = _AUTHOR_SPLIT.split(text)
    names: list[str] = []
    for part in parts:
        name = part.strip(" ,;.")
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            continue
        if name.casefold() in {"and", "&"}:
            continue
        if re.fullmatch(r"[\d\*†‡§¶]+", name):
            continue
        if _looks_like_affiliation_only(name):
            continue
        if _looks_like_prose(name):
            continue
        # Drop fragments that are not name-like
        tokens = name.split()
        if len(tokens) > 5:
            continue
        if name[:1].islower():
            continue
        names.append(name)
    return names


def _dedupe(names: list[str]) -> list[str]:
    seen: set[str] = set()
    uniq: list[str] = []
    for name in names:
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(name)
    return uniq


def _authors_from_equal_contrib(region: str) -> list[str]:
    # Search line-wise then collapsed — Nature wraps the clause
    collapsed = re.sub(r"\s+", " ", region)
    m = _EQUAL_CONTRIB.search(collapsed)
    if not m:
        return []
    return _dedupe(split_author_names(m.group(1)))


def _take_title_wrap(lines: list[str], start: int) -> tuple[list[str], int]:
    """Return title parts and index after the title block."""
    title_parts: list[str] = []
    i = start
    if i >= len(lines):
        return title_parts, i
    line = lines[i]
    if not _looks_like_title_line(line) or _looks_like_prose(line):
        return title_parts, i
    # Do not take a clear author list as title
    if _looks_like_author_line(line) and (
        "," in line or re.search(r"(?i)\band\b|&", line) or _acm_author_name(line)
    ):
        return title_parts, i
    # Lone short personal name is an author, not a title
    tokens = [t for t in line.split() if t[:1].isalpha()]
    if 2 <= len(tokens) <= 3 and _PERSON_NAME.match(line) and not _TITLE_FUNCTION_WORDS.search(line):
        return title_parts, i
    title_parts.append(line)
    i += 1
    # Optional wrap: next short non-author / non-name line
    if i < len(lines):
        nxt = lines[i]
        if (
            _looks_like_title_line(nxt)
            and not _looks_like_prose(nxt)
            and not _acm_author_name(nxt)
            and not _looks_like_author_line(nxt)
            and not (
                2 <= len(nxt.split()) <= 3
                and _PERSON_NAME.match(nxt)
                and not _TITLE_FUNCTION_WORDS.search(nxt)
            )
            and not re.search(r"(?i)\band\b|&", nxt)
            and "," not in nxt
            and len(nxt.split()) <= 12
        ):
            title_parts.append(nxt)
            i += 1
    return title_parts, i


def extract_frontmatter(document: Document, params: dict[str, Any]) -> dict[str, Any]:
    """Return structured title/authors/publisher fields for *document*."""
    params = params or {}
    max_pages = int(params.get("max_pages") or 1)
    stop_headings = list(params.get("stop_headings") or _DEFAULT_STOP)
    text = _joined_front_pages(document, max_pages)
    region = _front_region(text, stop_headings)
    raw_lines = _nonempty_lines(region)
    emails = EMAIL_RE.findall(region)

    # Tag → extract BibTeX-ish fields → exclude from title (CIP-0013).
    tagged_lines: list[str] = []
    lines: list[str] = []
    for ln in raw_lines:
        if is_publisher_front_matter(ln) or _LEADING_PUBLISHER_FM.match(ln):
            tagged_lines.append(ln)
        cleaned = strip_leading_publisher_front_matter(ln)
        if cleaned is None:
            continue
        lines.append(cleaned)
    publisher_fields = parse_publisher_front_matter(tagged_lines)

    title: str | None = None
    author_lines: list[str] = []
    equal_authors = _authors_from_equal_contrib(region)

    i = 0
    # Skip leading affiliation blocks (Nature image-title layouts)
    while i < len(lines) and (
        _looks_like_affiliation_only(lines[i])
        or "these authors contributed equally" in lines[i].lower()
    ):
        i += 1

    title_parts, i = _take_title_wrap(lines, i)
    if title_parts:
        title = " ".join(title_parts)
    else:
        # Scan forward for a title-like line before authors / body prose
        j = i
        while j < len(lines):
            if _looks_like_affiliation_only(lines[j]):
                j += 1
                continue
            if _looks_like_prose(lines[j]):
                break
            parts, j2 = _take_title_wrap(lines, j)
            if parts:
                title_parts = parts
                title = " ".join(parts)
                i = j2
                break
            j += 1

    # Soft-fail: never keep a title that is still publisher front matter
    # (e.g. wrapped remnants that only classify as FM once joined).
    title = _reject_publisher_title(title)

    # Author lines follow title (or start after skipped affiliations)
    saw_acm = False
    while i < len(lines):
        line = lines[i]
        if "these authors contributed equally" in line.lower():
            break
        acm = _acm_author_name(line)
        if acm:
            author_lines.append(line)
            saw_acm = True
            i += 1
            continue
        if saw_acm:
            # ACM blocks are contiguous; prose/abstract follows immediately
            break
        if _looks_like_affiliation_only(line):
            break
        if _looks_like_prose(line):
            break
        if _looks_like_author_line(line):
            author_lines.append(line)
            i += 1
            # Keep collecting while the next line is also authorish
            # (wrapped author lists; Nature / arXiv multi-line names).
            continue
        if author_lines:
            break
        i += 1

    # ACM lines are one person each; otherwise join wraps carefully so
    # "Lionel\nWong" stays one name while "Phillip Lin\nBianca …" splits.
    authors: list[str] = []
    if author_lines:
        if any(_acm_author_name(ln) for ln in author_lines):
            for aline in author_lines:
                authors.extend(split_author_names(aline))
        else:
            joined = author_lines[0]
            for ln in author_lines[1:]:
                prev = joined.rstrip()
                if prev.endswith((",", "&")) or ln.lstrip().lower().startswith(
                    ("&", "and ")
                ):
                    joined = f"{joined} {ln}"
                else:
                    # "Lionel" + "Wong*, Mina…" → space; "Phillip Lin" + "Bianca…" → comma
                    tail = prev.split(",")[-1].strip()
                    if len(tail.split()) == 1 and tail[:1].isupper():
                        joined = f"{joined} {ln}"
                    else:
                        joined = f"{joined}, {ln}"
            joined = re.sub(r"\s+", " ", joined)
            authors = split_author_names(joined)
        authors = _dedupe(authors)

    # Nature-style equal-contribution clause (also when stronger / only source)
    if equal_authors and (not authors or len(equal_authors) >= len(authors)):
        authors = equal_authors

    authors_raw = ", ".join(author_lines) if author_lines else (
        ", ".join(authors) if authors else None
    )

    return {
        "title": title,
        "authors": authors,
        "authors_raw": authors_raw,
        "emails": emails,
        **publisher_fields,
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
