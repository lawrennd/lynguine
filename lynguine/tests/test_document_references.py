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
from lynguine.access.documents.strategies.pmlr_references_v1 import (
    split_reference_entries,
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


def test_split_rejects_coarse_blank_line_page_artifacts():
    """Few huge blank-line blocks + many year dots → year-boundary split."""
    # Simulate two-column PDF: one blank line mid-list (page break), years intact
    entries = [
        "TW Archibald et al. On Markov decision processes. JORS, 1995.",
        "Leemon Baird. Residual algorithms. ML Proceedings, 1995.",
        "M. G. Bellemare et al. Arcade learning environment. JAIR, 2013.",
        "Dimitri Bertsekas. Neuro-dynamic programming. Athena, 1996.",
        "Shalabh Bhatnagar et al. Natural actor-critic. Automatica, 2009.",
    ]
    # Join with newlines (line-wrapped style) and one blank line mid-way
    region = "\n".join(entries[:3]) + "\n\n" + "\n".join(entries[3:])
    parts = split_reference_entries(region)
    assert len(parts) == 5
    assert parts[0].startswith("TW Archibald")
    assert parts[1].startswith("Leemon Baird")
    assert all(len(p.split()) < 40 for p in parts)


def test_split_keeps_blank_line_when_entries_are_separated():
    region = (
        "Faruk Ahmed and Aaron Courville. Detecting semantic anomalies. "
        "In ICML, 2019.\n\n"
        "Stafford Beer. Brain of the Firm. Wiley, 1972.\n\n"
        "Roger Conant. Every good regulator. Int J Systems Sci, 1970."
    )
    parts = split_reference_entries(region)
    assert len(parts) == 3
    assert "Ahmed" in parts[0]
    assert "Beer" in parts[1]


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
