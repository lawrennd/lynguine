---
id: "2026-10-22_liquid-mapping-index-cache"
title: "Cache subset mappings for the current index"
status: "Ready"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0016"]
owner: "lawrennd"
dependencies:
- "2026-10-22_demand-driven-liquid-to-value"
tags:
- backlog
- cip0016
- liquid
- mapping
- cache
---

# Task: Cache subset mappings for the current index

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Memoize subset maps so sibling Liquid blocks on one HTMX GET do not
rebuild the same subset. Cache key is `(get_index(), frozenset(names))`.
Invalidate on `set_index`, `set_value`, and `from_flow`. Document that
the cache is a per-object render memo, not a second data store.

## Acceptance Criteria

- [ ] Two `liquid_to_value` calls naming `store_status` on the same index call `get_value` once
- [ ] Cache miss after `set_value`
- [ ] Cache miss after `set_index`

## Implementation Notes

See [CIP-0016](../../cip/cip0016.md) Implementation Plan step 5. `from_flow`
is a classmethod that returns a new object, so a new instance starts with
an empty cache; still clear if any in-place reload path exists.

## Related

- CIP: 0016

## Progress Updates

### 2026-10-22

CIP-0016 accepted. Task created.
