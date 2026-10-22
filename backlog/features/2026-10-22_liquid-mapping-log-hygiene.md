---
id: "2026-10-22_liquid-mapping-log-hygiene"
title: "Stop interpolating cell values in mapping debug logs"
status: "Completed"
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
- liquid
- mapping
- logging
---

# Task: Stop interpolating cell values in mapping debug logs

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Eager f-string interpolation in `mapping()` / `liquid_to_value` debug logs
stringifies every cell even when the logger is at WARNING. On a packed
corpus row that costs about 1.4s over `get_row_data()`. Replace with lazy
`%s` logging of names and types only. Same rule anywhere `mapping` /
`get_value` logs a cell.

## Acceptance Criteria

- [x] `mapping()` / `liquid_to_value` debug logs do not interpolate cell values
- [x] Logging at WARNING does not call `repr` on a large list cell (spy or a cell whose `__repr__` raises)

## Implementation Notes

See [CIP-0016](../../cip/cip0016.md) Implementation Plan step 1. Use
`log.debug("mapping %s type=%s", name, type(value).__name__)`. No
`f"{value}"`.

## Related

- CIP: 0016

## Progress Updates

### 2026-10-22

CIP-0016 accepted. Task created.

### 2026-10-22

Implemented. Logger formats lazily; mapping/get_value/set_value log names and types only.
