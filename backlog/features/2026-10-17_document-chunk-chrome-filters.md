---
id: "2026-10-17_document-chunk-chrome-filters"
title: "Filter PDF chrome from body_chunks (footers, running headers, TOC)"
status: "Completed"
priority: "Medium"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-segment-pub-dialogue-v1"
tags:
- backlog
- features
- access
- documents
- pub-dialogue
- cip0013
---

# Task: Filter PDF chrome from body_chunks (footers, running headers, TOC)

## Description

End-to-end review of `pub_dialogue.v1` on real public-dialogue PDFs shows **parity with the legacy extractor**, but the resulting units are not a clean paragraph corpus. Recurring PDF chrome passes the word/char floors and pollutes downstream analysis:

1. **Near-duplicate footers** — Ipsos/Royal Society reports emit the same ISO 20252 / Terms footer as dozens of near-identical chunks (~28–43% of chunks on sampled reports).
2. **Running headers / page chrome** — taglines, “Page N of M”, and site URLs are woven into body units (especially under sentence fallback, e.g. Ada Lovelace web-print PDFs).
3. **TOC / front-matter pages** — contents lists and cover/nav blocks become early chunks despite carrying little deliberative content.

Implement **explicit, opt-in (or clearly documented default) filters** on the body_chunks path so flows can drop this chrome without breaking the seeded parity mode used for regression against `pub_dialogue.access.extract_chunks_from_pdf`.

## Acceptance Criteria

- [x] Near-duplicate footer / boilerplate chunks can be dropped (same or near-same text repeating across the document, or known footer patterns)
- [x] Running headers / page chrome (page-X-of-Y, repeated taglines, URL-only or chrome-heavy prefixes) can be stripped from unit text and/or cause a unit to be discarded when little remains
- [x] TOC-like / front-matter units can be skipped (e.g. dense leader-dot contents, cover-only blocks) via an explicit strategy parameter
- [x] Filters are **explicit** in the API (`strategy` params or named post-process flags) — default behaviour that preserves legacy parity remains available for regression
- [x] Unit tests cover synthetic fixtures with planted footer repeats, running headers, and a TOC page
- [x] Documented on at least one real-corpus smoke check (or backlog note) that Ipsos-style footer duplication falls sharply when filters are enabled
- [x] Chosen strategy id and filter flags remain visible on output rows / extras for auditability

## Implementation Notes

- Prefer a small post-segment filter stage on `pub_dialogue.v1` (or a shared `body_chunks` cleanup helper) rather than baking opaque magic into the PDF reader.
- Near-duplicate detection: hash/normalised-text frequency with a minimum repeat count; optionally seed known Ipsos footer substrings as patterns, but do not rely only on hard-coded vendor strings.
- Running-header strip: line-level or prefix/suffix patterns (page markers, URLs) applied before the empty/short unit drop.
- TOC skip: structural signals (leader dots, “Contents”, very high period/dot density with low prose) — keep conservative to avoid dropping real bullet findings (AICAM missions uses arrows/bullets).
- Keep CIP-0013 tenets: no silent empty success; filters that remove everything should surface clearly.
- Out of scope for this task: OCR; full layout-aware header/footer geometry; changing default parity with pub-dialogue without an explicit flag.

## Related

- CIP: 0013
- Depends on: `2026-10-17_document-segment-pub-dialogue-v1`
- Motivated by: 2026-10-17 e2e dive on `pub-dialogue/data` PDFs vs legacy `extract_chunks_from_pdf`
- Related follow-on: `2026-10-17_document-segment-example-yaml` (document filter flags in example YAML once implemented)

## Progress Updates

### 2026-10-17

Task created (Ready) after e2e review: lynguine matches pub-dialogue chunk-for-chunk, but Ipsos footer duplication, Ada page/URL chrome, and TOC/front matter remain in the unit stream. Implement filters before claiming better-than-legacy extraction quality.

### 2026-10-17 (implemented)

Added `lynguine.access.documents.chrome_filters` and wired into `pub_dialogue.v1` via `filter_chrome` / per-flag params (default off = legacy parity). Smoke on real PDFs with `filter_chrome=True`:

- Ipsos/RS 2017: 323 → 226 chunks; footer-only 92 → 0
- Ada Lovelace 2025: 39 → 39 chunks; `Page N of M` chrome in 35 → 0 (stripped in place)

Tests: `test_document_chrome_filters.py`. Status → Completed.
