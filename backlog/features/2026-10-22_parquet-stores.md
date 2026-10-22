---
id: "2026-10-22_parquet-stores"
title: "CIP-0015 phase 2: parquet Access stores"
status: "In Progress"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0015"]
owner: "lawrennd"
dependencies: ["2026-10-21_gzip-yaml-stores"]
tags:
- backlog
- cip0015
- access
- parquet
- pyarrow
---

# Task: Parquet named stores through read_data / write_data

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement CIP-0015 phase 2: `type: parquet` on the same named-store
contract as YAML/JSON. Optional extra `lynguine[parquet]` → pyarrow.
Embedding columns round-trip as Arrow `list<float32>`, not pickle-in-an-object-column.
`store_stat` reports `logical_type: parquet` and the parquet codec
(snappy by default, or zstd/gzip/…) without loading the table.

This is encoding, not CIP-0014 reshape and not CIP-0016 Liquid mapping.

## Acceptance Criteria

- [x] `type: parquet` in `read_data` / `write_data`
- [x] Extra `lynguine[parquet]` (pyarrow); missing extra raises an install hint
- [x] Phrase table with a float list column round-trips as `list<float32>`
- [x] `store_stat` for missing and written `.parquet` files
- [x] `extract_file_type("phrases.parquet")` is parquet
- [x] CI installs the parquet extra

## Implementation Notes

See [CIP-0015](../../cip/cip0015.md) encoding ladder. Default parquet
codec is snappy via `compress:` (parquet's own codecs, not gzip-wrapped
YAML). npy/hstack remains later if list columns are not enough.

## Related

- CIP: 0015
- Depends on: `2026-10-21_gzip-yaml-stores`

## Progress Updates

### 2026-10-22

Task created. Branch `cip0015-parquet-stores` from main after CIP-0014
follow-up PR #48. Wired `read_parquet` / `write_parquet` through
`read_data` / `write_data`, extra `lynguine[parquet]` (pyarrow 14–17 for
NumPy 1.x), `store_stat` codec from parquet metadata. Tests in
`test_parquet_stores.py`. Follow-up tests cover `read_auto`, declared
`list_columns`, named-index reset, uncompressed codec, missing-extra
read path, and `store_stat` when pyarrow cannot read metadata.
