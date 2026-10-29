---
id: "2026-10-28_cip0018-bind-directory-sources"
title: "Bind inherited glob/directory sources to inherit.directory"
status: "Completed"
priority: "High"
created: "2026-10-28"
last_updated: "2026-10-28"
category: "features"
related_cips: ["0018"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- inherit
- directory
- yaml_directory
- cip0018
---

# Task: Bind inherited glob/directory sources to inherit.directory

> Linked CIP: 0018. Consumer: referia CIP-001C sibling Today/Year views.

## Description

`Interface._bind_spec_directory` rewrites relative `directory` only when the spec has `filename`. Catalog `yaml_directory` sources have `directory` + `glob` and are skipped. A child that inherits the catalog therefore discovers from its own directory.

Extend the bind gate to path-allocating specs (`filename` **or** `glob`) and keep the existing rewrite rules (empty → inherit.directory; relative → join; absolute unchanged).

## Acceptance Criteria

- [ ] Specs with `glob` and relative `directory` (including `.`) resolve against `inherit.directory`
- [ ] Specs with `filename` still bind as today (`test_from_file_inherit_binds_parent_data_directory` still passes)
- [ ] Nested `input.source[]` entries are rebound (recursion already walks lists)
- [ ] A spec with neither `filename` nor `glob` is not rewritten
- [ ] Absolute directories remain unchanged
- [ ] `from_flow` on a child inherit reads files from the parent tree, not the child
- [ ] Inherited output `filename` + relative `directory` still binds (regression: shared score file)

## Implementation Notes

- Touch: `lynguine/config/interface.py` — `_bind_spec_directory`
- Do not special-case `yaml_directory` or `_referia.yml`
- Tests: tmp_path parent catalog with glob source + child inherit; no referia fixtures
- Writable inherit (`inherit.writable: true`) is existing lynguine behaviour; this task only asserts directory bind, not referia's `reuse` opt-in

## Related

- CIP: 0018
- REQ-000F
- referia CIP-001C
- Precedent: `test_from_file_inherit_binds_parent_data_directory`

## Progress Updates

### 2026-10-28

Task created (Ready) from CIP-0018. Blocks referia Today/Year from sharing catalog discovery.
