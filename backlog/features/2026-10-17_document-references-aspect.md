---
id: "2026-10-17_document-references-aspect"
title: "References aspect with academic prose strategy"
status: "Ready"
priority: "Medium"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-segment-pub-dialogue-v1"
- "2026-10-17_document-fixtures-programme"
tags:
- backlog
- features
- access
- documents
- references
- cip0013
---

# Task: References aspect with academic prose strategy

## Description

Implement the `references` aspect: locate the references region in a PDF document model, then split entries with at least one academic prose strategy suitable for PMLR-style end-of-paper lists. v1 output is `ref_id`, order, and `ref_raw` only — no required structured parse. Wire as `extract_references` or `document_segment` with `aspect: references` per CIP-0013 YAML sketch.

## Acceptance Criteria

- [ ] Region detection finds References (or equivalent) block on fixture academic PDFs
- [ ] At least one entry-splitting strategy emits ordered `ref_raw` rows
- [ ] Gold `ref_raw` lists asserted in fixture manifests for sample papers
- [ ] Missing/unfound region fails clearly (no invented citations)
- [ ] No GROBID / LLM dependency in this task

## Implementation Notes

- Separate region detection from entry parsing (CIP-0013)
- Fixtures from mlresearch volume PDFs (excerpts OK)
- Structured author/title/year parse is explicitly later

## Related

- CIP: 0013
- Depends on: strategy API + fixtures harness

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 5.
