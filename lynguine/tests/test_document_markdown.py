"""Tests for CIP-0013 markdown reader and socratic_markdown.v1."""

from __future__ import annotations

from lynguine.access.documents import (
    TextLayer,
    choose_strategy,
    document_features,
    document_segment,
    ensure_builtin_strategies,
    list_strategies,
    read_markdown,
    segment_pdf,
)

SAMPLE = """---
crsid: "abc123"
llm_provider: "OpenAI"
title: "Worksheet 1: Socratic dialogue"
---

# Worksheet 1: dialogue

## How to fill this file

Ignore this preamble. It is not an exchange.

## Exchange 1

### User

<!-- Paste your first prompt here (curiosity: why Shannon used "entropy"). -->
Why did Shannon choose the word entropy for his measure of uncertainty in communication?

### LLM

<!-- Paste the model's reply here in full. -->
Shannon used entropy because the formula matched Boltzmann and Gibbs in statistical mechanics, and a popular story credits von Neumann with suggesting the name.

## Exchange 2

### User

That anecdote sits poorly against Shannon's Tolman footnote and the Wiener citations in the 1948 paper. What is the primary-source trail?

### LLM

Tolman's statistical mechanics text is the citation beside the formula. Wiener appears throughout the acknowledgements. The von Neumann story is later folklore, not the 1948 apparatus.
"""


def _write(tmp_path, name: str = "L172_abc123_worksheet1_dialogue.md") -> str:
    path = tmp_path / name
    path.write_text(SAMPLE, encoding="utf-8")
    return str(path)


def test_socratic_strategy_registered():
    ensure_builtin_strategies()
    assert "socratic_markdown.v1" in list_strategies(aspect="dialogue_units")
    assert "socratic_markdown.v1" in list_strategies(aspect="body_chunks")


def test_read_markdown_strips_frontmatter(tmp_path):
    path = _write(tmp_path)
    doc = read_markdown(path, allowed_roots=[str(tmp_path)])
    assert doc.reader == "markdown"
    assert doc.text_layer is TextLayer.PRESENT
    assert doc.metadata["frontmatter"]["crsid"] == "abc123"
    assert "crsid:" not in doc.full_text
    assert "## Exchange 1" in doc.full_text


def test_socratic_exchange_units(tmp_path):
    path = _write(tmp_path)
    units = segment_pdf(
        path,
        reader="markdown",
        strategy="socratic_markdown.v1",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
        min_chunk_words=10,
    )
    assert len(units) == 2
    assert [u.extras["exchange_index"] for u in units] == [1, 2]
    assert all(u.segment_strategy == "socratic_markdown.v1" for u in units)
    assert all(u.aspect == "dialogue_units" for u in units)
    assert "Paste your first prompt" not in units[0].text
    assert "Why did Shannon" in units[0].extras["user_text"]
    assert "von Neumann" in units[0].extras["llm_text"]
    assert "preamble" not in units[0].text.lower()


def test_socratic_auto_picks_strategy(tmp_path):
    path = _write(tmp_path)
    units = segment_pdf(
        path,
        reader="markdown",
        strategy="auto",
        aspect="dialogue_units",
        allowed_roots=[str(tmp_path)],
        min_chunk_words=10,
    )
    assert units
    assert units[0].segment_strategy == "socratic_markdown.v1"
    assert units[0].extras.get("recogniser_score", 0) > 0


def test_socratic_auto_body_chunks_does_not_pick_pub_dialogue(tmp_path):
    path = _write(tmp_path)
    doc = read_markdown(path, allowed_roots=[str(tmp_path)])
    feats = document_features(doc)
    assert feats["reader"] == "markdown"
    assert feats["has_socratic_exchange"]
    assert feats["has_user_llm_labels"]
    choice = choose_strategy(doc, aspect="body_chunks", strategy="auto")
    assert choice.strategy_id == "socratic_markdown.v1"


def test_document_segment_markdown_compute(tmp_path):
    path = _write(tmp_path)
    rows = document_segment(
        path,
        reader="markdown",
        strategy="socratic_markdown.v1",
        aspect="dialogue_units",
        root=str(tmp_path),
        min_chunk_words=10,
    )
    assert len(rows) == 2
    assert rows[0]["unit_id"].endswith("::ex01")
    assert rows[0]["chunking_method"] == "socratic_exchange"


def test_short_exchange_dropped(tmp_path):
    path = tmp_path / "short.md"
    # Preamble keeps the document above the sparse-text threshold so the
    # strategy, not text-layer detection, is what drops the short exchange.
    preamble = " ".join(["padding"] * 50)
    path.write_text(
        f"# Notes\n\n{preamble}\n\n## Exchange 1\n\n### User\nHi?\n\n### LLM\nNo.\n",
        encoding="utf-8",
    )
    units = segment_pdf(
        str(path),
        reader="markdown",
        strategy="socratic_markdown.v1",
        allowed_roots=[str(tmp_path)],
        min_chunk_words=40,
    )
    assert units == []
