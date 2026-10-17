---
id: "2026-10-17_document-fixtures-programme"
title: "Multi-corpus document fixture programme for CIP-0013"
status: "Ready"
priority: "High"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-model-pdf-reader"
tags:
- backlog
- features
- testing
- documents
- cip0013
---

# Task: Multi-corpus document fixture programme for CIP-0013

## Description

Stand up `tests/fixtures/documents/<corpus>/…` with per-file manifests (expected strategy, aspect, gold snippets / ref lists) and pytest parametrisation. Cover pub-dialogue-style PDFs, mlresearch/PMLR academic PDFs (reference oracles), DOCX dialogue shapes, and at least one scan-like PDF that asserts **detection** only. CI must run without network, API keys, or OCR binaries.

## Acceptance Criteria

- [ ] Fixture layout + manifest schema documented in the test package or CIP notes
- [ ] At least one fixture per corpus family: public-dialogue PDF, academic PDF, DOCX transcript (synthetic OK)
- [ ] Scan-like fixture asserts text-layer detection / explicit failure behaviour
- [ ] Parametrised tests fail clearly when gold mismatches
- [ ] Licence/redaction approach recorded for any non-synthetic PDFs
- [ ] No Tesseract / OpenAI required in default pytest path

## Implementation Notes

- Can grow incrementally as strategies land; harness first is fine
- Prefer small committed page excerpts over full 66-report corpus
- Optional env var for local full-corpus path later

## Related

- CIP: 0013 §8
- Depends on: `2026-10-17_document-model-pdf-reader` (for reader-level tests); expands with segment/ref tasks

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 7.
