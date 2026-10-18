"""``form_fields`` engine — structured key/value extraction from form-like PDFs.

Algorithms live here; corpus-specific labels, section bounds, and aliases come
from YAML strategy ``params`` (CIP-0013).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..model import Document
from ..unit import Unit

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_DAY_MON_YEAR_RE = re.compile(
    r"(?P<day>\d{1,2})\s+(?P<mon>[A-Za-z]{3,9})\s+(?P<year>\d{4})"
)
_CAM_TERM_RE = re.compile(r"\((?P<term>MT|LT|ET)\s*(?P<year>\d{4})\)", re.I)

_DEFAULT_NAME_LINE = re.compile(
    r"^(?P<family>[A-Za-z][A-Za-z' -]+),\s*"
    r"(?P<title>Mr|Ms|Mrs|Miss|Mx|Dr)\s+"
    r"(?P<given>.+)$"
)
_DEFAULT_COURSE = re.compile(
    r"(?P<award>MPhil|PhD)\s+in\s+(?P<title>.+?)(?:\s*\((?P<code>[A-Z0-9]+)\))?\s*$",
    re.I | re.M,
)


def _joined_pages(document: Document) -> str:
    """Join page texts with newlines for line-oriented form matching."""
    return "\n".join(page.text for page in document.pages)


def _norm_person_case(s: str) -> str:
    """Title-case shouted tokens; leave mixed ordinary case alone."""
    s = s.strip()
    if not s:
        return s
    parts = []
    for word in s.split():
        letters = [c for c in word if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) / len(letters) > 0.85:
            parts.append(word.title())
        else:
            parts.append(word)
    return " ".join(parts)


def _to_iso_date(text: str | None, month_aliases: dict[str, str]) -> str | None:
    if not text:
        return None
    m = _DAY_MON_YEAR_RE.search(text.strip())
    if not m:
        return None
    day = int(m.group("day"))
    mon_raw = m.group("mon")
    year = int(m.group("year"))
    mon = month_aliases.get(mon_raw.lower(), mon_raw[:3].title())
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(f"{day} {mon} {year}", fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_start_date(
    raw: str | None, month_aliases: dict[str, str]
) -> dict[str, str | None]:
    if not raw:
        return {
            "course_start_date": None,
            "course_start_term": None,
            "course_start_raw": None,
        }
    raw = raw.strip()
    term = None
    tm = _CAM_TERM_RE.search(raw)
    if tm:
        term = f"{tm.group('term').upper()} {tm.group('year')}"
    return {
        "course_start_date": _to_iso_date(raw, month_aliases),
        "course_start_term": term,
        "course_start_raw": raw,
    }


def _section_after(text: str, start_pat: str, end_pats: list[str]) -> str | None:
    start = re.search(start_pat, text, flags=re.I | re.M)
    if not start:
        return None
    rest = text[start.end() :]
    end_at = len(rest)
    for ep in end_pats:
        m = re.search(ep, rest, flags=re.I | re.M)
        if m:
            end_at = min(end_at, m.start())
    return rest[:end_at]


def _label_value(page0: str, label: str, until: list[str] | None = None) -> str | None:
    """Match ``Label <value>`` until optional stop tokens or end of line/block."""
    until = until or []
    stop = "|".join(re.escape(u) for u in until) if until else r"\n"
    if until:
        pat = rf"{re.escape(label)}\s+(.+?)(?:\s+(?:{stop})|\n|$)"
    else:
        pat = rf"{re.escape(label)}\s+(.+?)(?:\n|$)"
    m = re.search(pat, page0, flags=re.I | re.M)
    return m.group(1).strip() if m else None


def parse_name_from_page0(page0: str, name_line_re: re.Pattern[str]) -> dict[str, Any]:
    hits = []
    for line in page0.splitlines():
        line = line.strip()
        m = name_line_re.match(line)
        if not m:
            continue
        family_raw = m.group("family")
        given_raw = m.group("given").strip()
        if re.search(r"(?i)\b(mphil|phd|computer science)\b", given_raw):
            continue
        hits.append(
            {
                "family_raw": family_raw,
                "given_raw": given_raw,
                "title": m.group("title"),
                "family": _norm_person_case(family_raw),
                "given": _norm_person_case(given_raw),
            }
        )
    if not hits:
        return {
            "family": None,
            "given": None,
            "title": None,
            "family_raw": None,
            "given_raw": None,
            "name_parse_ok": False,
        }
    best = hits[0]
    best["name_parse_ok"] = True
    best["name_line_count"] = len(hits)
    return best


def parse_header(page0: str, params: dict[str, Any]) -> dict[str, Any]:
    labels = params.get("labels") or {}
    month_aliases = {
        str(k).lower(): str(v) for k, v in (params.get("month_aliases") or {}).items()
    }
    name_re = _DEFAULT_NAME_LINE
    course_re = _DEFAULT_COURSE
    if params.get("name_line_pattern"):
        name_re = re.compile(params["name_line_pattern"])
    if params.get("course_pattern"):
        course_re = re.compile(params["course_pattern"], re.I | re.M)

    name = parse_name_from_page0(page0, name_re)
    course = course_re.search(page0)
    course_full = award = title = code = None
    if course:
        award = course.group("award")
        title = course.group("title").strip()
        title = re.sub(r"(?i)\s*course\s*$", "", title).strip()
        code = course.groupdict().get("code")
        course_full = course.group(0).strip()
        course_full = re.sub(r"(?i)\s*course\s*$", "", course_full).strip()

    submitted_raw = _label_value(
        page0,
        labels.get("date_submitted", "Date submitted"),
        until=["Mode of study"],
    )
    start = _parse_start_date(
        _label_value(
            page0,
            labels.get("course_start_date", "Course start date"),
            until=["PUF"],
        ),
        month_aliases,
    )

    if title and start["course_start_term"]:
        title = re.sub(
            r",?\s*(Michaelmas|Lent|Easter)\s+Term\s+\d{4}\s*$",
            "",
            title,
            flags=re.I,
        ).strip()
        if course_full:
            course_full = re.sub(
                r",?\s*(Michaelmas|Lent|Easter)\s+Term\s+\d{4}\s*$",
                "",
                course_full,
                flags=re.I,
            ).strip()

    app_label = labels.get("application_number", "Application Number:")
    usn_label = labels.get("usn", "USN:")
    app_m = re.search(rf"{re.escape(app_label)}\s*(\d+)", page0, re.I)
    usn_m = re.search(rf"{re.escape(usn_label)}\s*(\d+)", page0, re.I)

    return {
        **name,
        "application_number": app_m.group(1) if app_m else None,
        "usn": usn_m.group(1) if usn_m else None,
        "award": award,
        "course_title": title,
        "course_code": code,
        "course": course_full,
        "date_submitted": _to_iso_date(submitted_raw, month_aliases),
        "date_submitted_raw": submitted_raw,
        "mode_of_study": _label_value(
            page0, labels.get("mode_of_study", "Mode of study"), until=["Course start"]
        ),
        **start,
        "nationality": _label_value(
            page0,
            labels.get("nationality", "Nationality"),
            until=["Country of birth"],
        ),
        "fee_status": _label_value(
            page0, labels.get("fee_status", "Estimated fee status")
        ),
    }


def parse_contact(full_text: str, params: dict[str, Any]) -> dict[str, Any]:
    contact_cfg = params.get("contact") or {}
    personal_start = contact_cfg.get("personal_section", r"^Personal Information\s*$")
    personal_ends = contact_cfg.get(
        "personal_end",
        [r"^Referee Details\s*$", r"^Research\s*$", r"^Academic History\s*$"],
    )
    contact_start = contact_cfg.get("contact_section", r"^Contact\s*$")
    contact_ends = contact_cfg.get(
        "contact_end",
        [
            r"^Home address\s*$",
            r"^Immigration\s*$",
            r"^Language\s*$",
            r"^Funding\s*$",
            r"^Referee Details\s*$",
            r"^Research\s*$",
        ],
    )
    address_stop = contact_cfg.get(
        "address_stop_prefixes",
        [
            "Home address",
            "Email",
            "Telephone",
            "Mobile",
            "Phone",
            "Valid until",
            "Immigration",
            "Language",
            "Funding",
            "Referee",
        ],
    )
    referee_heading = contact_cfg.get("referee_section", r"^Referee Details\s*$")

    personal = _section_after(full_text, personal_start, personal_ends)
    region = personal if personal else full_text
    ref = re.search(referee_heading, region, flags=re.I | re.M)
    if ref:
        region = region[: ref.start()]

    contact = _section_after(region, contact_start, contact_ends)
    blob = contact if contact else region

    email = None
    m = re.search(r"(?im)^Email\s+(\S+@\S+)\s*$", blob)
    if m:
        email = m.group(1).strip()
    else:
        m = re.search(r"(?im)^Email\s*$", blob)
        if m:
            after = blob[m.end() :]
            for line in after.splitlines():
                line = line.strip()
                if not line:
                    continue
                em = EMAIL_RE.search(line)
                if em:
                    email = em.group(0)
                break
        if email is None:
            found = EMAIL_RE.findall(blob)
            email = found[0] if found else None

    address_lines: list[str] = []
    lines = blob.splitlines()
    stop_pat = r"^(?:" + "|".join(re.escape(p) for p in address_stop) + r")\b"
    for i, line in enumerate(lines):
        if re.match(r"(?i)^Contact address\b", line.strip()):
            rest = re.sub(r"(?i)^Contact address\s*", "", line.strip())
            if rest:
                address_lines.append(rest)
            for cont in lines[i + 1 :]:
                cont_s = cont.strip()
                if not cont_s:
                    break
                if re.match(stop_pat, cont_s, flags=re.I):
                    break
                if EMAIL_RE.search(cont_s):
                    break
                address_lines.append(cont_s)
            break

    referee_emails: list[str] = []
    for m in re.finditer(
        rf"(?im){referee_heading}([\s\S]*?)(?={referee_heading}|\Z)",
        full_text,
    ):
        block = m.group(1)
        cut = re.search(
            r"(?im)^(Personal Information|Research Experience|Curriculum Vitae|"
            r"Supporting Documents|Academic History)\s*$",
            block,
        )
        if cut:
            block = block[: cut.start()]
        referee_emails.extend(EMAIL_RE.findall(block))
    referee_emails = sorted(set(referee_emails))

    all_emails = sorted(set(EMAIL_RE.findall(full_text)))
    referee_only = [e for e in referee_emails if e != email]
    contact_emails = EMAIL_RE.findall(blob)

    return {
        "email": email,
        "contact_address": ", ".join(address_lines) if address_lines else None,
        "emails_all": all_emails,
        "emails_referee": referee_only,
        "email_ambiguous": len(set(contact_emails)) > 1,
    }


def extract_fields(document: Document, params: dict[str, Any]) -> dict[str, Any]:
    """Return structured form fields for *document* using *params*."""
    page0 = document.pages[0].text if document.pages else ""
    full = _joined_pages(document)
    header = parse_header(page0, params)
    contact = parse_contact(full, params)
    return {**header, **contact}


class FormFieldsEngine:
    """Emit one ``form_fields`` unit per document (fields in ``extras``)."""

    name = "form_fields"

    def run(
        self,
        document: Document,
        params: dict[str, Any],
        *,
        strategy_id: str,
        aspects: tuple[str, ...],
    ) -> list[Unit]:
        aspect = "form_fields" if "form_fields" in aspects else aspects[0]
        fields = extract_fields(document, params or {})
        stem = Path(document.path).name
        summary_parts = [
            fields.get("family") or "",
            fields.get("given") or "",
            fields.get("application_number") or "",
        ]
        text = " ".join(p for p in summary_parts if p).strip()
        extras = {
            **fields,
            "segment_engine": self.name,
            "form_fields": fields,
        }
        return [
            Unit(
                unit_id=f"{stem}::form0",
                text=text,
                segment_strategy=strategy_id,
                aspect=aspect,
                chunk_index=0,
                word_count=len(text.split()) if text else 0,
                chunking_method="form_fields",
                was_truncated=False,
                source_path=document.path,
                extras=extras,
            )
        ]
