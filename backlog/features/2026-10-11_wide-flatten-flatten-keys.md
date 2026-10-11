---
id: "2026-10-11_wide-flatten-flatten-keys"
title: "Emit flattenKeys on wide_flatten (configurable name)"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-core-helper"
- "2026-10-11_wide-flatten-access-type"
tags:
- backlog
- features
- access
- wide-flatten
- flatten-keys
- cip0010
---

# Task: Emit flattenKeys on wide_flatten (configurable name)

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-0010 Phase 2a: after materialized `wide_flatten`, emit an ordered list of former index labels on the single wide row so Liquid/templates can `{% for %}` without parsing column names.

Aligns with tenet `authoritative-store-and-views`: key list is infrastructure metadata, not an application heuristic.

## Acceptance Criteria

- [x] Wide result includes a list field of index labels used for name prefixes (default name `flattenKeys`)
- [x] Config key to rename the field (e.g. `keys_field: flattenKeys`)
- [x] Order is stable and matches prefix order for `index_then_field` / documented for `field_then_index`
- [x] Empty input → empty list (or omit per documented policy)
- [x] Path metadata (`sourceDirectory`, …) stays as widened value columns when listed in `columns` — not forced to be the index
- [x] Unit tests cover happy path, empty, and custom keys field name
- [x] Separator-in-index policy unchanged (v1)

## Implementation Notes

- Touch `wide_flatten_dataframe` / `read_wide_flatten` in `lynguine/access/io.py`
- List cell type: Python `list` in a single-row object column (same spirit as series list cells)
- View-path metadata (Phase 2b) may reuse the same key list without materializing wide columns

## Related

- CIP: 0010
- Tenet: `authoritative-store-and-views` (Proposed)
- Unblocks: virtual wide view + docs

## Progress Updates

### 2026-10-11

Task created (Ready) from CIP-0010 Phase 2a.

Implemented with Phase 2 helpers in `lynguine/access/io.py` and tests/docs. Marked Completed.
