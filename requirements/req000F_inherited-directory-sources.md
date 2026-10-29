---
id: "000F"
title: "Inherited directory sources resolve from the parent and can exclude paths"
status: "Validated"
priority: "High"
created: "2026-10-28"
last_updated: "2026-10-28"
related_tenets:
- explicit-infrastructure
- flow-based-processing
- authoritative-store-and-views
stakeholders:
- Application developers
- Configuration authors
- Referia catalog overviews
tags:
- requirement
- access
- directory
- inherit
- discovery
- yaml_directory
---

# REQ-000F: Inherited directory sources resolve from the parent and can exclude paths

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

When a configuration inherits another configuration, **directory-of-files sources** in the parent must resolve against the **parent's directory**, not the child's. Filename sources already behave this way. Directory sources (`directory` plus `glob`, no `filename`) must match that contract so a child view can reuse a catalog without discovering from the wrong tree or writing a second store.

Authors must also be able to **omit matched paths** from a directory source with an explicit, generic rule. A catalog that auto-discovers descendant configs should be able to hide view configs nested under that tree (for example sibling Today and Year reviews) without listing every include directory and without teaching infrastructure about application overview names.

Default behaviour of existing directory sources stays unchanged: no new excludes, and filename-only inherit bind remains as today.

**Why this matters**: *Explicit infrastructure* — relative `.` on an inherited source must mean one documented directory. *Flow-based processing* — bind and omit happen during inherit/flow, not as application path rewriting. *Authoritative store and views* — several configs can present the same discovered store; views are not extra rows in that store.

**Who benefits**: Application authors who inherit a `yaml_directory` (or sibling directory type) catalog as a view; referia CIP-001C sibling Today/Year overviews are the first consumer.

## Acceptance Criteria

- [x] An inherited directory source whose `directory` is relative (including `.`) is resolved against the inherited configuration's directory, matching inherited filename sources
- [x] A child configuration that inherits a directory catalog therefore discovers the same files the parent would, not files under the child's own directory
- [x] Authors can omit matched paths from a directory source using explicit exclude patterns on that source (or equivalent generic details key)
- [x] Absent exclude keeps today's match set (`recursive`, `glob`, `include_start_directory`, `regexp` unchanged)
- [x] Exclude is generic (no knowledge of `_referia.yml`, `today/`, or other application names)
- [x] Path confinement (allowed roots) still applies to every kept path
- [x] Applications do not reimplement inherit path rewrite or discovery omit for these outcomes

## Notes

Filename specs with `directory: .` already bind to `inherit.directory` (`test_from_file_inherit_binds_parent_data_directory`). This requirement extends that outcome to specs that allocate by `glob` rather than `filename`.

Listing work directories as separate `source` entries remains a valid YAML alternative to exclude. Exclude is required when the catalog must keep auto-picking new top-level folders without enumerating them.

## References

- Tenet: [explicit-infrastructure](../tenets/lynguine/explicit-infrastructure.md)
- Tenet: [flow-based-processing](../tenets/lynguine/flow-based-processing.md)
- Tenet: [authoritative-store-and-views](../tenets/lynguine/authoritative-store-and-views.md)
- Related: [REQ-0002](./req0002_predictable-architecture.md), [REQ-0005](./req0005_config-flexibility.md), [REQ-0006](./req0006_clear-architectural-boundaries.md)
- CIP-000F (recursive directory + field projection; `include_start_directory`)
- Downstream: referia CIP-001C (sibling Today/Year catalog views)

## Progress Updates

### 2026-10-28

Requirement created (Ready → In Progress). Paired with CIP-0018. Consumer: referia CIP-001C cannot share a catalog `yaml_directory` source or hide view configs from discovery until this outcome holds.

### 2026-10-28 (validated)

CIP-0018 Closed after referia `/today/` verification. Status Validated.
