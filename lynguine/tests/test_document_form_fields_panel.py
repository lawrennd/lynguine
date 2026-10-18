"""Tests for form_fields engine + cam_panel_application.v1 YAML strategy."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import (
    DocumentSegmentError,
    choose_strategy,
    ensure_builtin_strategies,
    extract_form_fields,
    get_strategy,
    list_strategies,
    read_pdf,
    segment_document,
    segment_pdf,
)
from lynguine.access.documents.engines import ensure_builtin_engines, get_engine
from lynguine.access.documents.engines.form_fields import (
    _norm_person_case,
    _parse_start_date,
    _to_iso_date,
    parse_contact,
    parse_header,
    parse_name_from_page0,
)
from lynguine.access.documents.model import Document, TextLayer
from lynguine.access.documents.recogniser import _yaml_recogniser_boost
from lynguine.access.documents.strategies.loader import (
    StrategySpec,
    YamlStrategy,
    load_strategy_yaml,
    parse_strategy_yaml,
)
from lynguine.assess.compute import Compute
from lynguine.tests.fixtures.documents.builders import (
    make_cam_panel_application,
    make_scan_like,
)


@pytest.fixture(autouse=True)
def _builtin_strategies():
    ensure_builtin_strategies()


def test_cam_panel_yaml_strategy_registered():
    assert "cam_panel_application.v1" in list_strategies(aspect="form_fields")
    strat = get_strategy("cam_panel_application.v1")
    assert strat.engine == "form_fields"
    assert "form_fields" in strat.aspects


def test_form_fields_engine_registered():
    eng = get_engine("form_fields")
    assert eng.name == "form_fields"


def test_unknown_engine_errors_clearly():
    with pytest.raises(DocumentSegmentError, match="Unknown segment engine"):
        get_engine("no_such_engine")


def test_invalid_strategy_yaml_missing_keys(tmp_path):
    bad = tmp_path / "bad.v1.yml"
    bad.write_text("id: bad.v1\naspects: [form_fields]\n", encoding="utf-8")
    with pytest.raises(DocumentSegmentError, match="missing required keys"):
        load_strategy_yaml(bad)


def test_parse_strategy_yaml_rejects_non_mapping():
    with pytest.raises(DocumentSegmentError, match="non-empty"):
        parse_strategy_yaml(
            {"id": "x", "aspects": [], "engine": "form_fields"},
            source_path="x.yml",
        )


def test_segment_cam_panel_header_and_contact(tmp_path):
    pdf = tmp_path / "panel.pdf"
    make_cam_panel_application(pdf)

    units = segment_pdf(
        str(pdf),
        strategy="cam_panel_application.v1",
        aspect="form_fields",
        allowed_roots=[str(tmp_path)],
    )
    assert len(units) == 1
    u = units[0]
    assert u.aspect == "form_fields"
    assert u.segment_strategy == "cam_panel_application.v1"
    assert u.extras["segment_engine"] == "form_fields"
    assert u.extras["family"] == "Smith"
    assert u.extras["given"] == "Jane Ann"
    assert u.extras["title"] == "Ms"
    assert u.extras["application_number"] == "90000001"
    assert u.extras["usn"] == "90000002"
    assert u.extras["award"] == "PhD"
    assert "Synthetic Computing" in (u.extras["course_title"] or "")
    assert u.extras["date_submitted"] == "2026-09-21"
    assert u.extras["course_start_date"] == "2027-10-04"
    assert u.extras["course_start_term"] == "MT 2027"
    assert u.extras["email"] == "jane.ann.smith@example.com"
    assert "1 Synthetic Street" in (u.extras["contact_address"] or "")
    assert "referee.one@university.example" in u.extras["emails_referee"]
    assert u.extras["email"] not in u.extras["emails_referee"]
    assert u.extras["email_ambiguous"] is False


def test_extract_form_fields_helper(tmp_path):
    pdf = tmp_path / "panel.pdf"
    make_cam_panel_application(pdf)
    fields = extract_form_fields(
        str(pdf),
        strategy="cam_panel_application.v1",
        root=str(tmp_path),
    )
    assert fields["email"] == "jane.ann.smith@example.com"
    assert fields["segment_strategy"] == "cam_panel_application.v1"
    assert fields["segment_engine"] == "form_fields"
    assert fields["usn"] == "90000002"


def test_recogniser_auto_picks_cam_panel(tmp_path):
    pdf = tmp_path / "panel.pdf"
    make_cam_panel_application(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    choice = choose_strategy(doc, aspect="form_fields", strategy="auto")
    assert choice.strategy_id == "cam_panel_application.v1"
    assert choice.score > 0
    assert "page0" in choice.rationale

    units = segment_document(doc, strategy="auto", aspect="form_fields")
    assert units[0].segment_strategy == "cam_panel_application.v1"


def test_packaged_yaml_roundtrip_loads():
    yml = (
        Path(__file__).resolve().parents[1]
        / "access"
        / "documents"
        / "strategies"
        / "cam_panel_application.v1.yml"
    )
    assert yml.is_file()
    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    assert data["id"] == "cam_panel_application.v1"
    strat = load_strategy_yaml(yml)
    assert strat.id == data["id"]
    assert strat.engine == "form_fields"


def test_extract_form_fields_in_compute_registry():
    names = [f["name"] for f in Compute({})._compute_functions_list()]
    assert "extract_form_fields" in names
    assert "document_segment" in names


# --- Edge / branch coverage for Codecov patch gaps ---


def test_norm_person_case_and_dates():
    assert _norm_person_case("") == ""
    assert _norm_person_case("SMITH") == "Smith"
    assert _norm_person_case("Jane ANN") == "Jane Ann"
    assert _norm_person_case("McDonald") == "McDonald"
    aliases = {"sept": "Sep"}
    assert _to_iso_date(None, aliases) is None
    assert _to_iso_date("not-a-date", aliases) is None
    assert _to_iso_date("21 Sept 2026", aliases) == "2026-09-21"
    assert _to_iso_date("32 Foo 2026", aliases) is None  # invalid day/month
    empty = _parse_start_date(None, aliases)
    assert empty["course_start_date"] is None
    assert empty["course_start_term"] is None
    start = _parse_start_date("04 Oct 2027 (LT 2027)", aliases)
    assert start["course_start_date"] == "2027-10-04"
    assert start["course_start_term"] == "LT 2027"


def test_parse_name_skips_course_false_positive():
    import re

    page0 = "Bloggs, Dr PhD in Computing\nSMITH, Ms Jane ANN\n"
    name = parse_name_from_page0(page0, re.compile(
        r"^(?P<family>[A-Za-z][A-Za-z' -]+),\s*"
        r"(?P<title>Mr|Ms|Mrs|Miss|Mx|Dr)\s+"
        r"(?P<given>.+)$"
    ))
    assert name["name_parse_ok"] is True
    assert name["family"] == "Smith"
    none = parse_name_from_page0("no name here", re.compile(
        r"^(?P<family>[A-Za-z]+),\s*(?P<title>Ms)\s+(?P<given>.+)$"
    ))
    assert none["name_parse_ok"] is False


def test_parse_header_strips_term_from_course_title():
    page0 = "\n".join(
        [
            "SMITH, Ms Jane ANN",
            "Application Number: 1",
            "USN: 2",
            "MPhil in Widgets, Michaelmas Term 2027 Course",
            "Date submitted 13 Oct 2026",
            "Mode of study Full-time",
            "Course start date 04 Oct 2027 (MT 2027)",
            "Nationality United Kingdom",
            "Estimated fee status Home",
        ]
    )
    header = parse_header(page0, {"month_aliases": {"sept": "Sep"}})
    assert header["award"] == "MPhil"
    assert "Michaelmas" not in (header["course_title"] or "")
    assert header["date_submitted"] == "2026-10-13"


def test_parse_contact_email_next_line_and_ambiguous():
    # Prefixed prose on the next line so the same-line Email regex cannot span
    # newlines and the Email-then-next-line branch runs.
    text = "\n".join(
        [
            "Personal Information",
            "Contact",
            "Email",
            "primary candidate@example.com",
            "Contact address 9 Test Road",
            "",
            "continued after blank",
            "Phone 000",
            "Referee Details",
            "Email ref@example.com",
            "Curriculum Vitae",
            "Email leftover@example.com",
        ]
    )
    contact = parse_contact(text, {})
    assert contact["email"] == "candidate@example.com"
    assert "ref@example.com" in contact["emails_referee"]
    assert contact["email"] not in contact["emails_referee"]
    assert "9 Test Road" in (contact["contact_address"] or "")
    assert "continued after blank" not in (contact["contact_address"] or "")

    ambiguous = "\n".join(
        [
            "Personal Information",
            "Contact",
            "Email first@example.com",
            "also second@example.com",
            "Contact address Somewhere",
            "Phone 000",
            "Referee Details",
            "Email ref@example.com",
        ]
    )
    amb = parse_contact(ambiguous, {})
    assert amb["email_ambiguous"] is True


def test_parse_header_custom_patterns_and_referee_trim():
    page0 = "\n".join(
        [
            "DOE, Dr Ada",
            "Application Number: 3",
            "USN: 4",
            "MPhil in Custom Course Title (CC1)",
            "Date submitted 01 June 2026",
            "Mode of study Part-time",
            "Course start date 01 Oct 2026 (ET 2026)",
            "Nationality Testland",
            "Estimated fee status Overseas",
        ]
    )
    header = parse_header(
        page0,
        {
            "month_aliases": {"june": "Jun"},
            "name_line_pattern": (
                r"^(?P<family>[A-Za-z]+),\s*(?P<title>Dr)\s+(?P<given>.+)$"
            ),
            "course_pattern": (
                r"(?P<award>MPhil|PhD)\s+in\s+(?P<title>.+?)"
                r"(?:\s*\((?P<code>[A-Z0-9]+)\))?\s*$"
            ),
        },
    )
    assert header["family"] == "Doe"
    assert header["given"] == "Ada"
    assert header["course_code"] == "CC1"
    assert header["date_submitted"] == "2026-06-01"
    assert header["course_start_term"] == "ET 2026"

    # Referee block truncated when a CV heading appears inside it
    text = "\n".join(
        [
            "Personal Information",
            "Contact",
            "Email sole@example.com",
            "Contact address Flat 1",
            "Phone 1",
            "Referee Details",
            "Email keep@example.com",
            "Curriculum Vitae",
            "Email drop@example.com",
            "Referee Details",
            "Email other@example.com",
            "Academic History",
            "Email drop2@example.com",
        ]
    )
    contact = parse_contact(text, {})
    assert "keep@example.com" in contact["emails_referee"]
    assert "other@example.com" in contact["emails_referee"]
    assert "drop@example.com" not in contact["emails_referee"]
    assert "drop2@example.com" not in contact["emails_referee"]


def test_parse_contact_fallback_email_and_address_stops_on_email():
    text = "\n".join(
        [
            "Personal Information",
            "Contact",
            "Contact address Line One",
            "extra@example.com",
            "should-not-appear",
            "Phone 000",
            "Referee Details",
        ]
    )
    contact = parse_contact(text, {})
    assert contact["email"] == "extra@example.com"
    assert contact["contact_address"] == "Line One"


def test_parse_contact_without_personal_section_uses_full_text():
    text = "\n".join(
        [
            "Contact",
            "Email alone@example.com",
            "Contact address Only Place",
            "Phone 1",
        ]
    )
    contact = parse_contact(text, {})
    assert contact["email"] == "alone@example.com"
    assert "Only Place" in (contact["contact_address"] or "")


def test_parse_contact_trims_referee_inside_wide_personal_region():
    # personal_end omits Referee so the inner truncate branch runs
    text = "\n".join(
        [
            "Personal Information",
            "Contact",
            "Email wide@example.com",
            "Contact address Road",
            "Phone 1",
            "Referee Details",
            "Email should-not-be-candidate@example.com",
            "Research",
        ]
    )
    contact = parse_contact(
        text,
        {
            "contact": {
                "personal_end": [r"^Research\s*$"],
            }
        },
    )
    assert contact["email"] == "wide@example.com"
    assert contact["email"] != "should-not-be-candidate@example.com"


def test_yaml_recogniser_partial_miss_and_wrong_aspect():
    feats = {
        "page0_text": "Application Number: 1\n",
        "reader": "pdf",
        "text_layer": "present",
    }
    partial = _yaml_recogniser_boost(
        "cam_panel_application.v1", "form_fields", feats
    )
    assert partial is not None
    assert partial.score > 0
    assert "partial" in partial.rationale

    miss = _yaml_recogniser_boost(
        "cam_panel_application.v1",
        "form_fields",
        {"page0_text": "unrelated", "reader": "pdf", "text_layer": "present"},
    )
    assert miss is not None
    assert miss.score == 0
    assert "no boost" in miss.rationale or "missing" in miss.rationale

    wrong = _yaml_recogniser_boost(
        "cam_panel_application.v1", "body_chunks", feats
    )
    assert wrong is not None
    assert wrong.score == 0
    assert "aspect not declared" in wrong.rationale

    assert _yaml_recogniser_boost("no.such.strategy", "form_fields", feats) is None


def test_yaml_recogniser_empty_cfg_returns_none():
    spec = StrategySpec(
        id="tmp.empty.v1",
        aspects=("form_fields",),
        engine="form_fields",
        grain="one_record_per_document",
        recogniser={},
        params={},
        source_path="tmp.yml",
    )
    strat = YamlStrategy(spec)
    with patch(
        "lynguine.access.documents.strategy.get_strategy", return_value=strat
    ):
        assert (
            _yaml_recogniser_boost(
                "tmp.empty.v1",
                "form_fields",
                {"page0_text": "x", "reader": "pdf"},
            )
            is None
        )


def test_loader_errors_oserror_yamlerror_non_dict(tmp_path):
    missing = tmp_path / "missing.yml"
    with pytest.raises(DocumentSegmentError, match="Cannot read"):
        load_strategy_yaml(missing)

    bad = tmp_path / "bad.yml"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(DocumentSegmentError, match="Invalid strategy YAML"):
        load_strategy_yaml(bad)

    not_map = tmp_path / "list.yml"
    not_map.write_text("- just a list\n", encoding="utf-8")
    with pytest.raises(DocumentSegmentError, match="mapping at the top level"):
        load_strategy_yaml(not_map)

    spec = parse_strategy_yaml(
        {
            "id": "string.aspects.v1",
            "aspects": "form_fields",
            "engine": "form_fields",
            "grain": "one_record_per_document",
        },
        source_path="x.yml",
    )
    assert spec.aspects == ("form_fields",)
    assert spec.grain == "one_record_per_document"


def test_extract_form_fields_empty_on_sparse(tmp_path):
    pdf = tmp_path / "scan.pdf"
    make_scan_like(pdf)
    fields = extract_form_fields(
        str(pdf),
        strategy="cam_panel_application.v1",
        root=str(tmp_path),
        on_sparse_text="empty",
    )
    assert fields == {}


def test_extract_form_fields_flat_extras_unwrap():
    flat_unit = {
        "unit_id": "x::form0",
        "text": "Smith",
        "segment_strategy": "cam_panel_application.v1",
        "aspect": "form_fields",
        "chunk_index": 0,
        "word_count": 1,
        "chunking_method": "form_fields",
        "was_truncated": False,
        "source_path": "x.pdf",
        "family": "Smith",
        "email": "flat@example.com",
        "segment_engine": "form_fields",
        "recogniser_score": 0.9,
        "recogniser_rationale": "test",
    }
    with patch(
        "lynguine.access.documents.segment.document_segment",
        return_value=[flat_unit],
    ):
        fields = extract_form_fields("x.pdf", strategy="cam_panel_application.v1")
    assert fields["family"] == "Smith"
    assert fields["email"] == "flat@example.com"
    assert fields["segment_strategy"] == "cam_panel_application.v1"
    assert fields["segment_engine"] == "form_fields"
    assert fields["recogniser_score"] == 0.9
    assert fields["recogniser_rationale"] == "test"
    assert "unit_id" not in fields


def test_ensure_builtin_engines_idempotent():
    ensure_builtin_engines()
    ensure_builtin_engines()
    assert get_engine("form_fields").name == "form_fields"


def test_form_fields_engine_empty_document():
    doc = Document(
        path="empty.pdf",
        reader="pdf",
        page_count=0,
        total_words=0,
        words_per_page=0.0,
        text_layer=TextLayer.PRESENT,
        pages=(),
    )
    units = get_engine("form_fields").run(
        doc,
        {},
        strategy_id="cam_panel_application.v1",
        aspects=("form_fields",),
    )
    assert len(units) == 1
    assert units[0].extras["family"] is None
    assert units[0].extras["email"] is None
