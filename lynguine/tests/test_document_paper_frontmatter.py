"""Tests for paper_frontmatter engine + academic_paper_front.v1 YAML strategy."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import (
    choose_strategy,
    ensure_builtin_strategies,
    extract_paper_frontmatter,
    get_strategy,
    list_strategies,
    read_pdf,
    segment_pdf,
)
from lynguine.access.documents.engines import get_engine
from lynguine.access.documents.engines.paper_frontmatter import (
    extract_frontmatter,
    split_author_names,
)
from lynguine.access.documents.model import Document, Page, TextLayer
from lynguine.access.documents.strategies.loader import load_strategy_yaml
from lynguine.assess.compute import Compute
from lynguine.tests.fixtures.documents.builders import (
    make_academic_paper_front,
    make_academic_paper_three_authors,
    make_pmlr_twocolumn,
)


@pytest.fixture(autouse=True)
def _builtin_strategies():
    ensure_builtin_strategies()


def test_academic_paper_yaml_strategy_registered():
    assert "academic_paper_front.v1" in list_strategies(aspect="paper_frontmatter")
    strat = get_strategy("academic_paper_front.v1")
    assert strat.engine == "paper_frontmatter"
    assert "paper_frontmatter" in strat.aspects


def test_paper_frontmatter_engine_registered():
    eng = get_engine("paper_frontmatter")
    assert eng.name == "paper_frontmatter"


def test_segment_academic_paper_title_and_authors(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_academic_paper_front(pdf)

    units = segment_pdf(
        str(pdf),
        strategy="academic_paper_front.v1",
        aspect="paper_frontmatter",
        allowed_roots=[str(tmp_path)],
    )
    assert len(units) == 1
    u = units[0]
    assert u.aspect == "paper_frontmatter"
    assert u.segment_strategy == "academic_paper_front.v1"
    assert u.extras["segment_engine"] == "paper_frontmatter"
    assert u.extras["title"] == (
        "A Synthetic Study of Document Front-Matter Extraction"
    )
    assert u.extras["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert "Ada Lovelace" in (u.extras["authors_raw"] or "")
    assert "ada.lovelace@example.com" in u.extras["emails"]


def test_extract_paper_frontmatter_helper(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_academic_paper_front(pdf)
    fields = extract_paper_frontmatter(
        str(pdf),
        strategy="academic_paper_front.v1",
        root=str(tmp_path),
    )
    assert fields["title"].startswith("A Synthetic Study")
    assert fields["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert fields["segment_strategy"] == "academic_paper_front.v1"
    assert fields["segment_engine"] == "paper_frontmatter"


def test_three_authors_comma_and(tmp_path):
    pdf = tmp_path / "three.pdf"
    make_academic_paper_three_authors(pdf)
    fields = extract_paper_frontmatter(
        str(pdf),
        strategy="academic_paper_front.v1",
        root=str(tmp_path),
    )
    assert fields["authors"] == [
        "Grace Hopper",
        "Katherine Johnson",
        "Margaret Hamilton",
    ]


def test_recogniser_auto_picks_academic_paper(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_academic_paper_front(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    choice = choose_strategy(doc, aspect="paper_frontmatter", strategy="auto")
    assert choice.strategy_id == "academic_paper_front.v1"
    assert choice.score > 0


def test_pmlr_like_fixture_extracts_title_authors(tmp_path):
    pdf = tmp_path / "pmlr.pdf"
    make_pmlr_twocolumn(pdf)
    fields = extract_paper_frontmatter(
        str(pdf),
        strategy="academic_paper_front.v1",
        root=str(tmp_path),
    )
    assert "Synthetic Proceedings Paper Title" in (fields.get("title") or "")
    assert "A. Author" in fields.get("authors", [])
    assert "B. Writer" in fields.get("authors", [])


def test_packaged_yaml_roundtrip_loads():
    yml = (
        Path(__file__).resolve().parents[1]
        / "access"
        / "documents"
        / "strategies"
        / "academic_paper_front.v1.yml"
    )
    assert yml.is_file()
    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    assert data["id"] == "academic_paper_front.v1"
    strat = load_strategy_yaml(yml)
    assert strat.id == data["id"]
    assert strat.engine == "paper_frontmatter"


def test_extract_paper_frontmatter_in_compute_registry():
    names = [f["name"] for f in Compute({})._compute_functions_list()]
    assert "extract_paper_frontmatter" in names


def test_split_author_names_variants():
    assert split_author_names("Ada Lovelace and Alan Turing") == [
        "Ada Lovelace",
        "Alan Turing",
    ]
    assert split_author_names("A, B, and C") == ["A", "B", "C"]
    assert split_author_names("") == []


def test_extract_frontmatter_empty_document():
    doc = Document(
        path="empty.pdf",
        reader="pdf",
        page_count=1,
        total_words=0,
        words_per_page=0.0,
        text_layer=TextLayer.ABSENT,
        pages=(
            Page(index=0, width=100, height=100, text="", word_count=0, blocks=()),
        ),
    )
    fields = extract_frontmatter(doc, {})
    assert fields["title"] is None
    assert fields["authors"] == []
