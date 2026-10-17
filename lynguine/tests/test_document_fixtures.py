"""Parametrised structural tests for CIP-0013 synthetic document fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import TextLayer, read_pdf
from lynguine.tests.fixtures.documents.builders import BUILDERS

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "documents"
MANIFESTS = sorted((FIXTURES / "manifests").glob("*.yml"))


def _load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), path
    return data


def _median_text_block_width_ratio(pdf_path: Path, page_index: int = 0) -> float:
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        pw = page.rect.width
        ratios = []
        for block in page.get_text("blocks") or []:
            if len(block) < 7 or block[6] != 0:
                continue
            ratios.append((block[2] - block[0]) / pw)
        if not ratios:
            return 1.0
        ratios.sort()
        return ratios[len(ratios) // 2]
    finally:
        doc.close()


@pytest.mark.parametrize("manifest_path", MANIFESTS, ids=lambda p: p.stem)
def test_manifest_pdf_structure(manifest_path: Path, tmp_path: Path):
    manifest = _load_manifest(manifest_path)
    builder_name = manifest["builder"]
    assert builder_name in BUILDERS, builder_name
    expected = manifest["expected"]

    pdf_path = tmp_path / f"{manifest['id']}.pdf"
    BUILDERS[builder_name](pdf_path)

    doc = read_pdf(str(pdf_path), allowed_roots=[str(tmp_path)])
    layer = TextLayer(expected["text_layer"])
    assert doc.text_layer is layer
    assert doc.page_count >= expected.get("min_pages", 1)
    assert doc.total_words >= expected.get("min_total_words", 0)
    if "max_total_words" in expected:
        assert doc.total_words <= expected["max_total_words"]

    full = doc.full_text
    for needle in expected.get("contains", []):
        assert needle in full, f"missing {needle!r} in {manifest['id']}"

    if "cover_page_max_words" in expected:
        assert doc.pages[0].word_count <= expected["cover_page_max_words"]

    if expected.get("twocolumn_body"):
        # Body page (0): median text block should be clearly less than full width
        ratio = _median_text_block_width_ratio(pdf_path, page_index=0)
        assert ratio < 0.75, f"expected two-column-ish blocks, got ratio={ratio}"

    if "min_reference_lines" in expected:
        # Count non-empty lines after the References heading
        after = full.split("References", 1)[-1]
        lines = [ln.strip() for ln in after.splitlines() if ln.strip()]
        assert len(lines) >= expected["min_reference_lines"]


def test_builders_registered():
    assert set(BUILDERS) >= {
        "make_public_dialogue_report",
        "make_pmlr_twocolumn",
        "make_scan_like",
    }
