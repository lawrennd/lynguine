"""``docx_chatbot.v1`` — chatbot transcript DOCX → dialogue units.

Seeded from ``dialogue_formats.access.parse_chatbot`` (simplified; no project
tagging). Expects Participant headings and Conversation Transcript sections.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Document
from ..unit import Unit

SUMMARY_RE = re.compile(r"^\s*Conversation Summary\s*:?\s*$", re.I)
TRANSCRIPT_RE = re.compile(r"^\s*Conversation Transcript\s*:?\s*$", re.I)
PARTICIPANT_HEADING_RE = re.compile(r"^\s*Participant\s+(\d{3,})\s*$", re.I)
PARTICIPANT_TURN_RE = re.compile(r"^\s*Participant\s+(\d{3,})\s*:\s*(.*)$", re.I | re.S)
TASK_RE = re.compile(r"^\s*(Task\s+\d+\s*:.*|Activity\s*:.*)$", re.I)
PRIVATE_RE = re.compile(r"^\s*Private Comments\b", re.I)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _transcript_parts(raw: str) -> list[str]:
    """Split a Recollective conversation blob into bot / participant turns.

    Exports often pack one conversation into a single paragraph with a
    newline per turn (no blank lines). Flattening first would hide
    ``Participant N:`` answers after the opening bot greeting.
    """
    lines = [ln.strip() for ln in raw.replace("\xa0", " ").splitlines() if ln.strip()]
    if len(lines) > 1:
        return lines
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw) if b.strip()]
    return blocks or [_norm(raw)]


def _paragraphs(document: Document) -> list[str]:
    return [b.text for p in document.pages for b in p.blocks if b.block_type == "text"]


class DocxChatbotV1:
    id = "docx_chatbot.v1"
    aspects = ("dialogue_units",)

    def segment(self, document: Document, **_params) -> list[Unit]:
        paras = _paragraphs(document)
        stem = Path(document.path).name
        min_unit_words = int(_params["min_unit_words"]) if _params.get("min_unit_words") not in (None, "") else 0
        units: list[Unit] = []
        pid: str | None = None
        state = "outside"
        last_q = ""
        n = 0

        for raw in paras:
            text = _norm(raw)
            m = PARTICIPANT_HEADING_RE.match(text)
            if m:
                pid, state = m.group(1), "outside"
                last_q, n = "", 0
                continue
            if pid is None:
                continue
            if state != "transcript" and TASK_RE.match(text):
                continue
            if SUMMARY_RE.match(text):
                state = "summary"
                continue
            if TRANSCRIPT_RE.match(text):
                state = "transcript"
                continue
            if state != "transcript":
                continue
            if PRIVATE_RE.match(text):
                continue
            for part in _transcript_parts(raw):
                if PRIVATE_RE.match(part):
                    continue
                part_n = _norm(part)
                pm = PARTICIPANT_TURN_RE.match(part_n)
                if pm:
                    answer = _norm(pm.group(2))
                    if not answer:
                        continue
                    if min_unit_words and len(answer.split()) < min_unit_words:
                        continue
                    n += 1
                    units.append(
                        Unit(
                            unit_id=f"{stem}::{pid}::t{n:03d}",
                            text=answer,
                            segment_strategy=self.id,
                            aspect="dialogue_units",
                            chunk_index=n - 1,
                            word_count=len(answer.split()),
                            chunking_method="chatbot_answer",
                            was_truncated=False,
                            source_path=document.path,
                            extras={
                                "format": "chatbot",
                                "participant_id": pid,
                                "context": last_q,
                                "extract_text": answer,
                            },
                        )
                    )
                else:
                    last_q = part_n
        return units
