---
id: "authoritative-store-and-views"
title: "Authoritative Store and Views"
created: "2026-10-11"
last_updated: "2026-10-11"
version: "0.1"
status: "Proposed"
last_reviewed: "2026-10-11"
review_frequency: "Quarterly"
tags:
- tenet
- store
- view
- reshape
- assess
- access
- doa
---

# Authoritative Store and Views

## Tenet

**Description**: lynguine keeps an **authoritative store shape** that is explicit and what persistence sees. Presentation and edit aliases — wide names, Liquid-friendly layouts, pivot-like facades — are **views** (or disposable snapshots) over that store, not a silent replacement of it. Access may materialize frames when loading and combining sources; assess focuses and mutates through an explicit view API (`get_value` / `set_value` and typed `colspecs`). Reshapes that change how data is edited or saved must be named, documented, and either invertible or clearly lossy — never the default path for writable scores.

This does **not** mean “lynguine never builds a DataFrame.” Directory reads, `hstack` / `vstack`, and similar access steps allocate concrete rows. It means the **identity of editable, persisted data** stays the declared store (for example tall scores keyed by config path), while wide or pivoted *names* resolve into that store unless the flow explicitly opts into a materialized reshape and its write consequences.

**Quote**: *"Shape the store on purpose; treat wide names as a view"*

**Examples**:
- Catalog discovery stays **tall** (one row per config); Liquid lists keys via `flattenKeys` (or equivalent) and resolves `{key}{sep}{field}` through focus get/set into the tall frame
- `input` columns remain immutable; `output` / `cache` mutations go through the focused cell API and `write_data` persists those typed frames as shaped
- Access `type: wide_flatten` materializes a wide **snapshot** for templates or one-shot flows; it is not the default in-memory shape for editing `complete`
- Aggregating `pivot_table` is documented as lossy; editable “pivot-like” UX, if any, views the tall store rather than replacing it with aggregates
- Series nesting uses index + selector + subindex focus — a view over multi-row storage, not a flattened lossy dump as the source of truth

**Counter-examples**:
- Replacing the working `CustomDataFrame` with a materialized wide row so that Save writes `grant_a_complete`-style columns without an explicit unflatten policy
- Inferring loop keys by parsing wide column names in the application instead of emitting an ordered key list from infrastructure
- Treating `pivot_table` with aggregation as round-trippable for scores
- Hidden reshape-on-write so the on-disk schema silently tracks the UI layout
- Expecting infrastructure to “just know” that a Liquid flat dict is authoritative over the tall store

**Conflicts**:
- **vs Access materialization**: Loaders must still build concrete frames (`yaml_directory`, `hstack`, …)
  Resolution: Materialization at access is fine for allocation and joins; do not promote every reshape to the editable store identity. Prefer views/resolvers for presentation aliases.
- **vs Explicit Infrastructure**: A “smart” auto-unflatten on Save can look convenient
  Resolution: Keep Save behaviour predictable — write the store as shaped; if a flow uses a materialized wide working set, name the inverse (`wide_unflatten`) or forbid that pattern for writable data.
- **vs Flow-Based Processing**: Snapshots for address/Liquid may look like a second store
  Resolution: Treat snapshots as read-only presentation unless the flow defines an explicit write-back; processing stages stay access → assess → address with one authoritative assess store.
- **vs User Convenience**: Apps want `{{grant_a_title}}` without thinking about tall rows
  Resolution: Provide name resolution and key lists in infrastructure; keep convenience in the view layer, not by mutating store shape by default.

## Related

- [Explicit Infrastructure](./explicit-infrastructure.md) — views and reshapes must be named, not magical
- [Flow-Based Processing](./flow-based-processing.md) — access may allocate; assess views; address must not invent a second truth
- CIP-0010 — wide flatten: Pattern A (tall store + virtual wide) vs Pattern B (materialized)
- CIP-0012 — pivot / pivot_table invertibility review
