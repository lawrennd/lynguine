"""Tests for CIP-0013 DOCX reader and dialogue unit strategies."""

from __future__ import annotations

import pytest

pytest.importorskip("docx")

from lynguine.access.documents import (
    read_docx,
    segment_pdf,
)
from lynguine.tests.fixtures.documents.builders import (
    make_chatbot_transcript,
    make_workshop_transcript,
)


def test_read_docx_paragraphs(tmp_path):
    path = tmp_path / "chat.docx"
    make_chatbot_transcript(path)
    doc = read_docx(str(path), allowed_roots=[str(tmp_path)])
    assert doc.reader == "docx"
    assert doc.total_words > 0
    assert "Participant 001" in doc.full_text


def test_docx_chatbot_units(tmp_path):
    path = tmp_path / "chat.docx"
    make_chatbot_transcript(path)
    units = segment_pdf(
        str(path),
        reader="docx",
        strategy="docx_chatbot.v1",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
    )
    assert len(units) >= 3
    assert all(u.aspect == "dialogue_units" for u in units)
    assert all(u.extras.get("format") == "chatbot" for u in units)
    assert any("accountability" in u.text for u in units)


def test_docx_workshop_units(tmp_path):
    path = tmp_path / "ws.docx"
    make_workshop_transcript(path)
    units = segment_pdf(
        str(path),
        reader="docx",
        strategy="docx_workshop.v1",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
        facilitator_names=["Facilitator"],
    )
    assert len(units) >= 1
    assert units[0].extras.get("format") == "workshop"
    assert units[0].word_count >= 4


def test_dialogue_auto_picks_chatbot(tmp_path):
    path = tmp_path / "chat.docx"
    make_chatbot_transcript(path)
    units = segment_pdf(
        str(path),
        reader="docx",
        strategy="auto",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
    )
    assert units
    assert units[0].segment_strategy == "docx_chatbot.v1"
    assert units[0].extras.get("recogniser_score", 0) > 0
