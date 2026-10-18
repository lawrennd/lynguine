"""Tests for form_fields engine + cam_panel_application.v1 YAML strategy."""

from __future__ import annotations

from pathlib import Path

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
from lynguine.assess.compute import Compute
from lynguine.access.documents.engines import get_engine
from lynguine.access.documents.strategies.loader import (
    load_strategy_yaml,
    parse_strategy_yaml,
)
from lynguine.tests.fixtures.documents.builders import make_cam_panel_application


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
