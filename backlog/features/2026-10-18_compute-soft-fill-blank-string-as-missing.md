---
id: "2026-10-18_compute-soft-fill-blank-string-as-missing"
title: "Soft fill: treat blank strings as missing when refresh is false"
status: "Proposed"
priority: "Low"
created: "2026-10-18"
last_updated: "2026-10-18"
category: "features"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- compute
- soft-fill
- documentation
---

# Task: Soft fill — blank string as missing

## Description

lynguine compute soft fill (`refresh: false`) only treats a cell as missing when the column is absent or `isna(value)` is true. An empty string `""` is treated as present, so soft fill will not overwrite it.

That surprises review UIs that clear a field to `""` and expect a later PDF/access suggestion to refill the cell. Documented as a caveat in `docs/compute_framework.md` (Refresh Behavior). This task is the optional **behaviour change** if we want blank (and perhaps whitespace-only) strings to count as missing for soft-fill write decisions.

## Acceptance Criteria

- [ ] Spec agreed: which values count as missing for soft fill (`""`, whitespace-only, empty list, …) without breaking intentional empty-string storage
- [ ] `Compute.run` / write gate updated consistently for `refresh: false` replace mode
- [ ] Tests for: null filled; `""` filled (new); non-empty preserved; `refresh: true` still overwrites
- [ ] `docs/compute_framework.md` caveat updated to match new behaviour
- [ ] Brief note in changelog / CIP compression notes if behaviour is user-visible

## Implementation Notes

- Current gate: `lynguine/assess/compute.py` (`missing_vals` via `isna` only).
- Prefer an explicit opt-in flag (e.g. `fill_if_empty: true` or `missing_as: [null, blank]`) if changing global default is too breaking; otherwise change default and call out in release notes.
- Motivating consumer: referia Panel soft fill from `extract_form_fields` / CIP-0013 `form_fields`.

## Related

- Docs: `docs/compute_framework.md` (Refresh Behavior / Soft fill)
- Backlog: `2026-10-18_document-form-fields-cam-panel-v1`

## Progress Updates

### 2026-10-18

Task created (Proposed) after documenting the soft-fill pattern and the `""` vs `isna` caveat. No implementation until the footgun shows up in Panel review practice.
