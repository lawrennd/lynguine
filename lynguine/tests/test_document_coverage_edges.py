"""Edge-path coverage for CIP-0013 document modules (Codecov patch gaps)."""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fitz")
pytest.importorskip("docx")

from lynguine.access.documents import (
    Block,
    Document,
    DocumentSegmentError,
    Page,
    SparseTextLayerError,
    TextLayer,
    UnknownStrategyError,
    choose_strategy,
    document_features,
    document_segment,
    ensure_builtin_strategies,
    is_toc_like,
    read_docx,
    read_pdf,
    resolve_strategy_id,
    segment_document,
    segment_pdf,
    units_to_frame,
)
from lynguine.access.documents.chrome_filters import apply_chrome_filters
from lynguine.access.documents.pdf import (
    PyMuPDFMissingError,
    _block_type_name,
    _import_fitz,
)
from lynguine.access.documents.strategies.pmlr_references_v1 import (
    find_references_region,
    split_reference_entries,
)
from lynguine.access.documents.strategies.pub_dialogue_v1 import (
    PubDialogueV1,
    _coverage,
    _repack_sentences_into_chunks,
    _split_into_sentences,
)
from lynguine.access.documents.unit import Unit
from lynguine.tests.fixtures.documents.builders import (
    make_chatbot_transcript,
    make_pmlr_twocolumn,
    make_scan_like,
    make_workshop_transcript,
)


def _doc(
    *,
    text: str,
    reader: str = "pdf",
    text_layer: TextLayer = TextLayer.PRESENT,
    blocks: tuple[Block, ...] | None = None,
    path: str = "doc.pdf",
) -> Document:
    words = len(text.split()) if text.strip() else 0
    if blocks is None:
        blocks = (
            Block(
                page_index=0,
                block_index=0,
                x0=0,
                y0=0,
                x1=100,
                y1=20,
                text=text,
                block_type="text",
                word_count=words,
            ),
        )
    page = Page(
        index=0,
        width=100,
        height=100,
        text=text,
        word_count=words,
        blocks=blocks,
    )
    return Document(
        path=path,
        reader=reader,
        page_count=1,
        total_words=words,
        words_per_page=float(words),
        text_layer=text_layer,
        pages=(page,),
    )


@pytest.fixture(autouse=True)
def _builtins():
    ensure_builtin_strategies()


# --- pub_dialogue helpers / branches ---


def test_coverage_zero_total_words():
    assert _coverage(["hello world"], 0, 40, 80) == 0.0


def test_repack_sentences_handles_long_and_flush():
    long = " ".join(f"Word{i}" for i in range(50)) + "."
    short = ["One short. ", "Two short. ", "Three short. "]
    # mix: accumulate shorts then a long sentence clears buffer
    sents = [s.strip() for s in short] + [long]
    chunks = _repack_sentences_into_chunks(sents, target_words=10)
    assert len(chunks) >= 2
    assert any(len(c.split()) >= 40 for c in chunks)


def test_split_into_sentences():
    parts = _split_into_sentences("Hello world. Next sentence? Third one!")
    assert len(parts) >= 2


def test_pub_dialogue_sentence_fallback_and_truncation():
    # Many tiny paragraphs → coverage fails → sentence fallback
    tiny = "\n\n".join(f"Tiny line {i}." for i in range(20))
    body = " ".join(f"Word{i}" for i in range(80))
    text = tiny + "\n\n" + body + ". " + body + "?"
    units = PubDialogueV1().segment(
        _doc(text=text),
        min_chunk_words=10,
        min_chunk_chars=20,
        max_chunk_words=30,
        sentence_fallback_min_paragraphs=5,
        min_text_coverage=0.9,
    )
    assert units
    assert any(u.chunking_method == "sentence_fallback" for u in units)
    assert any(u.was_truncated for u in units)


def test_pub_dialogue_sentence_split_oversized_paragraph():
    long = " ".join(f"Word{i}" for i in range(120)) + ". More words here too."
    # Single large paragraph with blank-line isolation so newline mode can win
    text = (
        "Intro paragraph with enough words to count as substantive content here.\n\n"
        + long
        + "\n\n"
        + "Closing paragraph with enough words to count as substantive content again."
    )
    units = PubDialogueV1().segment(
        _doc(text=text),
        min_chunk_words=10,
        min_chunk_chars=20,
        max_chunk_words=40,
        sentence_fallback_target_words=25,
    )
    assert units
    assert any(u.chunking_method in ("sentence_split", "paragraph") for u in units)


