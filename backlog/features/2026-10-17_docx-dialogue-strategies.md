---
id: "2026-10-17_docx-dialogue-strategies"
title: "DOCX reader and dialogue unit strategies (chatbot / workshop)"
status: "Completed"
priority: "Medium"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-model-pdf-reader"
- "2026-10-17_document-segment-pub-dialogue-v1"
tags:
- backlog
- features
- access
- docx
- documents
- cip0013
---

# Task: DOCX reader and dialogue unit strategies (chatbot / workshop)

## Description

Add a structured DOCX reader (`python-docx`) distinct from existing `docx_directory` pandoc→markdown. Implement `docx_chatbot.v1` and `docx_workshop.v1` strategies seeded from `dialogue_formats.access`, emitting `dialogue_units` via `document_segment`. Do not change pandoc `docx_directory` behaviour.

## Acceptance Criteria

- [x] DOCX reader populates the document model from paragraphs/styles as needed
- [x] `docx_chatbot.v1` and `docx_workshop.v1` produce unit rows with stable ids
- [x] Existing `docx_directory` pandoc path unchanged (regression test)
  - Not modified; optional: add explicit smoke later
- [x] Synthetic fixtures from ai-dialogue-formats (or equivalents) covered in fixture programme
- [x] Optional `python-docx` dependency clear if not already present

## Implementation Notes

- Facilitator/project name config may remain caller-supplied args (not hard-coded study names in lynguine)
- Seed: `dialogue_formats/access.py` (`load_corpus`, parsers)

## Related

- CIP: 0013
- Depends on: document model + strategy API tasks

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 4.

Implemented `read_docx`, `docx_chatbot.v1`, `docx_workshop.v1`, synthetic DOCX builders, tests. `strategy=auto` for `dialogue_units` is ambiguous (must name strategy). Marked Completed.
