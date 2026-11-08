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
    is_publisher_front_matter,
    parse_publisher_front_matter,
    split_author_names,
    strip_leading_publisher_front_matter,
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
    assert fields["journal"] is None
    assert fields["publisher_front_matter_lines"] == []


def _doc_from_text(text: str, path: str = "synthetic.pdf") -> Document:
    words = len(text.split())
    return Document(
        path=path,
        reader="pdf",
        page_count=1,
        total_words=words,
        words_per_page=float(words),
        text_layer=TextLayer.PRESENT,
        pages=(
            Page(
                index=0,
                width=612,
                height=792,
                text=text,
                word_count=words,
                blocks=(),
            ),
        ),
    )


def test_ieee_header_and_page_number_skipped():
    text = "\n".join(
        [
            "IEEE TRANSACTIONS ON AFFECTIVE COMPUTING, VOL. 14, NO. 8, AUGUST 2015",
            "1",
            "Learning Person-specific Cognition from Facial",
            "Reactions for Automatic Personality Recognition",
            "Siyang Song, Zilong Shao, Shashank Jaiswal, Linlin Shen, Michel Valstar and Hatice Gunes",
            "Abstract—This paper proposes to recognise personality traits.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert fields["title"] == (
        "Learning Person-specific Cognition from Facial "
        "Reactions for Automatic Personality Recognition"
    )
    assert fields["authors"] == [
        "Siyang Song",
        "Zilong Shao",
        "Shashank Jaiswal",
        "Linlin Shen",
        "Michel Valstar",
        "Hatice Gunes",
    ]
    assert fields["journal"].startswith("IEEE TRANSACTIONS")
    assert fields["volume"] == "14"
    assert fields["number"] == "8"
    assert fields["year"] == "2015"
    assert "1" in fields["publisher_front_matter_lines"]


def test_acm_name_university_author_lines():
    text = "\n".join(
        [
            "DeliData: A dataset for deliberation in multi-party problem solving",
            "GEORGI KARADZHOV, University of Cambridge, United Kingdom",
            "TOM STAFFORD, University of Sheffield, United Kingdom",
            "ANDREAS VLACHOS, University of Cambridge, United Kingdom",
            "Group deliberation enables people to collaborate and solve problems, however, "
            "it is understudied due to a lack of resources. To this end, we introduce "
            "the first publicly available dataset.",
            "CCS Concepts: • Human-centered computing",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert fields["title"].startswith("DeliData:")
    assert fields["authors"] == [
        "Georgi Karadzhov",
        "Tom Stafford",
        "Andreas Vlachos",
    ]


def test_nature_mi_running_header_and_multiline_authors():
    text = "\n".join(
        [
            "Nature Machine Intelligence | Volume 5 | July 2023 | 739–753",
            "739",
            "nature machine intelligence",
            "https://doi.org/10.1038/s42256-023-00684-8",
            "Article",
            "Hypergraph factorization for multi-tissue",
            "gene expression imputation",
            "Ramon Viñas 1, Chaitanya K. Joshi1, Dobrik Georgiev 1, Phillip Lin,",
            "Bianca Dumitrascu 3, Eric R. Gamazon 4 & Pietro Liò 1",
            "Integrating gene expression across tissues and cell types is crucial for "
            "understanding the coordinated biological mechanisms that drive disease.",
            "Abstract",
            "We present HYFA for joint imputation.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert "Hypergraph factorization" in (fields["title"] or "")
    assert "gene expression imputation" in (fields["title"] or "")
    assert "Ramon Viñas" in fields["authors"]
    assert "Pietro Liò" in fields["authors"]
    assert not any("Integrating gene" in a for a in fields["authors"])
    assert fields["doi"] == "10.1038/s42256-023-00684-8"
    assert fields["journal"] == "nature machine intelligence"
    assert any("Volume 5" in ln for ln in fields["publisher_front_matter_lines"])


def test_nature_equal_contribution_image_title():
    text = "\n".join(
        [
            "Articles",
            "https://doi.org/10.1038/s41593-022-01026-4",
            "1Department of Psychology and the Neuroscience Institute, Princeton University, Princeton, NJ, USA. "
            "2Google Research, Mountain View, CA, USA.",
            "8These authors contributed equally: Zaid Zada, Eliav Buchnik, Mariano Schain, "
            "Amy Price, Bobbi Aubrey, Samuel A. Nastase, Amir Feder, Dotan Emanuel, "
            "Alon Cohen, Aren Jansen.",
            "✉e-mail: ariel.y.goldstein@gmail.com",
            "T",
            "he outstanding success of autoregressive (predictive) DLMs is striking.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    # Title may be absent when rendered as an image in the real PDF
    assert "Zaid Zada" in fields["authors"]
    assert "Aren Jansen" in fields["authors"]
    assert "ariel.y.goldstein@gmail.com" in fields["emails"]


def test_publisher_front_matter_tagger():
    assert is_publisher_front_matter(
        "Neurocomputing 275 (2018) 2251–2263 Neurocomputing"
    )
    assert is_publisher_front_matter(
        "IEEE TRANSACTIONS ON AFFECTIVE COMPUTING, VOL. 14, NO. 8, AUGUST 2015"
    )
    assert is_publisher_front_matter("Skip to MainContent • IEEE.org")
    assert not is_publisher_front_matter(
        "Learning Person-specific Cognition from Facial Reactions"
    )


def test_header_before_title_on_separate_lines():
    text = "\n".join(
        [
            "Neurocomputing 275 (2018) 2251–2263 Neurocomputing",
            "A dynamic colour perception system for autonomous robot navigation",
            "Ada Lovelace and Alan Turing",
            "University of Example",
            "Abstract",
            "We describe a synthetic navigation fixture.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert fields["title"] == (
        "A dynamic colour perception system for autonomous robot navigation"
    )
    assert fields["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert fields["journal"] == "Neurocomputing"
    assert fields["volume"] == "275"
    assert fields["year"] == "2018"
    assert fields["pages"] == "2251--2263"
    assert fields["publisher_front_matter_lines"][0].startswith("Neurocomputing 275")


def test_header_glued_before_title_same_line():
    text = "\n".join(
        [
            "IEEE JOURNAL OF BIOMEDICAL AND HEALTH INFORMATICS, VOL. 22, NO. 4, "
            "JULY 2018 Automated Breast Ultrasound Lesions Detection Using CNNs",
            "Ada Lovelace, Alan Turing",
            "Abstract",
            "Synthetic abstract text for the fixture.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert "Automated Breast Ultrasound" in (fields["title"] or "")
    assert "Ada Lovelace" in fields["authors"]
    assert fields["journal"] and "BIOMEDICAL" in fields["journal"].upper()
    assert fields["volume"] == "22"
    assert fields["number"] == "4"
    assert fields["year"] == "2018"
    assert any("VOL. 22" in ln for ln in fields["publisher_front_matter_lines"])


def test_header_only_page_yields_empty_title():
    text = "\n".join(
        [
            "Applied Soft Computing Journal 91 (2020) 106230 Applied Soft Computing Journal",
            "Contents lists available at ScienceDirect",
            "https://doi.org/10.1016/j.asoc.2020.106230",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert fields["title"] is None
    assert fields["journal"] and "Soft Computing" in fields["journal"]
    assert fields["volume"] == "91"
    assert fields["year"] == "2020"
    assert fields["doi"] == "10.1016/j.asoc.2020.106230"
    assert len(fields["publisher_front_matter_lines"]) >= 2


def test_clean_manuscript_without_publisher_lines():
    text = "\n".join(
        [
            "A Synthetic Study of Document Front-Matter Extraction",
            "Ada Lovelace and Alan Turing",
            "University of Example",
            "Abstract",
            "We describe a synthetic fixture used only for layout tests.",
        ]
    )
    fields = extract_frontmatter(_doc_from_text(text), {})
    assert fields["title"].startswith("A Synthetic Study")
    assert fields["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert fields["journal"] is None
    assert fields["volume"] is None
    assert fields["number"] is None
    assert fields["pages"] is None
    assert fields["year"] is None
    assert fields["doi"] is None
    assert fields["publisher_front_matter_lines"] == []


def test_strip_leading_publisher_front_matter_helpers():
    assert strip_leading_publisher_front_matter(
        "Neurocomputing 275 (2018) 2251–2263 Neurocomputing"
    ) is None
    rest = strip_leading_publisher_front_matter(
        "IEEE JOURNAL OF BIOMEDICAL AND HEALTH INFORMATICS, VOL. 22, NO. 4, "
        "JULY 2018 Automated Breast Ultrasound Lesions Detection Using CNNs"
    )
    assert rest is not None
    assert rest.startswith("Automated Breast")


def test_parse_publisher_front_matter_first_wins():
    parsed = parse_publisher_front_matter(
        [
            "IEEE TRANSACTIONS ON AFFECTIVE COMPUTING, VOL. 14, NO. 8, AUGUST 2015",
            "Neurocomputing 275 (2018) 2251–2263 Neurocomputing",
            "https://doi.org/10.1016/j.neucom.2017.10.001",
            "Skip to MainContent",
        ]
    )
    assert parsed["journal"].startswith("IEEE TRANSACTIONS")
    assert parsed["volume"] == "14"
    assert parsed["number"] == "8"
    assert parsed["year"] == "2015"
    assert parsed["doi"] == "10.1016/j.neucom.2017.10.001"
    # First line wins journal/volume; pages still fill from a later line.
    assert parsed["pages"] == "2251--2263"
    assert "Skip to MainContent" in parsed["publisher_front_matter_lines"]


def test_publisher_front_matter_tagger_edge_cases():
    assert not is_publisher_front_matter("")
    assert not is_publisher_front_matter("   ")
    assert is_publisher_front_matter("42")
    assert is_publisher_front_matter("nature machine intelligence")
    # Pipe + pages without other running-header keywords (hits pipe branch)
    assert is_publisher_front_matter("Venue Name Here | pages 12")
    assert is_publisher_front_matter("Smith, Jones (2020)")
    assert is_publisher_front_matter("† ‡")
    assert is_publisher_front_matter("journal")
    assert is_publisher_front_matter("Original Article")
    assert is_publisher_front_matter("doi: 10.1000/xyz.abc")
    assert is_publisher_front_matter("Applied Soft Computing Journal")


def test_strip_publisher_front_matter_edge_cases():
    assert strip_leading_publisher_front_matter("") is None
    assert strip_leading_publisher_front_matter("   ") is None
    # Pure FM with no title remnant
    assert strip_leading_publisher_front_matter(
        "IEEE TRANSACTIONS ON X, VOL. 1, NO. 2, JANUARY 2020"
    ) is None
    # Remnant that is only a journal name must not become a title
    assert strip_leading_publisher_front_matter(
        "Neurocomputing 275 (2018) 2251–2263 Applied Soft Computing Journal"
    ) is None
    # Clean title passes through
    assert (
        strip_leading_publisher_front_matter("Learning Useful Representations")
        == "Learning Useful Representations"
    )


def test_parse_publisher_front_matter_audit_and_edges():
    empty = parse_publisher_front_matter([])
    assert empty["journal"] is None
    assert empty["publisher_front_matter_lines"] == []

    # Blanks skipped; duplicates collapsed; doi: form; journal-name-only
    parsed = parse_publisher_front_matter(
        [
            "",
            "  ",
            "nature machine intelligence",
            "Nature Machine Intelligence",  # casefold duplicate of audit? different text
            "doi: 10.1038/s42256-023-00684-8).",
            "1",
            "nature machine intelligence",  # exact duplicate
        ]
    )
    assert parsed["journal"] == "nature machine intelligence"
    assert parsed["doi"] == "10.1038/s42256-023-00684-8"
    assert parsed["publisher_front_matter_lines"].count(
        "nature machine intelligence"
    ) == 1
    assert "1" in parsed["publisher_front_matter_lines"]
    # Page marker and web-shell do not invent volume/pages
    assert parsed["volume"] is None
    assert parsed["pages"] is None


def test_parse_doi_only_line_does_not_set_journal():
    parsed = parse_publisher_front_matter(
        ["https://doi.org/10.1016/j.asoc.2020.106230"]
    )
    assert parsed["doi"] == "10.1016/j.asoc.2020.106230"
    assert parsed["journal"] is None


def test_parse_ieee_without_issue_and_repeated_journal_token():
    no_issue = parse_publisher_front_matter(
        ["IEEE TRANSACTIONS ON X, VOL. 3, MARCH 2019"]
    )
    assert no_issue["volume"] == "3"
    assert no_issue["number"] is None
    assert no_issue["year"] == "2019"

    repeated = parse_publisher_front_matter(
        ["Neurocomputing Neurocomputing 275 (2018) 10-20"]
    )
    assert repeated["journal"] == "Neurocomputing"
    assert repeated["volume"] == "275"
    assert repeated["pages"] == "10--20"


def test_extract_helper_exposes_publisher_fields(tmp_path):
    pdf = tmp_path / "paper.pdf"
    make_academic_paper_front(pdf)
    fields = extract_paper_frontmatter(
        str(pdf),
        strategy="academic_paper_front.v1",
        root=str(tmp_path),
    )
    assert "journal" in fields
    assert fields["journal"] is None
    assert fields["publisher_front_matter_lines"] == []


def test_engine_run_extras_include_publisher_fields():
    """Engine.run surfaces structured publisher fields in unit extras."""
    text = "\n".join(
        [
            "IEEE TRANSACTIONS ON AFFECTIVE COMPUTING, VOL. 14, NO. 8, AUGUST 2015",
            "A Synthetic Personality Recognition Study",
            "Ada Lovelace and Alan Turing",
            "Abstract",
            "We describe a synthetic fixture used only for layout tests with enough words.",
        ]
    )
    eng = get_engine("paper_frontmatter")
    units = eng.run(
        _doc_from_text(text, path="ieee_header.pdf"),
        {},
        strategy_id="academic_paper_front.v1",
        aspects=("paper_frontmatter",),
    )
    assert len(units) == 1
    extras = units[0].extras
    assert "Synthetic Personality" in (extras.get("title") or "")
    assert extras.get("volume") == "14"
    assert extras.get("number") == "8"
    assert extras.get("year") == "2015"
    assert extras.get("journal") and "AFFECTIVE" in extras["journal"].upper()
    assert extras.get("publisher_front_matter_lines")
    nested = extras.get("paper_frontmatter") or {}
    assert nested.get("volume") == "14"
