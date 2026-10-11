---
id: "2026-10-11_document-wide-flatten"
title: "Document type: wide_flatten and distinguish from series/stack"
status: "Completed"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "documentation"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-access-type"
tags:
- backlog
- documentation
- access
- wide-flatten
- cip0010
---

# Task: Document type: wide_flatten and distinguish from series/stack

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Document CIP-0010’s access type next to stacking / directory allocation material: config keys, shape change, and explicit “not series / not hstack” guidance. Note opt-in only and that full `postcompute` honesty is CIP-0011.

## Acceptance Criteria

- [x] README (or equivalent in-tree user docs) describes `type: wide_flatten`
- [x] Example shows nested `yaml_directory` (or local multi-row) → wide columns
- [x] Documents `separator`, `order`, optional `columns`, and defaults
- [x] States result is one row with index-augmented names; no parent index required
- [x] Contrasts with `series` (lists / parent index) and `hstack`/`vstack` (source concat)
- [x] Notes thin nested/outer `compute` via `finalize_data`; does not claim unwired `postcompute`
- [x] Short release note: additive, opt-in

## Implementation Notes

- README section under Stacking Data; cross-link from Directory of Files

## Related

- CIP: 0010
- Depends on: `2026-10-11_wide-flatten-access-type`
- Related: CIP-0011

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-0010 — documentation step.

README updated. Marked Completed.
