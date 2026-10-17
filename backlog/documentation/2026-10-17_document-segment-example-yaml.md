---
id: "2026-10-17_document-segment-example-yaml"
title: "Example YAML flows for document_segment (pub-dialogue sketch)"
status: "Proposed"
priority: "Low"
created: "2026-10-17"
last_updated: "2026-10-17"
category: "documentation"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-segment-pub-dialogue-v1"
tags:
- backlog
- documentation
- documents
- cip0013
---

# Task: Example YAML flows for document_segment

## Description

Document example interface YAML for metadata spreadsheet → `document_segment` (pub-dialogue-shaped), and short notes pointing dialogue-formats / mlresearch follow-ons. Prefer README or compute docs only after behaviour exists; until then a `examples/` sketch is enough. Full Sphinx compression waits for CIP close.

## Acceptance Criteria

- [ ] At least one worked YAML example committed under `examples/` or docs
- [ ] Mentions strategy override vs `auto`, explode grain, and scan detection behaviour
- [ ] Links to CIP-0013; does not claim OCR or `pdf_directory` sugar

## Implementation Notes

- Light touch until segment API is stable
- Formal doc compression is a separate post-close step

## Related

- CIP: 0013
- Depends on: `2026-10-17_document-segment-pub-dialogue-v1`

## Progress Updates

### 2026-10-17

Task created (Proposed) from Accepted CIP-0013 implementation plan step 8.
