"""Tests for CIP-0013 layout recogniser v0."""

from __future__ import annotations

import pytest

fitz = pytest.importorskip("fitz")
pytest.importorskip("docx")

from lynguine.access.documents import (
    SparseTextLayerError,
    UnknownStrategyError,
    choose_strategy,
    document_features,
    rank_strategies,
    read_docx,
    read_pdf,
    segment_pdf,
)
from lynguine.tests.fixtures.documents.builders import (
    make_chatbot_transcript,
    make_pmlr_twocolumn,
    make_public_dialogue_report,
    make_scan_like,
    make_workshop_transcript,
)


def test_features_public_dialogue_report(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    feats = document_features(doc)
    assert feats["reader"] == "pdf"
    assert feats["text_layer"] == "present"
    assert feats["has_findings"]
    assert feats["has_recommendations"]
    assert feats["has_references_heading"]


def test_auto_body_chunks_picks_pub_dialogue(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    units = segment_pdf(str(pdf), strategy="auto", allowed_roots=[str(tmp_path)])
    assert units
    assert units[0].segment_strategy == "pub_dialogue.v1"
    assert units[0].extras["recogniser_score"] > 0
    assert "recogniser_rationale" in units[0].extras
    rows = [u.to_dict() for u in units]
    assert "recogniser_score" in rows[0]
    assert rows[0]["segment_strategy"] == "pub_dialogue.v1"


def test_auto_references_picks_pmlr(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_pmlr_twocolumn(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    choice = choose_strategy(doc, aspect="references", strategy="auto")
    assert choice.strategy_id == "pmlr_references.v1"
    assert choice.score > 0
    ranked = rank_strategies(doc, aspect="references")
    assert ranked[0].strategy_id == "pmlr_references.v1"


def test_manual_override_ignores_ranking(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    choice = choose_strategy(doc, aspect="body_chunks", strategy="pub_dialogue.v1")
    assert choice.strategy_id == "pub_dialogue.v1"
    assert choice.rationale.startswith("manual override")


def test_auto_chatbot_docx(tmp_path):
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
    assert units[0].extras["recogniser_score"] > 0


def test_auto_workshop_docx(tmp_path):
    path = tmp_path / "ws.docx"
    make_workshop_transcript(path)
    units = segment_pdf(
        str(path),
        reader="docx",
        strategy="auto",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
        facilitator_names=["Facilitator"],
    )
    assert units
    assert units[0].segment_strategy == "docx_workshop.v1"


def test_sparse_auto_does_not_silently_succeed(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    with pytest.raises(SparseTextLayerError):
        segment_pdf(str(pdf), strategy="auto", allowed_roots=[str(tmp_path)])
    units = segment_pdf(
        str(pdf),
        strategy="auto",
        allowed_roots=[str(tmp_path)],
        on_sparse_text="empty",
    )
    assert units == []


def test_rank_sparse_scores_zero(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    ranked = rank_strategies(doc, aspect="body_chunks")
    assert ranked
    assert all(c.score == 0 for c in ranked)
    with pytest.raises(UnknownStrategyError, match="no positive match"):
        choose_strategy(doc, aspect="body_chunks", strategy="auto")


def test_docx_features(tmp_path):
    path = tmp_path / "chat.docx"
    make_chatbot_transcript(path)
    doc = read_docx(str(path), allowed_roots=[str(tmp_path)])
    feats = document_features(doc)
    assert feats["reader"] == "docx"
    assert feats["has_participant_heading"]
    assert feats["has_conversation_transcript"]
