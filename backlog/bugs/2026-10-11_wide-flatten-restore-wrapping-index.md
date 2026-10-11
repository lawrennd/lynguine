---
id: "2026-10-11_wide-flatten-restore-wrapping-index"
title: "wide_flatten read_data must restore wrapping index for _finalize_df"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "bugs"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bugs
- wide_flatten
- cip0010
---

# Task: Restore wrapping index after wide_flatten finalize

## Description

`read_data` for `type: wide_flatten` stripped wrapping `index` before `finalize_data` (so tall `columns` were not injected onto the wide row) but never put it back. `CustomDataFrame._finalize_df` then raised `Missing index field in data frame specification in interface file`, so referia root overview configs could not load.

## Acceptance Criteria

- [x] Returned interface from `read_data(wide_flatten)` still contains wrapping `index` when provided
- [x] Tall `columns` are still not injected onto the wide row
- [x] Unit test asserts `iface["index"] == "root"`

## Related

- CIP: 0010
- Discovered via referia OneDrive root `_referia.yml` smoke load

## Progress Updates

### 2026-10-11

Fixed in `lynguine/access/io.py`; test updated in `test_wide_flatten.py`.
