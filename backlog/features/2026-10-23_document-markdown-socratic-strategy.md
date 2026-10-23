---
id: "2026-10-23_document-markdown-socratic-strategy"
title: "Markdown reader and socratic_markdown.v1 exchange units"
status: "Completed"
priority: "High"
created: "2026-10-23"
last_updated: "2026-10-23"
category: "features"
related_cips: ["0013"]
owner: "Neil Lawrence"
dependencies: []
tags:
- backlog
- documents
- markdown
- dialogue
---

# Task: Markdown reader and socratic_markdown.v1

> CIP-0013 follow-on: L172 Worksheet 1 dialogues are markdown, not PDF/DOCX.

## Description

Add a `markdown` reader and strategy `socratic_markdown.v1` so the dialogue-analysis pipeline can catalog, segment, and explode student Socratic dialogues (exactly ten `## Exchange N` / `### User` / `### LLM` turns with YAML frontmatter).

Phrase extract still happens downstream in referia (`02_embed`). This task is access-stage only.

## Acceptance Criteria

- [x] `read_markdown` loads UTF-8, strips YAML frontmatter into metadata, classifies text layer
- [x] `socratic_markdown.v1` emits one unit per exchange (`dialogue_units` and `body_chunks`)
- [x] HTML comments in the worksheet template are stripped
- [x] `document_segment` accepts `reader: markdown`
- [x] Recogniser `auto` picks this strategy on markdown files with Exchange / User / LLM markers
- [x] Tests green: `lynguine/tests/test_document_markdown.py`

## Implementation Notes

Reader lives in `lynguine/access/documents/markdown.py`. Strategy in `strategies/socratic_markdown_v1.py`. Grain is the exchange pair (student probe + model reply), not the whole file.

## Related

- CIP: 0013
- Application: `dialogue-analysis/l172-worksheet1/` in the referia reviews folder

## Progress Updates

### 2026-10-23

Task created. Reader, strategy, recogniser wiring, and tests written on `cip0013-markdown-socratic-dialogues`.

Tests green (`7 passed` in `lynguine/tests/test_document_markdown.py`). Short-exchange case needs a non-sparse preamble so `min_chunk_words` is what drops the unit.
