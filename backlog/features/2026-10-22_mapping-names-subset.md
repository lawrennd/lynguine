---
id: "2026-10-22_mapping-names-subset"
title: "Add mapping(names=...) subset fetch"
status: "Ready"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0016"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- cip0016
- mapping
- liquid
---

# Task: Add mapping(names=...) subset fetch

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Add an optional `names` argument to `CustomDataFrame.mapping()` so callers
can fetch only requested identifiers. No-arg `mapping()` remains the
full-row dict. Missing names are omitted (same as today's unmapped
columns). Keep the current KeyError when a requested name is in the map
and the column is absent.

## Acceptance Criteria

- [ ] `mapping(names=["store_status", "selected_doc"])` fetches only those names
- [ ] Existing no-arg `mapping()` tests unchanged
- [ ] Unmapped names omitted; mapped-but-missing-column still KeyError

## Implementation Notes

See [CIP-0016](../../cip/cip0016.md) Implementation Plan step 2. The
existing `mapping={"store_status": "store_status", ...}` dict form stays.
Liquid will use `names=` after identifier extraction.

## Related

- CIP: 0016

## Progress Updates

### 2026-10-22

CIP-0016 accepted. Task created.
