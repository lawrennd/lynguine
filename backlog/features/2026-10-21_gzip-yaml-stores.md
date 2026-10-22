---
id: "2026-10-21_gzip-yaml-stores"
title: "Gzip YAML/JSON Access stores and store_stat"
status: "In Progress"
priority: "High"
created: "2026-10-21"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0015"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- cip0015
- access
- gzip
- yaml
- json
---

# Task: Gzip YAML/JSON Access stores and store_stat

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement lynguine CIP-0015 v1: round-trip YAML/JSON stores through gzip
when the filename ends in `.gz` (or `compress: gzip` with a matching
suffix), and add `store_stat` for path/mtime/size/codec without loading
the table. Parquet remains phase 2.

## Acceptance Criteria

- [x] `.yml.gz` / `.json.gz` round-trip; logical type stays yaml/json
- [x] A `.yml` file whose bytes are gzip fails explicitly
- [x] `compress: gzip` with a non-`.gz` name fails
- [x] `store_stat` for missing, plain, and gzip files
- [ ] Phase 2 parquet (out of this task)

## Implementation Notes

See [CIP-0015](../../cip/cip0015.md). Encoding is Access IO, not compute.

## Related

- CIP: 0015

## Progress Updates

### 2026-10-21

CIP-0015 accepted. Gzip YAML/JSON and `store_stat` implemented; parquet deferred.

### 2026-10-22

Phase 2 parquet moved to
[2026-10-22_parquet-stores](./2026-10-22_parquet-stores.md).
