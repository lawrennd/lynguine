---
author: "Neil D. Lawrence"
created: "2026-10-11"
id: "000F"
last_updated: "2026-10-11"
status: "Accepted"
compressed: false
related_requirements: ["0002", "0005", "0006"]
related_cips: ["0009", "000A"]
tags:
- cip
- access
- directory
- yaml
- allocation
- flow
- explicit-infrastructure
title: "Recursive directory discovery and field projection for YAML sources"
---

# CIP-000F: Recursive directory discovery and field projection for YAML sources

> **Note**: CIPs describe HOW to achieve requirements (WHAT).
> Use `related_requirements` to link to the requirements this CIP implements.

## Status

- [x] Proposed - Initial idea documented
- [x] Accepted - Approved, ready to start work
- [ ] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented (add reason, use superseded_by if replaced)
- [ ] Deferred - Postponed (use blocked_by field to indicate blocker)

## Summary

Extend lynguine directory allocation so nested trees of YAML (or other directory types) can be discovered with recursive globs, and so each file can contribute an **explicit projection** of fields rather than a full `json_normalize` of the document.

This keeps catalog-style flows (one row per config or document in a tree) inside the normal access → assess path, instead of forcing applications to invent parallel discoverers.

**Which requirements does this CIP address?** REQ-0002 (predictable, explicit flow), REQ-0005 (configuration flexibility), REQ-0006 (clear architectural boundaries — infrastructure stays generic; applications do not fork discovery).

**Downstream:** referia CIP-0010 depends on this CIP so a root `_referia.yml` can allocate rows from `**/_referia.yml` and drive a config-backed events/catalog page.

## Motivation

`yaml_directory` (and sibling directory readers) already turn a flat folder of YAML files into a DataFrame via `read_directory` → `glob.glob` → `read_files` → `json_normalize`. That is the right DOA shape for “files as rows,” but two gaps block tree-scale catalogs:

1. **Non-recursive globs.** `glob.glob(globname)` in `lynguine/access/io.py` does not walk nested directories. Patterns such as `**/_referia.yml` do not discover configs under `applications/2025-01-09_mphil-admissions/interviews/`.

2. **Full-document rows.** Each YAML is fully loaded and normalized. A referia (or any rich) config row explodes into `input.*`, `review.*`, `viewer.*`, … — noisy for a catalog that only needs `title`, `description`, `date`, `current`, plus path metadata from `store_fields`.

Application layers (e.g. referia’s web `_list_sub_configs`) already reimplement lightweight meta discovery outside the data plane. That bypasses flow-based processing and duplicates path confinement concerns already owned by CIP-000A.

Lynguine should provide **explicit, generic** recursive discovery and field projection so any consumer — referia events calendar, document indexes, multi-package YAML trees — uses the same allocation path.

## Detailed Description

### Design principles

- **Explicit over magic.** Recursive walk and field lists are opt-in keys in the source/details config. Default behaviour of existing flat `yaml_directory` stays unchanged.
- **Infrastructure stays generic.** No knowledge of `_referia.yml`, seasons, or web URLs. Callers name globs and field lists.
- **Path confinement unchanged.** Discovered paths continue through `confine_configured_path` / `allowed_roots` (CIP-000A). Recursion must not weaken the jail.
- **Flow-time processing.** Discovery remains inside `read_data` / directory readers used by `from_flow()`, not construction-time side effects.

### Configuration sketch

```yaml
input:
  type: yaml_directory
  source:
    - directory: .
      glob: "**/_referia.yml"
      recursive: true          # NEW: enable ** / rglob semantics
  fields:                      # NEW: project before normalize
    - title
    - description
    - date
    - current
  store_fields:
    directory: sourceDirectory
    filename: sourceFile
    root: sourceRoot
```

Equivalent keys may live on each `source` entry when different globs need different projections:

```yaml
source:
  - directory: applications
    glob: "**/_referia.yml"
    recursive: true
    fields: [title, description, date, current]
```

### Behaviour

| Key | Default | Effect |
|-----|---------|--------|
| `recursive` | `false` | When `true`, resolve globs with recursive semantics (`pathlib.Path.rglob` or `glob.glob(..., recursive=True)`). Document that `**` is meaningful only when `recursive: true`. |
| `fields` | absent | When absent: today’s full `yaml.safe_load` + `json_normalize`. When present: after load, keep only listed top-level keys (missing keys → null/absent); then normalize. Path `store_fields` still appended. |

Optional clarifying key (nice-to-have in the same CIP if cheap):

| Key | Values | Effect |
|-----|--------|--------|
| `load` | `full` (default) / `project` | Alternate spelling: `load: project` requires `fields`; `fields` alone implies project mode. Prefer documenting one canonical form (`fields` present ⇒ project). |

