"""Tests for CIP-0013 strategy API and pub_dialogue.v1 segmentation."""

from __future__ import annotations

import pytest

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import (
    SparseTextLayerError,
    UnknownStrategyError,
    document_segment,
    ensure_builtin_strategies,
    list_strategies,
    segment_pdf,
    segment_pdf_frame,
)
from lynguine.assess.compute import Compute
from lynguine.tests.fixtures.documents.builders import (
    make_pmlr_twocolumn,
    make_public_dialogue_report,
    make_scan_like,
)


@pytest.fixture(autouse=True)
def _builtin_strategies():
    ensure_builtin_strategies()


def test_pub_dialogue_strategy_registered():
    assert "pub_dialogue.v1" in list_strategies(aspect="body_chunks")


def test_segment_public_dialogue_report(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)

    units = segment_pdf(
        str(pdf),
        strategy="pub_dialogue.v1",
        allowed_roots=[str(tmp_path)],
    )

    assert len(units) >= 1
    assert all(u.segment_strategy == "pub_dialogue.v1" for u in units)
    assert all(u.aspect == "body_chunks" for u in units)
    assert all(u.word_count >= 40 for u in units)
    assert any("finding" in u.text.lower() or "Finding" in u.text for u in units) or any(
        u.chunking_method in ("paragraph", "sentence_fallback", "sentence_split")
        for u in units
    )


def test_segment_auto_resolves_sole_strategy(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    units = segment_pdf(str(pdf), strategy="auto", allowed_roots=[str(tmp_path)])
    assert units
    assert units[0].segment_strategy == "pub_dialogue.v1"


def test_segment_frame_exploded(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    df = segment_pdf_frame(
        str(pdf), strategy="pub_dialogue.v1", allowed_roots=[str(tmp_path)]
    )
    assert len(df) >= 1
    assert "text" in df.columns
    assert "segment_strategy" in df.columns
    assert df["segment_strategy"].nunique() == 1


def test_segment_pmlr_fixture(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_pmlr_twocolumn(pdf)
    units = segment_pdf(
        str(pdf), strategy="pub_dialogue.v1", allowed_roots=[str(tmp_path)]
    )
    # Two-column academic text should yield at least one kept chunk
    assert len(units) >= 1


def test_sparse_text_errors_by_default(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    with pytest.raises(SparseTextLayerError):
        segment_pdf(str(pdf), allowed_roots=[str(tmp_path)])


def test_sparse_text_empty_mode(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    units = segment_pdf(
        str(pdf),
        allowed_roots=[str(tmp_path)],
        on_sparse_text="empty",
    )
    assert units == []


def test_unknown_strategy():
    with pytest.raises(UnknownStrategyError):
        ensure_builtin_strategies()
        from lynguine.access.documents.strategy import resolve_strategy_id

        resolve_strategy_id("no_such.v1", aspect="body_chunks")


def test_document_segment_compute_fn(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    rows = document_segment(
        pdf.name,
        strategy="pub_dialogue.v1",
        root=str(tmp_path),
    )
    assert isinstance(rows, list)
    assert rows and "text" in rows[0]
    assert rows[0]["segment_strategy"] == "pub_dialogue.v1"


def test_compute_registry_lists_document_segment():
    compute = Compute({})
    names = [f["name"] for f in compute._compute_functions_list()]
    assert "document_segment" in names
