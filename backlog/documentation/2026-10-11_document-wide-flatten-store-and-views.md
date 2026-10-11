---
id: "2026-10-11_document-wide-flatten-store-and-views"
title: "Document wide_flatten Pattern A vs B and authoritative-store-and-views tenet"
status: "Completed"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "documentation"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-flatten-keys"
- "2026-10-11_wide-flatten-virtual-view"
- "2026-10-11_wide-unflatten"
tags:
- backlog
- documentation
- wide-flatten
- tenets
- cip0010
---

# Task: Document wide_flatten Pattern A vs B and store/views tenet

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Update user-facing docs so CIP-0010 Phase 2 matches tenet `authoritative-store-and-views`:

- Pattern **A** (default for editable catalogs): tall store + virtual wide names / `flattenKeys`
- Pattern **B**: materialized `type: wide_flatten` snapshot; `wide_unflatten` if you must write tall from wide
- Point at CIP-0012 for pivot (lossy vs view)

## Acceptance Criteria

- [x] README (or equivalent) states A vs B and which path Save uses
- [x] Documents `flattenKeys` / keys field and loop guidance for Liquid
- [x] Documents virtual name→`(index, field)` for get/set (once implemented)
- [x] Documents `wide_unflatten` as secondary / round-trip
- [x] Links or cites tenet `authoritative-store-and-views` (once Active, or as Proposed with note)
- [x] Cross-link CIP-0012 for pivot policy
- [x] Does not claim aggregating `pivot_table` is editable/round-trippable

## Implementation Notes

- Extend the existing Wide Flatten README section from Phase 1
- Keep examples infrastructure-generic

## Related

- CIP: 0010, 0012
- Tenet: `authoritative-store-and-views`
- Depends on: Phase 2a–2c feature tasks for accurate API names

## Progress Updates

### 2026-10-11

Task created (Ready) from CIP-0010 Phase 2 docs.

Implemented with Phase 2 helpers in `lynguine/access/io.py` and tests/docs. Marked Completed.
