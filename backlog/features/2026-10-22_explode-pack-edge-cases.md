---
id: "2026-10-22_explode-pack-edge-cases"
title: "CIP-0014 explode/pack follow-up: empty pack, inherit skip, parameter nulls"
status: "In Progress"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0014"]
owner: "lawrennd"
dependencies: ["2026-10-21_explode-units-to-rows"]
tags:
- backlog
- cip0014
- access
- explode
- pack
---

# Task: Explode/pack follow-up edges for packed corpus flows

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Land the CIP-0014 leftover WIP that was held back from the CIP-0016
Liquid-mapping PR. Packed-corpus Save paths need explode-then-pack from
chunk grain (without joining an already-tall output), empty packs as
empty arrays, missing inherit columns skipped with a warning, YAML
`keep_nulls` for parameter Series, `row_args` that name the frame index,
and parameter reconstruction that does not call `np.isnan(None)`.

Log sanitizer interpolation (`%d` after format, then redact) is in the
same working set because httpx status-code logs fire during these flows.

`file_catalog` stays on the original CIP-0014 task.

## Acceptance Criteria

- [x] Empty tall frames pack to empty arrays instead of aborting
- [x] Missing explode `inherit` columns are skipped with a warning
- [x] `output.explode` reads input/cache only (not already-tall output)
- [x] Pack without `source` explodes the chunk-grain table first
- [x] `save_flows` writes cache and parameter stores as well as output/pack
- [x] Parameter/constant `None` values round-trip (`keep_nulls`)
- [x] `row_args` may name the DataFrame index (explode identity)
- [x] SanitizingFormatter interpolates then redacts (httpx `%d` still works)
- [x] Tests for the above pass on this branch

## Implementation Notes

See [CIP-0014](../../cip/cip0014.md). This is not CIP-0016 (Liquid
mapping, merged) and not CIP-0015 phase 2 (parquet). Parquet stays a
separate encoding task.

## Related

- CIP: 0014
- Depends on: `2026-10-21_explode-units-to-rows`
- Held back from: CIP-0016 PR #47

## Progress Updates

### 2026-10-22

Task created to track leftover explode/pack WIP after CIP-0016 merged.
Restored `data.py` helpers that had been stripped so the Liquid PR stayed
clean (`_explode_source_frame`, `_explode_output_for_pack`,
`_parameter_series_for_write`, None-safe parameter distribution).
