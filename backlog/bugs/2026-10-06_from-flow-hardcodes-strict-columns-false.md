---
id: "2026-10-06_from-flow-hardcodes-strict-columns-false"
title: "from_flow hardcodes strict_columns=False for input loads"
status: "Ready"
priority: "High"
created: "2026-10-06"
last_updated: "2026-10-06"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- from_flow
- strict_columns
- data
- layering
---

# Bug: `from_flow` hardcodes `strict_columns=False` for input loads

## Description

In `CustomDataFrame.from_flow`, when loading an **input** data source the
call forces permissive column checking:

```python
# lynguine/assess/data.py (input branch)
newdf = cdf._finalize_df(*access.io.read_data(item), strict_columns=False)
```

Non-input branches omit the kwarg:

```python
newdf = cdf._finalize_df(*access.io.read_data(item))
```

but `_finalize_df` itself defaults `strict_columns=False`, so the same
permissive behaviour applies unless a caller passes an explicit value.

Application layers (notably referia) override `_finalize_df` to resolve
`strict_columns` from YAML and dialect policy when the argument is `None`
(v1 → permissive, v2 → strict). Because `from_flow` always passes
`False` for inputs, that resolution never runs on the main load path.
Explicit `strict_columns: true` in a config is also ignored for input
loads.

Discovered while validating referia CIP-000F dialect defaults: unit-level
`_resolve_strict_columns` is correct, but end-to-end `from_flow` /
`WebReviewer` loads still accept undeclared Excel columns under stamped
v2 configs.

## Acceptance Criteria

- [ ] Input loads in `from_flow` do **not** hardcode `strict_columns=False`.
      Prefer passing `None` (or omitting the kwarg after changing the
      default) so `_finalize_df` / subclasses can resolve policy.
- [ ] Lynguine’s own default when neither YAML nor caller specifies a
      value remains **permissive** (`False`) — no surprise breakage for
      existing lynguine-only configs.
- [ ] When the data-spec or top-level interface sets
      `strict_columns: true|false`, `from_flow` honours that for input
      loads.
- [ ] Subclasses that treat `strict_columns is None` as “resolve myself”
      (referia dialect defaults) see `None` on the input path, not
      forced `False`.
- [ ] Unit tests cover:
      - input load with no key → permissive (lynguine default)
      - input load with `strict_columns: true` + undeclared column → raises
      - input load with `strict_columns: false` + undeclared column → loads
      - subclass override receiving `None` on input load (mock or thin
        subclass)

## Implementation Notes

Touchpoints in `lynguine/assess/data.py`:

1. `from_flow` input branch (~line 1161): stop passing
   `strict_columns=False`. Options:
   - Pass `item.get("strict_columns")` if present, else `None`
   - Or always pass `None` and let `_finalize_df` read the interface
2. `_finalize_df` / `_finalize_ds` signature default: consider
   `strict_columns=None` instead of `False`, with lynguine resolving
   `None` → `False` (or interface value) inside the method so behaviour
   stays explicit.

Keep lynguine explicit and predictable: document that the default policy
is permissive, and that callers/YAML must opt into strict mode. Do not
import referia dialect rules into lynguine.

## Related

- Referia completed: `backlog/bugs/2026-10-06_strict-columns-duplicate-excel-headers.md`
  (dialect-aware defaults in referia’s `_finalize_df` override)
- Referia CIP-000F (config dialect versioning)
- Tenet: progressive augmentation / explicit infrastructure — referia
  should not need to fork `from_flow` to get its defaults applied

## Progress Updates

### 2026-10-06

Bug identified during referia test-plan validation of stamped v2
`strict_columns` behaviour. Policy helpers pass; `from_flow` input path
forces `False`.
