"""Tests for CIP-0013 references aspect (pmlr_references.v1)."""

from __future__ import annotations

import pytest
import yaml

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import (
    ReferencesRegionNotFoundError,
    extract_references,
    segment_pdf,
)
from lynguine.assess.compute import Compute
from lynguine.tests.fixtures.documents.builders import (
    make_pmlr_twocolumn,
    make_public_dialogue_report,
)

MANIFEST = (
    __import__("pathlib").Path(__file__).resolve().parent
    / "fixtures"
    / "documents"
    / "manifests"
    / "pmlr_twocolumn_v1.yml"
)


def test_extract_references_from_pmlr_fixture(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_pmlr_twocolumn(pdf)
    units = segment_pdf(
        str(pdf),
        strategy="auto",
        aspect="references",
        allowed_roots=[str(tmp_path)],
    )
    assert len(units) >= 3
    assert all(u.aspect == "references" for u in units)
    assert all(u.segment_strategy == "pmlr_references.v1" for u in units)
    assert units[0].extras["ref_raw"] == units[0].text


def test_gold_ref_raw_from_manifest(tmp_path):
    with MANIFEST.open(encoding="utf-8") as fh:
        expected = yaml.safe_load(fh)["expected"]
    pdf = tmp_path / "paper.pdf"
    make_pmlr_twocolumn(pdf)
    rows = extract_references(pdf.name, root=str(tmp_path))
    joined = "\n".join(r["ref_raw"] for r in rows)
    for needle in expected["ref_raw_contains"]:
        assert needle in joined, needle


def test_missing_references_region(tmp_path):
    """Present text without a References heading → clear error."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(72, 72, 500, 400),
        " ".join(f"word{i}" for i in range(50)),
        fontsize=11,
    )
    path = tmp_path / "norefs.pdf"
    doc.save(path)
    doc.close()
    with pytest.raises(ReferencesRegionNotFoundError):
        segment_pdf(
            str(path),
            aspect="references",
            strategy="pmlr_references.v1",
            allowed_roots=[str(tmp_path)],
        )


def test_public_dialogue_report_has_references(tmp_path):
    """Report-style References list is also extractable."""
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    units = segment_pdf(
        str(pdf),
        aspect="references",
        strategy="pmlr_references.v1",
        allowed_roots=[str(tmp_path)],
    )
    assert len(units) >= 2
    assert any("Sciencewise" in u.text or "Hopkins" in u.text for u in units)


def test_extract_references_in_compute_registry():
    names = [f["name"] for f in Compute({})._compute_functions_list()]
    assert "extract_references" in names
