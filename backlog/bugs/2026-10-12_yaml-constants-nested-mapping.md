---
id: "2026-10-12_yaml-constants-nested-mapping"
title: "read_yaml cannot load nested mappings as single-row constants"
status: "Completed"
priority: "High"
created: "2026-10-12"
last_updated: "2026-10-12"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- access
- yaml
- constants
- referia
---

# Bug: `read_yaml` cannot load nested mappings as single-row constants

## Description

`lynguine.access.io.read_yaml` only treats a YAML mapping as a single-row constants table when **every** top-level value is a scalar:

```python
if isinstance(data, dict) and all(not isinstance(v, (list, dict)) for v in data.values()):
    index_name = details.get("index", "value")
    return pd.DataFrame(data, index=[index_name])

return pd.DataFrame(data)  # fails for nested config maps
```

Real site/config files (e.g. Jekyll `_config.yml` in `~/lawrennd/talks`) mix scalars with nested maps and lists (`ghub`, `author`, `plugins`, `exclude`, …). Loading them as referia/lynguine `constants:` then raises:

```text
ValueError: All arrays must be of the same length
```

from `pd.DataFrame(data)`.

**Triggering use case:** talks calendar `_referia.yml` wants constants reverse-engineered from `_config.yml` (`github_username`, `ghub.repository`) to build per-talk GitHub edit URLs. Worked around with `type: local` duplicating those values until this is fixed.

Markdown constants already wrap a single document as one row (`pd.DataFrame([data])`). YAML constants should support the same “one config document → one row” pattern, with optional `fields` / liquid projection to flatten nested keys.

## Acceptance Criteria

- [x] A YAML mapping with nested dict/list values can be loaded as a **single-row** DataFrame (constants / parameters use case)
- [x] Optional `fields` (including liquid) can project nested paths into flat columns (e.g. `ghub.repository` → `github_repository`) before or after the row is formed
- [x] All-scalar YAML maps keep current behaviour (no regression)
- [x] YAML sequences of mappings (multi-row tables) keep current behaviour (no regression)
- [x] Clear error if the document is neither a mapping nor a sequence of mappings
- [x] Unit tests cover: nested Jekyll-like `_config.yml` fixture; scalar-only map; list-of-maps table
- [x] Documented in lynguine data-source docs (constants from nested YAML)

## Implementation Notes

Likely approaches (pick one and document):

1. **Single-document row** (mirror `read_markdown`): if top-level is a `dict`, always `pd.DataFrame([data])` so nested values remain cell objects (dicts/lists) accessible to liquid as `ghub.repository`.
2. **Opt-in** via details flag, e.g. `row: document` / `scalar_row: true`, so existing callers that rely on `pd.DataFrame(data)` column expansion are unchanged.
3. **Field projection first**: when `fields` is present, evaluate liquid / named fields against the raw mapping, then build an all-scalar single-row frame (fits today’s scalar-only path).

Prefer (1) or (3) for referia `constants:` ergonomics. Avoid silently expanding nested keys into misaligned columns.

Related compute note (may be separate backlog): constants columns are **not** available as `row_args` during input `finalize_data` compute — they must be passed as `args` parameter values or joined later. Fixing load alone does not auto-wire constants into input compute `row_args`.

## Related

- Discovered from: `~/lawrennd/talks/_referia.yml` (talks calendar overview)
- Code: `lynguine/access/io.py` `read_yaml`
- Contrast: `read_markdown` → `pd.DataFrame([data])`
- Workaround in talks: `constants: type: local` with duplicated github_* fields

## Progress Updates

### 2026-10-12

Bug confirmed while wiring GitHub edit URLs for talks overview. Task created Ready.

### 2026-10-12 (implemented)

`read_yaml` now loads any top-level mapping as a single-row frame (nested values as cell objects); optional `fields` supports keys, dotted `path`, and `liquid`. Tests and README YAML section updated. Marked Completed.