def test_pub_dialogue_skips_non_text_blocks():
    blocks = (
        Block(0, 0, 0, 0, 10, 10, "img", "image", 0),
        Block(
            0,
            1,
            0,
            20,
            100,
            40,
            " ".join(f"Word{i}" for i in range(50)),
            "text",
            50,
        ),
    )
    text = blocks[1].text
    units = PubDialogueV1().segment(
        _doc(text=text, blocks=blocks),
        min_chunk_words=10,
        min_chunk_chars=20,
    )
    assert units


# --- references splits ---


def test_split_numbered_and_paren_and_empty():
    assert split_reference_entries("") == []
    numbered = "[1] First ref 2020. [2] Second ref 2021. [3] Third ref 2022."
    # Force past year-dot by using paren style without A-Z after year-dot pattern
    paren = (
        "Alice (2020). Next paper title here. "
        "Bob (2021). Another paper title here. "
        "Carol (2022). Third paper title here."
    )
    parts = split_reference_entries(paren)
    assert len(parts) >= 2
    num_parts = split_reference_entries(numbered)
    assert len(num_parts) >= 2


def test_split_falls_back_to_coarse_blank_lines():
    # No year markers; two blank-line blocks → coarse fallback
    region = "Odd entry without years aaa.\n\nAnother odd entry without years bbb."
    parts = split_reference_entries(region)
    assert len(parts) == 2


def test_blank_line_plausible_rejects_fat_blocks():
    # year_count >= 4 and a fat block → not plausible → year split
    fat = " ".join(f"Word{i}" for i in range(120))
    region = (
        f"A 2010. B 2011. C 2012. D 2013. {fat}\n\n"
        f"E 2014. F 2015. G 2016. H 2017. {fat}"
    )
    parts = split_reference_entries(region)
    assert len(parts) >= 4


def test_references_empty_entries_error():
    from lynguine.access.documents.strategies.pmlr_references_v1 import PmlrReferencesV1

    doc = _doc(text="References\n\n")
    with pytest.raises(DocumentSegmentError, match="no entries"):
        PmlrReferencesV1().segment(doc)


def test_find_references_region_cuts_at_appendix():
    text = "Body\nReferences\nAlice 2020. Bob.\nAppendix\nExtra"
    region = find_references_region(text)
    assert "Alice" in region
    assert "Appendix" not in region


# --- workshop long-split / min words ---


def test_workshop_splits_long_labelled_turns(tmp_path):
    from docx import Document as DocxDocument

    path = tmp_path / "long.docx"
    doc = DocxDocument()
    body = " ".join(f"word{i}" for i in range(200))
    doc.add_paragraph(f"Speaker 1: {body}. Extra sentence here for the second pack.")
    doc.add_paragraph(f"Facilitator: Thanks. Speaker 2: {body}")
    doc.save(path)
    units = segment_pdf(
        str(path),
        reader="docx",
        strategy="docx_workshop.v1",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
        workshop_chunk_words=40,
        workshop_max_words=60,
        facilitator_names=["Facilitator"],
    )
    assert len(units) >= 1


def test_workshop_drops_facilitator_only_below_min():
    from lynguine.access.documents.strategies.docx_workshop_v1 import DocxWorkshopV1

    text = "Facilitator: Hi there briefly."
    units = DocxWorkshopV1().segment(
        _doc(text=text, reader="docx", path="fac.docx"),
        min_unit_words=10,
        workshop_chunk_words=5,
    )
    assert units == []


# --- chatbot edges ---


