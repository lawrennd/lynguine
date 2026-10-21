---
id: "000E"
title: "YAML and JSON stores can round-trip with explicit compression"
status: "Proposed"
priority: "High"
created: "2026-10-21"
last_updated: "2026-10-21"
related_tenets:
- explicit-infrastructure
- flow-based-processing
stakeholders:
- Referia review authors
- Dialogue / embedding pipelines
- Maintainers
tags:
- requirement
- access
- yaml
- json
- compression
- cache
- io
---

# REQ-000E: YAML and JSON stores can round-trip with explicit compression

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A flow can persist a YAML or JSON store in a compressed on-disk form and load it again as the same table, without a sidecar converter or a change of logical `type`. Compression is declared (filename suffix and/or store key), not sniffed as hidden magic. Uncompressed `.yml` / `.json` remain valid.

This is for named Access stores (input, cache, output, constants). It is not LLM client diskcache, and it is not a new analysis format: the bytes on disk are still YAML or JSON, wrapped in a standard compressor.

**Why this matters**: *Explicit infrastructure* keeps the store type `yaml` while making the on-disk encoding visible. *Flow-based processing* writes and reads during flow, not via an undeclared gzip step. Large cache and output tables (chunk text, LLM payloads, embedding lists, distance matrices) must not force uncompressed YAML as the only option.

**Who benefits**: Dialogue and embedding pipelines whose YAML caches would otherwise dominate disk; review authors who want git-friendly uncompressed YAML for small tables and compressed YAML for bulky ones.

## Acceptance Criteria

- [ ] A store with logical `type: yaml` (or `json`) can be written and read compressed; the in-memory table matches the uncompressed round-trip
- [ ] Compression is explicit: the filename suffix and/or a store key names the codec; a `.yml` file is not silently treated as gzip
- [ ] Uncompressed YAML/JSON configs continue to work unchanged
- [ ] Callers can ask for store file facts (path, exists, mtime, size, codec) without loading the whole table
- [ ] Missing compressed and uncompressed files fail the same way as today (absent store, not a silent empty cache)

## Notes

Suitable v1 codec is gzip (stdlib, YAML/JSON text compresses well). Other codecs may follow if declared the same way.

Numeric-heavy tables (embeddings, responsibility matrices, EMD) will still be the wrong *document* even when gzipped. Those stay the same named store with a different `type` (parquet as the binary table; npy only as a declared single-array column). That encoding is specified in CIP-0015’s ladder; it does not require a second cache system.

Does not replace named cache/output policy in the application (what belongs in cache vs output). Referia cache *visibility* in the review UI is a separate outcome (referia REQ-0011).

## References

- Tenet: [explicit-infrastructure](../tenets/lynguine/explicit-infrastructure.md)
- Tenet: [flow-based-processing](../tenets/lynguine/flow-based-processing.md)
- Related: [REQ-0005](./req0005_config-flexibility.md), [REQ-0002](./req0002_predictable-architecture.md)
- Consumer: referia [REQ-0010](https://github.com/lawrennd/referia/blob/main/requirements/req0010_dialogue-pipeline-in-referia.md), [REQ-0011](https://github.com/lawrennd/referia/blob/main/requirements/req0011_named-store-status.md)

## Progress Updates

### 2026-10-21

Requirement created (Proposed) from dialogue-pipeline cache size concerns. Paired with CIP-0015.
