---
id: "2026-10-11_wide-unflatten"
title: "wide_unflatten for materialized round-trip (Pattern B)"
status: "Ready"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-core-helper"
- "2026-10-11_wide-flatten-flatten-keys"
tags:
- backlog
- features
- access
- wide-flatten
- unflatten
- cip0010
---

# Task: wide_unflatten for materialized round-trip (Pattern B)

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-0010 Phase 2c: implement `wide_unflatten_dataframe` — inverse of materialized `wide_flatten` — for tests, Pattern B flows, and any case where a wide frame must become tall before `write_data`.

**Not** the default Save path for catalogs (Pattern A / virtual view is). Secondary under tenet `authoritative-store-and-views`.

## Acceptance Criteria

- [ ] `wide_unflatten_dataframe(wide, …)` recovers tall frame from a Phase-1/2a wide row
- [ ] Honours `separator`, `order`, and skips / handles `flattenKeys` (and configurable keys field)
- [ ] Round-trip: unflatten(flatten(df[columns])) matches original values for unique index
- [ ] Clear errors on ambiguous parse / separator violations
- [ ] Unit tests for happy path, keys field exclusion, error cases
- [ ] Docs state Pattern B / round-trip role — not default editable store

## Implementation Notes

- Live next to `wide_flatten_dataframe` in `lynguine/access/io.py`
- Optional later: access wiring only if a flow type needs it; helper + tests may be enough for v1 inverse

## Related

- CIP: 0010
- Tenet: `authoritative-store-and-views`
- Depends on: core helper + flattenKeys

## Progress Updates

### 2026-10-11

Task created (Ready) from CIP-0010 Phase 2c.
