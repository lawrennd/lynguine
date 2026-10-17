---
id: "2026-10-17_document-layout-recogniser"
title: "Document layout recogniser v0 (strategy ranking)"
status: "Ready"
priority: "Medium"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-segment-pub-dialogue-v1"
- "2026-10-17_docx-dialogue-strategies"
- "2026-10-17_document-references-aspect"
tags:
- backlog
- features
- access
- documents
- recogniser
- cip0013
---

# Task: Document layout recogniser v0 (strategy ranking)

## Description

Implement recogniser v0: compute features from the document model and return scored strategy candidates. `strategy: auto` selects the top candidate; chosen id and score are always written on output rows. Manual strategy override still wins. Include scan/sparse text features so auto does not pretend a text-layer strategy succeeded on image-only PDFs.

## Acceptance Criteria

- [ ] `features(document_model) -> [{strategy_id, score, rationale}, ...]`
- [ ] `auto` selects a registered strategy; override ignores ranking
- [ ] Output rows include `segment_strategy` and recogniser score/rationale fields
- [ ] Fixture manifests can assert expected strategy under `auto`
- [ ] Sparse/absent text layer does not silently pick a body_chunks strategy that yields empty success

## Implementation Notes

- Keep pure and testable without I/O beyond the document model
- v0 can be heuristic (column gap, References heading, participant headings, words/page)

## Related

- CIP: 0013
- Depends on: multiple strategies existing to rank

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 6.
