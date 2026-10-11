---
id: "2026-10-11_wide-flatten-virtual-view"
title: "Virtual wide view: name to (index, field) get/set on tall store"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-flatten-keys"
tags:
- backlog
- features
- assess
- wide-flatten
- view
- cip0010
---

# Task: Virtual wide view — name to (index, field) get/set on tall store

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-0010 Phase 2b (Pattern A, primary path): resolve logical wide names `"{key}{separator}{field}"` into focus on the **tall** store — set index → `key`, column → `field` — then existing `get_value` / `set_value`. Do **not** replace the working DataFrame with a materialized wide row for editing.

This is the tenet-aligned path for catalog `complete` and similar writable fields.

## Acceptance Criteria

- [x] Helper (or `CustomDataFrame` API) parses wide name → `(index, field)` given `separator` and `order`
- [x] Get via resolver returns the tall cell without changing `df.shape`
- [x] Set via resolver updates the tall cell; subsequent `write_data` sees tall columns only
- [x] Ambiguous / unparseable names raise clear errors (separator policy)
- [x] Works with `flattenKeys` (or equivalent) to enumerate keys for UI/Liquid
- [x] Unit tests: get/set `complete`-style field; shape unchanged; bad name errors
- [x] Document that this is Pattern A; materialized `type: wide_flatten` remains a snapshot option

## Implementation Notes

- Prefer assess-layer helpers next to get/set focus, not only access `io.py`
- Do not require callers to run `type: wide_flatten` for edit paths
- Liquid flat dict snapshots (if any) stay read-only unless a later write-back is defined

## Related

- CIP: 0010
- Tenet: `authoritative-store-and-views`
- Depends on: `2026-10-11_wide-flatten-flatten-keys` (shared key-list semantics)
- Related: CIP-0012 (pivot views should follow the same pattern later)

## Progress Updates

### 2026-10-11

Task created (Ready) from CIP-0010 Phase 2b.

Implemented with Phase 2 helpers in `lynguine/access/io.py` and tests/docs. Marked Completed.
