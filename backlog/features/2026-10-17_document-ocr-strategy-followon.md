---
id: "2026-10-17_document-ocr-strategy-followon"
title: "Follow-on: optional OCR strategy for scanned PDFs"
status: "Proposed"
priority: "Low"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-model-pdf-reader"
- "2026-10-17_document-layout-recogniser"
tags:
- backlog
- features
- documents
- ocr
- cip0013
- follow-on
---

# Task: Follow-on — optional OCR strategy for scanned PDFs

## Description

After text-layer detection is solid, add an optional OCR path (e.g. `pdf_ocr.v1` via Tesseract or PyMuPDF OCR) as an explicit strategy/reader flag with its own extra dependency. Not part of CIP-0013 v1 success criteria — recorded so scan handling has a clear next step.

## Acceptance Criteria

- [ ] OCR is opt-in (`strategy` or `ocr: true`), never default for normal PDFs
- [ ] Extra dependency documented; CI OCR tests optional or marked
- [ ] Detection metrics still run; OCR fills text layer before segment strategies
- [ ] At least one scan fixture exercises OCR when the optional extra is present

## Implementation Notes

- pub-dialogue `ocr_if_image_only` is a behavioural seed
- Keep separate from GROBID / LLM reference repair follow-ons

## Related

- CIP: 0013 §4
- Blocked in spirit until reader + recogniser exist

## Progress Updates

### 2026-10-17

Task created (Proposed) as explicit CIP-0013 out-of-scope follow-on.