### Scope of types

Apply the same `recursive` / `fields` handling in the shared `read_directory` path so **all** directory readers benefit (`yaml_directory`, `json_directory`, `markdown_directory`, …). Field projection for non-mapping payloads (plain text) is a no-op or warning — document that `fields` applies to mapping-valued file readers.

`meta_directory` (sidecar `filename.yml`) is **out of scope**; it solves a different problem and stays as today.

### Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| referia-only `type: referia_catalog` wrapping web listing helpers | Bypasses lynguine allocation; teaches infrastructure about `_referia.yml`; harder for non-referia trees |
| Always recurse when `**` appears | Implicit; surprises users; harder to audit under CIP-000A |
| Separate new `type: yaml_tree` | Unnecessary type explosion; recursive flag on existing directory types is enough |
| Promote full configs then drop columns in compute | Works but wastes I/O and pollutes the access stage; projection belongs at read time when requested |

### Interaction with CIP-000A / CIP-0009

- Every matched path is confined before read (existing directory flow).
- Remote `source` blocks (CIP-0009) remain orthogonal: fetch/cache first, then local directory read with recursive/fields.

### Downstream contract for referia

referia CIP-0010 will use:

```yaml
input:
  type: yaml_directory
  source:
    - directory: .
      glob: "**/_referia.yml"
      recursive: true
  fields: [title, description, date, current]
```

plus Liquid grouping. Lynguine does not compute “in season”; that stays application-side.

## Implementation Plan

1. **Directory glob**
   - Thread `recursive` from each `source` entry (and optionally top-level `details`) into `read_directory`.
   - Use `glob.glob(pattern, recursive=True)` or equivalent `Path` API when set.
   - Log at debug: pattern, recursive flag, match count.
   - Skip common junk only if already skipped elsewhere; do **not** add hidden referia-specific ignores. Document that callers can narrow with `glob` / `regexp`.

2. **Field projection**
   - After the per-file reader returns a `dict`, if `fields` is set, replace with `{k: data.get(k) for k in fields}` (only for `dict` results).
   - Resolve `fields` from the active `source` entry, else `details`.
   - Preserve existing `store_fields` injection order (project content first, then add path fields; path field name collisions still error as today).

3. **Documentation**
   - README / Sphinx “Directory of Files” section: `recursive`, `fields`, examples.
   - Note default non-recursive compatibility.

4. **Release note**
   - Opt-in only; no break for existing configs.

## Backward Compatibility

- Default `recursive: false` and absent `fields` preserve current behaviour for all existing `*_directory` configs.
- Configs that assumed `**` worked without `recursive: true` were already ineffective; requiring the flag makes behaviour explicit rather than changing silent matches.

## Testing Strategy

- Unit tests in `lynguine/tests/test_access_io.py`:
  - Nested tree: `a/b/c.yml` matched only when `recursive: true` with `**/c.yml` (or `**/*.yml`).
  - Flat `*.yml` unchanged with `recursive` absent/false.
  - `fields: [title, date]` drops other keys; missing keys present as null/NaN consistently.
  - `store_fields` still populate directory/filename/root.
  - Path outside `allowed_roots` still raises (CIP-000A regression).
  - `regexp` filter still applies after recursive expansion.
- No referia fixtures in lynguine tests; use tmp_path trees only.

## Related Requirements

- [REQ-0002](../requirements/req0002_predictable-architecture.md) — explicit, predictable allocation behaviour
- [REQ-0005](../requirements/req0005_config-flexibility.md) — expressive configuration without ad-hoc code
- [REQ-0006](../requirements/req0006_clear-architectural-boundaries.md) — keep discovery in infrastructure, not application forks

Specifically, this CIP makes the following true:

- Nested YAML (or directory) trees can be allocated as one row per file through the normal flow
- Catalog-sized rows can request an explicit field list at read time
- Applications need not reimplement recursive filesystem discovery for DOA catalogs

## Implementation Status

- [ ] Thread `recursive` through `read_directory` / source entries
- [ ] Implement `fields` projection for mapping-valued readers
- [ ] Unit tests (recursive match, projection, confinement, regexp)
- [ ] Document Directory-of-Files options
- [ ] Release note (opt-in)

## References

- `lynguine/access/io.py` — `read_directory` (~L471), `read_files` (~L561), `directory_readers` / `yaml_directory`
- CIP-000A — constrained filesystem access
- CIP-0009 — config-driven remote access (orthogonal `source` fetch)
- referia CIP-0010 — config-driven catalog / events root (consumer)
- Tenets: explicit-infrastructure, flow-based-processing
