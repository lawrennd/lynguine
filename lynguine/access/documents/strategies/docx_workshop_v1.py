"""``docx_workshop.v1`` — workshop transcript DOCX → chunked dialogue units.

Seeded from ``dialogue_formats.access`` workshop unitisation (simplified).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Document
from ..unit import Unit

DEFAULT_CHUNK_WORDS = 150
DEFAULT_MAX_WORDS = 260
DEFAULT_MIN_WORDS = 4


class _Labels:
    def __init__(self, facilitator_names: list[str] | None = None):
        names = list(facilitator_names or [])
        fac = "|".join([r"Facilitator"] + [re.escape(n) for n in names])
        self.label = re.compile(
            r"^\s*(Speaker\s*\d+|S\d+|" + fac + r")\s*[:\-–.\t]", re.I
        )
        self.facilitator = re.compile(r"^\s*(" + fac + r")\s*[:\-–.\t]", re.I)
        self.inner = re.compile(
            r"\s(?=(?:Speaker\s*\d+|S\d+|" + fac + r")\s*:\s)"
        )

    def split_turns(self, par: str) -> list[str]:
        return [x.strip() for x in self.inner.split(par) if x.strip()]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


class DocxWorkshopV1:
    id = "docx_workshop.v1"
    aspects = ("dialogue_units",)

    def segment(
        self,
        document: Document,
        *,
        facilitator_names: list[str] | None = None,
        workshop_chunk_words: int = DEFAULT_CHUNK_WORDS,
        workshop_max_words: int = DEFAULT_MAX_WORDS,
        min_unit_words: int = DEFAULT_MIN_WORDS,
        **_ignored,
    ) -> list[Unit]:
        labels = _Labels(facilitator_names)
        paras = [
            _norm(b.text)
            for p in document.pages
            for b in p.blocks
            if b.block_type == "text" and b.text.strip()
        ]
        stem = Path(document.path).name

        def split_long(par: str) -> list[str]:
            if len(par.split()) <= workshop_max_words:
                return [par]
            label = labels.label.match(par)
            prefix = par[: label.end()] if label else ""
            out, cur = [], []
            for s in re.split(r"(?<=[.?!])\s+", par[len(prefix) :]):
                if not s:
                    continue
                cur.append(s)
                if len(" ".join(cur).split()) >= workshop_chunk_words:
                    out.append(prefix + " ".join(cur))
                    cur = []
            if cur:
                out.append(prefix + " ".join(cur))
            return out

        pieces = [
            x for par in paras for t in labels.split_turns(par) for x in split_long(t)
        ]
        units: list[Unit] = []
        buf: list[str] = []
        n = 0

        def flush() -> None:
            nonlocal n
            if not buf:
                return
            n += 1
            lines = [
                ("[FACILITATOR] " + x) if labels.facilitator.match(x) else x for x in buf
            ]
            ext = " ".join(x for x in buf if not labels.facilitator.match(x))
            words = len(ext.split())
            if words < min_unit_words:
                buf.clear()
                return
            units.append(
                Unit(
                    unit_id=f"{stem}::c{n:04d}",
                    text="\n".join(lines),
                    segment_strategy=self.id,
                    aspect="dialogue_units",
                    chunk_index=n - 1,
                    word_count=words,
                    chunking_method="workshop_chunk",
                    was_truncated=False,
                    source_path=document.path,
                    extras={
                        "format": "workshop",
                        "extract_text": ext,
                        "n_fac_lines": sum(
                            l.startswith("[FACILITATOR]") for l in lines
                        ),
                    },
                )
            )
            buf.clear()

        for x in pieces:
            buf.append(x)
            if len(" ".join(buf).split()) >= workshop_chunk_words:
                flush()
        flush()
        return units
