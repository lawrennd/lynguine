"""``pmlr_references.v1`` — locate References region and split prose entries.

Region detection and entry splitting are separate steps (CIP-0013). v1 emits
``ref_raw`` strings only (stored in ``Unit.text``).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..errors import DocumentSegmentError
from ..model import Document
from ..unit import Unit

# Headings that start a references block (case-insensitive, line-oriented).
_REF_HEADING = re.compile(
    r"^\s*(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$",
    re.MULTILINE,
)
# Optional end of references region (next major heading).
_REF_END = re.compile(
    r"^\s*(Appendix|APPENDIX|Supplementary|Acknowledgments|Acknowledgements)\b",
    re.MULTILINE,
)


class ReferencesRegionNotFoundError(DocumentSegmentError):
    """No References / Bibliography heading found in the document."""


def find_references_region(full_text: str) -> str:
    """Return the text after the references heading, or raise if missing."""
    match = _REF_HEADING.search(full_text)
    if not match:
        raise ReferencesRegionNotFoundError(
            "No References/Bibliography heading found in document text"
        )
    region = full_text[match.end() :]
    end = _REF_END.search(region)
    if end:
        region = region[: end.start()]
    return region.strip()


_YEAR_DOT = re.compile(r"(?:19|20)\d{2}\.")


def _blank_line_blocks(region: str) -> list[str]:
    blocks = [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*\n", region)]
    return [b for b in blocks if b]


def _blank_line_plausible(blocks: list[str], collapsed: str) -> bool:
    """True when blank-line blocks look like individual bibliography entries.

    Two-column PMLR extraction often yields a handful of huge blank-line
    blocks (page/column artifacts) while year terminators mark many entries.
    Prefer year/numbered splitting in that case.
    """
    if len(blocks) < 2:
        return False
    year_count = len(_YEAR_DOT.findall(collapsed))
    if year_count >= 4 and len(blocks) * 2 < year_count:
        return False
    if year_count >= 4 and any(len(b.split()) > 100 for b in blocks):
        return False
    return True


def _year_dot_split(collapsed: str) -> list[str]:
    parts = re.split(r"(?<=(?:19|20)\d{2}\.)\s+(?=[A-Z])", collapsed)
    return [p.strip() for p in parts if p.strip()]


def _year_paren_split(collapsed: str) -> list[str]:
    parts = re.split(r"(?<=\((?:19|20)\d{2}\)\.)\s+(?=[A-Z])", collapsed)
    return [p.strip() for p in parts if p.strip()]


def _numbered_split(collapsed: str) -> list[str]:
    numbered = re.split(r"(?=\[\d+\]\s+)", collapsed)
    return [p.strip() for p in numbered if p.strip()]


def split_reference_entries(region: str) -> list[str]:
    """Split a references region into ordered raw entry strings.

    Prefers blank-line separated blocks when they look like individual
    entries. PDF text extraction often collapses blank lines or invents a
    few page-sized blocks, so also split after year markers typical of
    author–year prose (``2020. NextAuthor`` or ``(2024). NextAuthor``) or
    numbered ``[1]`` lists.
    """
    region = region.strip()
    if not region:
        return []

    collapsed = re.sub(r"\s+", " ", region).strip()
    blocks = _blank_line_blocks(region)
    if _blank_line_plausible(blocks, collapsed):
        return blocks

    parts = _year_dot_split(collapsed)
    if len(parts) >= 2:
        return parts

    parts = _year_paren_split(collapsed)
    if len(parts) >= 2:
        return parts

    numbered = _numbered_split(collapsed)
    if len(numbered) >= 2:
        return numbered

    # Fall back to blank-line blocks even if coarse, then whole region
    if len(blocks) >= 2:
        return blocks
    return [collapsed] if collapsed else []


class PmlrReferencesV1:
    """Extract bibliographic reference strings from an academic PDF model."""

    id = "pmlr_references.v1"
    aspects = ("references",)

    def segment(self, document: Document, **_params) -> list[Unit]:
        region = find_references_region(document.full_text)
        entries = split_reference_entries(region)
        if not entries:
            raise DocumentSegmentError(
                f"References region found in {document.path!r} but no entries parsed"
            )
        stem = Path(document.path).name
        units: list[Unit] = []
        for i, raw in enumerate(entries):
            units.append(
                Unit(
                    unit_id=f"{stem}::ref{i:04d}",
                    text=raw,
                    segment_strategy=self.id,
                    aspect="references",
                    chunk_index=i,
                    word_count=len(raw.split()),
                    chunking_method="references_region",
                    was_truncated=False,
                    source_path=document.path,
                    extras={"ref_id": f"{stem}::ref{i:04d}", "ref_raw": raw},
                )
            )
        return units