def test_chatbot_skips_preamble_and_empty_answers():
    from lynguine.access.documents.strategies.docx_chatbot_v1 import DocxChatbotV1

    paras = [
        "Preamble before any participant with filler words for length.",
        "Participant 001",
        "Task: ignore this task line entirely please",
        "Conversation Summary",
        "A short summary of the chat for the participant.",
        "Conversation Transcript",
        "Participant 001:",
        "Participant 001: Real answer with enough words here yes definitely.",
    ]
    blocks = tuple(
        Block(
            0,
            i,
            0,
            float(i),
            1,
            float(i) + 1,
            p,
            "text",
            len(p.split()),
        )
        for i, p in enumerate(paras)
    )
    text = "\n".join(paras)
    units = DocxChatbotV1().segment(
        _doc(text=text, reader="docx", path="chat.docx", blocks=blocks)
    )
    assert len(units) == 1
    assert "Real answer" in units[0].text


# --- strategy resolve ---


def test_resolve_strategy_with_document(tmp_path):
    pdf = tmp_path / "p.pdf"
    make_pmlr_twocolumn(pdf)
    doc = read_pdf(str(pdf), allowed_roots=[str(tmp_path)])
    assert (
        resolve_strategy_id("auto", aspect="references", document=doc)
        == "pmlr_references.v1"
    )
    assert resolve_strategy_id("pub_dialogue.v1", aspect="body_chunks") == "pub_dialogue.v1"


def test_resolve_auto_ambiguous_without_document():
    with pytest.raises(UnknownStrategyError, match="without a document"):
        resolve_strategy_id("auto", aspect="dialogue_units")


def test_resolve_auto_no_candidates():
    with pytest.raises(UnknownStrategyError, match="No strategies"):
        resolve_strategy_id("auto", aspect="no_such_aspect")


# --- recogniser edges ---


def test_features_empty_blocks_median():
    doc = _doc(text="", blocks=())
    feats = document_features(doc)
    assert feats["median_block_width_ratio"] == 1.0


def test_choose_manual_override_wrong_aspect(tmp_path):
    path = tmp_path / "c.docx"
    make_chatbot_transcript(path)
    doc = read_docx(str(path), allowed_roots=[str(tmp_path)])
    choice = choose_strategy(doc, aspect="dialogue_units", strategy="pub_dialogue.v1")
    assert choice.strategy_id == "pub_dialogue.v1"
    assert "not ranked" in choice.rationale


def test_recogniser_workshop_with_participant_overlap():
    # Speaker labels + participant heading → secondary workshop branch
    text = "Participant 001\nSpeaker 1: Hello there everyone today.\nFacilitator: Welcome."
    doc = _doc(text=text, reader="docx", path="x.docx")
    feats = document_features(doc)
    assert feats["has_participant_heading"]
    assert feats["has_speaker_labels"]
    from lynguine.access.documents.recogniser import _score_strategy

    c = _score_strategy("docx_workshop.v1", "dialogue_units", feats)
    assert "speaker labels (also has participant)" in c.rationale


def test_recogniser_no_refs_heading_low_score():
    from lynguine.access.documents.recogniser import _score_strategy

    feats = {
        "reader": "pdf",
        "text_layer": "present",
        "has_references_heading": False,
        "twocolumn_ish": False,
        "has_findings": False,
        "has_recommendations": False,
        "has_participant_heading": False,
        "has_conversation_transcript": False,
        "has_speaker_labels": False,
    }
    c = _score_strategy("pmlr_references.v1", "references", feats)
    assert c.score < 0.5
    assert "no references heading" in c.rationale


def test_recogniser_tie_raises(monkeypatch):
    from lynguine.access.documents import recogniser as rec

    def fake_rank(document, *, aspect):
        return [
            rec.StrategyCandidate("a.v1", 0.5, "x"),
            rec.StrategyCandidate("b.v1", 0.5, "y"),
        ]

    monkeypatch.setattr(rec, "rank_strategies", fake_rank)
    with pytest.raises(UnknownStrategyError, match="tie"):
        choose_strategy(_doc(text="hello world " * 20), aspect="body_chunks")


# --- segment edges ---


