"""Tests for CIP-0013 body_chunks chrome filters."""

from __future__ import annotations

import pytest

fitz = pytest.importorskip("fitz")

from lynguine.access.documents import (
    DocumentSegmentError,
    apply_chrome_filters,
    is_toc_like,
    resolve_chrome_filter_flags,
    segment_pdf,
    strip_running_chrome,
)
from lynguine.access.documents.unit import Unit
from lynguine.tests.fixtures.documents.builders import make_public_dialogue_report


def _unit(text: str, idx: int = 0) -> Unit:
    return Unit(
        unit_id=f"doc::c{idx:04d}",
        text=text,
        segment_strategy="pub_dialogue.v1",
        aspect="body_chunks",
        chunk_index=idx,
        word_count=len(text.split()),
        chunking_method="paragraph",
        was_truncated=False,
        source_path="doc.pdf",
        extras={},
    )


def _para(n: int = 45, prefix: str = "Word") -> str:
    return " ".join(f"{prefix}{i}" for i in range(n))


FOOTER = (
    "16-005670-01 Final | Public | This work was carried out in accordance with "
    "the requirements of the international quality standard for Market Research, "
    "ISO 20252:2012, and with the Ipsos MORI Terms and Conditions which can be "
    "found at http://www.ipsos-mori.com/terms. © Royal Society 2017"
)


def test_resolve_filter_chrome_enables_all():
    flags = resolve_chrome_filter_flags(filter_chrome=True)
    assert flags == {
        "drop_duplicate_footers": True,
        "strip_running_headers": True,
        "skip_toc": True,
    }


def test_resolve_per_flag_override():
    flags = resolve_chrome_filter_flags(
        filter_chrome=True,
        skip_toc=False,
    )
    assert flags["skip_toc"] is False
    assert flags["drop_duplicate_footers"] is True


def test_parity_default_leaves_units_untouched():
    units = [_unit(FOOTER, 0), _unit(_para(), 1)]
    out = apply_chrome_filters(units)
    assert out is units or out == units
    assert len(out) == 2
    assert "chrome_filters" not in (out[0].extras or {})


def test_drop_duplicate_footers():
    units = [_unit(FOOTER, i) for i in range(4)] + [_unit(_para() + " unique body.", 4)]
    out = apply_chrome_filters(units, drop_duplicate_footers=True, min_footer_repeats=3)
    assert len(out) == 1
    assert "unique body" in out[0].text
    assert out[0].extras["chrome_filters"]["drop_duplicate_footers"] is True
    assert out[0].chunk_index == 0


def test_strip_running_headers():
    raw = (
        f"25/06/2025, 15:22 Licence to build Page 3 of 41 "
        f"https://www.adalovelaceinstitute.org/policy-briefing/x {_para(50)}"
    )
    cleaned, reasons = strip_running_chrome(raw)
    assert "Page 3 of 41" not in cleaned
    assert "https://" not in cleaned
    assert "25/06/2025" not in cleaned
    assert set(reasons) >= {"page_of", "url", "print_timestamp"}

    units = [_unit(raw)]
    out = apply_chrome_filters(units, strip_running_headers=True)
    assert len(out) == 1
    assert "Page 3 of 41" not in out[0].text
    assert "chrome_stripped" in out[0].extras


def test_strip_drops_unit_when_only_chrome_remains():
    # Almost entirely page/url chrome; after strip, below word floor
    chrome_only = _unit(
        "Page 1 of 41 https://example.org/a https://example.org/b "
        "25/06/2025, 15:22 short remnant words here",
        0,
    )
    out = apply_chrome_filters(
        [chrome_only],
        strip_running_headers=True,
        min_chunk_words=40,
        min_chunk_chars=80,
        empty_after_filter="empty",
    )
    assert out == []


def test_is_toc_like():
    toc = (
        "Contents 1 Executive summary ................ 1 "
        "1.1 Background .............................. 2 "
        "2 Introduction ............................. 5 "
        "3 Findings ................................. 12"
    )
    assert is_toc_like(toc)
    body = (
        "→ Energy and net zero: Make Britain a clean energy superpower "
        "to cut bills, create jobs and deliver security with cheaper "
        "zero-carbon electricity by 2030, accelerating to net zero. "
        + _para(20)
    )
    assert not is_toc_like(body)


def test_skip_toc_units():
    toc = (
        "Contents 1 Executive summary ................ 1 "
        "1.1 Background .............................. 2 "
        "2 Introduction ............................. 5 "
        "3 Findings ................................. 12 "
        + _para(10)
    )
    body = _para(50) + " Participants discussed accountability in local services."
    out = apply_chrome_filters(
        [_unit(toc, 0), _unit(body, 1)],
        skip_toc=True,
    )
    assert len(out) == 1
    assert "accountability" in out[0].text


def test_empty_after_filter_errors():
    units = [_unit(FOOTER, i) for i in range(4)]
    with pytest.raises(DocumentSegmentError, match="removed all"):
        apply_chrome_filters(units, drop_duplicate_footers=True, min_footer_repeats=3)


def test_filter_chrome_on_realish_pdf(tmp_path):
    """Plant footer repeats + TOC in a multi-page PDF and filter."""
    pdf = tmp_path / "chrome.pdf"
    doc = fitz.open()

    cover = doc.new_page()
    cover.insert_textbox(
        fitz.Rect(72, 72, 520, 400),
        "Contents\n"
        "1 Executive summary ........................ 1\n"
        "2 Findings ................................. 5\n"
        "3 Recommendations .......................... 12\n"
        "4 Appendix ................................. 20\n",
        fontsize=11,
    )

    for i in range(4):
        page = doc.new_page()
        page.insert_textbox(
            fitz.Rect(72, 72, 520, 200),
            FOOTER,
            fontsize=9,
        )
        page.insert_textbox(
            fitz.Rect(72, 220, 520, 700),
            f"Page {i+1} of 5 https://example.org/report "
            f"Finding block {i}. {_para(60, prefix=f'Body{i}')}",
            fontsize=11,
        )
    doc.save(pdf)
    doc.close()

    raw = segment_pdf(
        str(pdf),
        strategy="pub_dialogue.v1",
        allowed_roots=[str(tmp_path)],
    )
    filtered = segment_pdf(
        str(pdf),
        strategy="pub_dialogue.v1",
        allowed_roots=[str(tmp_path)],
        filter_chrome=True,
    )
    assert len(filtered) < len(raw)
    footer_left = sum(1 for u in filtered if "ISO 20252" in u.text and u.word_count < 60)
    assert footer_left == 0
    assert all(u.extras.get("chrome_filters", {}).get("applied") for u in filtered)
    assert not any(is_toc_like(u.text) for u in filtered)


def test_parity_still_matches_on_fixture(tmp_path):
    pdf = tmp_path / "report.pdf"
    make_public_dialogue_report(pdf)
    a = segment_pdf(str(pdf), strategy="pub_dialogue.v1", allowed_roots=[str(tmp_path)])
    b = segment_pdf(
        str(pdf),
        strategy="pub_dialogue.v1",
        allowed_roots=[str(tmp_path)],
        filter_chrome=False,
    )
    assert [u.text for u in a] == [u.text for u in b]
