---
id: "2026-10-17_document-segment-pub-dialogue-v1"
title: "Strategy API, pub_dialogue.v1 segmenter, document_segment compute"
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
- access
- compute
- documents
- cip0013
---

# Task: Strategy API, pub_dialogue.v1 segmenter, document_segment compute

## Description

Define the named strategy interface and implement `pub_dialogue.v1` by porting behaviour from `pub_dialogue.access.extract_chunks_from_pdf`. Register a `document_segment` compute function that takes a path (+ reader/strategy/aspect args) and emits exploded unit rows (`unit_id`, `text`, `segment_strategy`, …). When the text layer is absent/sparse, fail or warn explicitly — do not silently emit an empty corpus.

## Acceptance Criteria

- [ ] Strategy protocol: id, supported aspects, parameters, `segment(document_model) -> units`
- [ ] `pub_dialogue.v1` produces body_chunks comparable to pub-dialogue chunking on fixtures
- [ ] `document_segment` available via Compute registry (lynguine access compute or agreed registration path)
- [ ] Default row grain is exploded (one row per unit); strategy id recorded on rows
- [ ] Sparse/absent text layer yields explicit error or empty result with warning (per CIP-0013)
- [ ] Unit tests against committed fixtures (may land with fixture task)

## Implementation Notes

- Port carefully; keep pub-dialogue app free to call shared API later
- Manual `strategy:` override must work before recogniser exists (`auto` can mean sole registered strategy or require explicit id until recogniser lands)

## Related

- CIP: 0013
- Depends on: `2026-10-17_document-model-pdf-reader`
- Seed: `pub_dialogue/access.py`

## Progress Updates

### 2026-10-17

Task created (Ready) from Accepted CIP-0013 implementation plan step 3.