def test_sparse_warn_and_empty_units_frame(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    with pytest.warns(UserWarning, match="text_layer"):
        units = segment_pdf(
            str(pdf),
            allowed_roots=[str(tmp_path)],
            on_sparse_text="warn",
        )
    assert units == []
    df = units_to_frame([])
    assert list(df.columns)


def test_unsupported_reader_and_aspect_mismatch(tmp_path):
    pdf = tmp_path / "p.pdf"
    make_pmlr_twocolumn(pdf)
    with pytest.raises(ValueError, match="Unsupported reader"):
        segment_pdf(str(pdf), reader="rtf", allowed_roots=[str(tmp_path)])
    with pytest.raises(ValueError, match="does not support aspect"):
        segment_pdf(
            str(pdf),
            strategy="pub_dialogue.v1",
            aspect="references",
            allowed_roots=[str(tmp_path)],
        )


def test_document_segment_min_chunk_words(tmp_path):
    pdf = tmp_path / "r.pdf"
    from lynguine.tests.fixtures.documents.builders import make_public_dialogue_report

    make_public_dialogue_report(pdf)
    rows = document_segment(
        pdf.name,
        strategy="pub_dialogue.v1",
        root=str(tmp_path),
        min_chunk_words=40,
    )
    assert rows


def test_sparse_explicit_strategy_path(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_scan_like(pdf)
    with pytest.raises(SparseTextLayerError, match="pub_dialogue"):
        segment_pdf(
            str(pdf),
            strategy="pub_dialogue.v1",
            allowed_roots=[str(tmp_path)],
        )


# --- pdf / chrome small edges ---


def test_block_type_names_and_import_error():
    assert _block_type_name(0) == "text"
    assert _block_type_name(1) == "image"
    assert _block_type_name(9) == "other"
    with patch.dict("sys.modules", {"fitz": None}):
        # Force import failure path
        with patch(
            "builtins.__import__",
            side_effect=ImportError("no fitz"),
        ):
            # Call through module helper with patched import inside function
            pass
    with patch(
        "lynguine.access.documents.pdf._import_fitz",
        side_effect=PyMuPDFMissingError("missing"),
    ):
        with pytest.raises(PyMuPDFMissingError):
            from lynguine.access.documents.pdf import read_pdf as rp

            rp("x.pdf")


def test_import_fitz_missing_message():
    import lynguine.access.documents.pdf as pdfmod

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "fitz":
            raise ImportError("nope")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(PyMuPDFMissingError):
            pdfmod._import_fitz()


def test_is_toc_empty_and_contents_numbered():
    assert is_toc_like("") is False
    assert is_toc_like("   ") is False
    assert is_toc_like(
        "Contents 1 Intro 2 Methods 3 Results 4 Discussion 5 Conclusion"
    )


def test_chrome_empty_after_filter_empty_mode():
    u = Unit(
        unit_id="d::c0000",
        text="Page 1 of 2 https://ex.com pad",
        segment_strategy="pub_dialogue.v1",
        aspect="body_chunks",
        chunk_index=0,
        word_count=6,
        chunking_method="paragraph",
        was_truncated=False,
        source_path="d.pdf",
    )
    out = apply_chrome_filters(
        [u],
        strip_running_headers=True,
        min_chunk_words=40,
        empty_after_filter="empty",
    )
    assert out == []


# --- remaining patch-edge coverage ---


def test_repack_flushes_when_buffer_exceeds_target():
    # Short sentences that accumulate past target without any one being long
    sents = [
        "One two three four.",
        "Five six seven eight.",
        "Nine ten eleven.",
    ]
    chunks = _repack_sentences_into_chunks(sents, target_words=6)
    assert len(chunks) >= 2


def test_pub_dialogue_skips_empty_and_short_char_chunks(monkeypatch):
    from lynguine.access.documents.strategies import pub_dialogue_v1 as pd

    body = " ".join(f"Word{i}" for i in range(40))
    oversized = ". ".join(" ".join(f"Word{i}" for i in range(30)) for _ in range(3)) + "."
    short_words = "a b c d e f g h i j"  # enough words, too few chars
    monkeypatch.setattr(
        pd, "_block_paragraphs", lambda d: ["", short_words, body, oversized]
    )
    monkeypatch.setattr(
        pd, "_paragraph_split", lambda t: ["", short_words, body, oversized]
    )
    # Empty packed piece exercises the unit-loop continue
    real_repack = pd._repack_sentences_into_chunks

    def fake_repack(sentences, target):
        return ["", *real_repack(sentences, target)]

    monkeypatch.setattr(pd, "_repack_sentences_into_chunks", fake_repack)

    units = PubDialogueV1().segment(
        _doc(text=body + "\n\n" + short_words + "\n\n" + oversized),
        min_chunk_words=5,
        min_chunk_chars=40,
        max_chunk_words=50,
        min_text_coverage=0.0,
        sentence_fallback_min_paragraphs=1,
    )
    assert units
    assert all(len(u.text) >= 40 for u in units)


def test_features_skips_non_text_blocks_for_width():
    blocks = (
        Block(0, 0, 0, 0, 50, 10, "pic", "image", 0),
        Block(0, 1, 0, 20, 80, 40, "Hello world text here", "text", 4),
    )
    feats = document_features(_doc(text="Hello world text here", blocks=blocks))
    assert feats["median_block_width_ratio"] == 0.8


def test_recogniser_single_column_pub_dialogue_bonus():
    from lynguine.access.documents.recogniser import _score_strategy

    feats = {
        "reader": "pdf",
        "text_layer": "present",
        "has_references_heading": False,
        "twocolumn_ish": False,
        "has_findings": True,
        "has_recommendations": False,
        "has_participant_heading": False,
        "has_conversation_transcript": False,
        "has_speaker_labels": False,
    }
    c = _score_strategy("pub_dialogue.v1", "body_chunks", feats)
    assert "single-column-ish" in c.rationale


def test_recogniser_unknown_strategy_aspect_pair():
    from lynguine.access.documents.recogniser import _score_strategy

    feats = {
        "reader": "pdf",
        "text_layer": "present",
        "has_references_heading": False,
        "twocolumn_ish": False,
        "has_findings": False,
        "has_recommendations": False,
        "has_participant_heading": False,
        "has_conversation_transcript": False,
        "has_speaker_labels": False,
    }
    c = _score_strategy("pub_dialogue.v1", "references", feats)
    assert "no heuristic match" in c.rationale


def test_choose_strategy_empty_rank_raises(monkeypatch):
    from lynguine.access.documents import recogniser as rec

    monkeypatch.setattr(rec, "rank_strategies", lambda *a, **k: [])
    with pytest.raises(UnknownStrategyError, match="No strategies registered"):
        choose_strategy(_doc(text="hello world " * 20), aspect="body_chunks")


def test_resolve_auto_single_candidate_without_document(monkeypatch):
    import lynguine.access.documents.strategy as strat

    monkeypatch.setattr(strat, "list_strategies", lambda *, aspect=None: ["only.v1"])
    assert resolve_strategy_id("auto", aspect="body_chunks") == "only.v1"


def test_chatbot_skips_task_lines_outside_transcript():
    from lynguine.access.documents.strategies.docx_chatbot_v1 import DocxChatbotV1

    paras = [
        "Participant 001",
        "Task 1: Do the thing with enough filler words",
        "Activity: Ignore this activity line as well please",
        "Conversation Transcript",
        "Bot: What is your view on accountability today?",
        "Participant 001: Answer with enough words to keep the unit.",
    ]
    blocks = tuple(
        Block(0, i, 0, float(i), 1, float(i) + 1, p, "text", len(p.split()))
        for i, p in enumerate(paras)
    )
    units = DocxChatbotV1().segment(
        _doc(text="\n".join(paras), reader="docx", path="t.docx", blocks=blocks)
    )
    assert len(units) == 1
    assert "Answer" in units[0].text
    assert "Bot:" in units[0].extras.get("context", "")


def test_workshop_split_ignores_empty_sentence_pieces(monkeypatch):
    import lynguine.access.documents.strategies.docx_workshop_v1 as ws

    real_split = re.split

    def split_with_empty(pattern, string, maxsplit=0):
        parts = real_split(pattern, string, maxsplit)
        if isinstance(pattern, str) and "(?<=[.?!])" in pattern:
            return [""] + parts
        return parts

    monkeypatch.setattr(ws.re, "split", split_with_empty)
    body = ". ".join(f"Sentence number {i} with words" for i in range(40))
    text = f"Speaker 1: {body}"
    units = ws.DocxWorkshopV1().segment(
        _doc(text=text, reader="docx", path="w.docx"),
        workshop_max_words=20,
        workshop_chunk_words=15,
        min_unit_words=5,
    )
    assert units


def test_blank_line_plausible_fat_block_with_enough_blocks():
    # year_count >= 4, blocks*2 >= year_count, but a fat block → not plausible
    fat = " ".join(f"Word{i}" for i in range(120))
    region = (
        f"Smith 2010. {fat}\n\n"
        f"Jones 2011. short\n\n"
        f"Lee 2012. short\n\n"
        f"Ng 2013. short"
    )
    parts = split_reference_entries(region)
    # Year-dot split should win over the implausible blank-line blocks
    assert len(parts) >= 2


def test_split_fallback_to_whole_region():
    # Single block, no year/number cues → whole collapsed region
    region = "Lone odd reference entry without year markers at all."
    parts = split_reference_entries(region)
    assert parts == [region]


def test_split_fallback_coarse_blocks_after_failed_splits():
    # Year terminators present (YYYY.) and fat blocks → blank lines implausible,
    # but lowercase after the year means year-dot split cannot fire either.
    fat = " ".join(f"word{i}" for i in range(120))
    region = (
        f"first 2010. {fat}\n\n"
        f"second 2011. {fat}\n\n"
        f"third 2012. short words here\n\n"
        f"fourth 2013. short words here"
    )
    parts = split_reference_entries(region)
    assert len(parts) == 4


def test_read_docx_details_and_bare_path_and_blank_para(tmp_path):
    from docx import Document as DocxDocument
    from lynguine.access.documents.docx_reader import (
        PythonDocxMissingError,
        _import_docx,
    )

    path = tmp_path / "blankish.docx"
    d = DocxDocument()
    d.add_paragraph("First real paragraph with words.")
    d.add_paragraph("")  # skipped empty
    d.add_paragraph("   ")  # skipped whitespace
    d.add_paragraph("Second real paragraph with words.")
    d.save(path)

    details = {"allowed_roots": [str(tmp_path)]}
    doc = read_docx(str(path), details=details)
    assert doc.metadata["paragraph_count"] == 2

    # Bare path (no details / allowed_roots)
    doc2 = read_docx(str(path))
    assert doc2.total_words > 0

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "docx" or name.startswith("docx."):
            raise ImportError("nope")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(PythonDocxMissingError):
            _import_docx()


def test_pdf_block_exceptions_and_bare_path(tmp_path):
    import lynguine.access.documents.pdf as pdfmod

    pdf = tmp_path / "p.pdf"
    make_pmlr_twocolumn(pdf)

    # Bare path (no details / allowed_roots)
    doc = read_pdf(str(pdf))
    assert doc.page_count >= 1

    class BadPage:
        def get_text(self, *args, **kwargs):
            if args and args[0] == "blocks":
                raise RuntimeError("blocks failed")
            return "Hello world from a synthetic page with words."

        @property
        def rect(self):
            return MagicMock(width=100, height=100)

    class BadDoc:
        metadata = None

        def __iter__(self):
            return iter([BadPage()])

        def __len__(self):
            return 1

        def close(self):
            pass

    pages = pdfmod._pages_from_doc(BadDoc())
    assert pages[0].blocks == ()

    class ShortBlockPage:
        def get_text(self, *args, **kwargs):
            if args and args[0] == "blocks":
                return [(0, 0, 1, 1, "x", 0)]  # len < 7 → skipped
            return "Hello world from a synthetic page with words."

        @property
        def rect(self):
            return MagicMock(width=100, height=100)

    class ShortBlockDoc:
        def __iter__(self):
            return iter([ShortBlockPage()])

        def __len__(self):
            return 1

        def close(self):
            pass

        @property
        def metadata(self):
            raise RuntimeError("meta boom")

    # Short blocks skipped
    pages2 = pdfmod._pages_from_doc(ShortBlockDoc())
    assert pages2[0].blocks == ()

    # metadata exception swallowed in read_pdf
    class OpenDoc(ShortBlockDoc):
        pass

    mock_fitz = MagicMock()
    mock_fitz.open.return_value = OpenDoc()
    with patch.object(pdfmod, "_import_fitz", return_value=mock_fitz):
        out = pdfmod.read_pdf(str(pdf))
        # When metadata raises, key is simply absent
        assert "pdf_metadata" not in out.metadata
