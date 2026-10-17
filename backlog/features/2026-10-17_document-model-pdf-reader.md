---
id: "2026-10-17_document-model-pdf-reader"
title: "Document model and PDF reader with text-layer detection"
status: "Completed"
priority: "High"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- access
- documents
- pdf
- cip0013
---

# Task: Document model and PDF reader with text-layer detection

> Backlog tasks execute CIPs. Linked CIP: 0013.

## Description

Add `lynguine.access.documents` with a minimal document model (pages/blocks/text stats) and a PDF reader wrapping PyMuPDF. Expose text-layer detection (`absent` / `sparse` / `present` or equivalent) using words-per-page and extractable-text coverage. Path confinement must use existing `allowed_roots`. PyMuPDF is an optional extra; missing install fails with a clear error.

No OCR in this task — detect only, as accepted in CIP-0013.

## Acceptance Criteria

- [x] Package/module `lynguine.access.documents` (or agreed name) with a documented document model
- [x] PDF reader opens a confined path and returns pages/blocks plus text-layer stats
- [x] Low-text / scan-like PDFs are classified without calling OCR
- [x] Optional dependency declared; import/use without PyMuPDF raises an actionable error
- [x] Unit tests with a small text PDF and a scan-like / empty-text fixture
- [x] No new `read_data` type yet (functions only)

## Implementation Notes

- Seed metrics from pub-dialogue `MIN_WORDS_PER_PAGE` / coverage ideas
- Keep reader thin: no research-unit segmentation here
- Optional extra in `pyproject.toml` (e.g. `pdf` or `documents`)

## Related

- CIP: 0013
- Downstream: `2026-10-17_document-segment-pub-dialogue-v1`, fixture programme

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 2.

Implemented on `cip0013-document-extractors`: `lynguine.access.documents` model + `read_pdf` / `classify_text_layer`; optional `documents` extra (PyMuPDF); CI installs `--extras documents`; tests in `test_access_documents_pdf.py`. Marked Completed.
