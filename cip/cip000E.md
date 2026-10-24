---
author: "Neil D. Lawrence"
created: "2026-10-07"
id: "000E"
last_updated: "2026-10-24"
status: "Implemented"
compressed: false
related_requirements: ["0002"]
related_cips: []
tags:
- cip
- data-join
- to_pandas
- hstack
title: "Explicit column-overlap policy for flow joins (to_pandas and hstack)"
---

# CIP-000E: Explicit column-overlap policy for flow joins (to_pandas and hstack)

> **Note**: CIPs describe HOW to achieve requirements (WHAT).
> Use `related_requirements` to link to the requirements this CIP implements.

> **Accepted policy**: earlier wins; later colliding columns are dropped.
> Implementation matches that policy (`to_pandas` and `read_hstack`). Not Closed:
> formal docs compression waits until after Closed.

## Status

- [x] Proposed - Initial idea documented
- [x] Accepted - Approved, ready to start work
- [x] In Progress - Actively being implemented
- [x] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented (add reason, use superseded_by if replaced)
- [ ] Deferred - Postponed (use blocked_by field to indicate blocker)

## Summary

When lynguine joins multiple flows or hstack specifications that share column
names, pandas either raises (`columns overlap but no suffix specified`) or,
after a first suffix pass, raises again (`MergeError` recreating `col_right`).
Later colliding columns are dropped (“earlier wins”). This CIP records that
policy so join behaviour is explicit rather than a silent pandas error.

**Which requirements does this CIP address?** [REQ-0002](../requirements/req0002_predictable-architecture.md)
(predictable, explicit architecture).

## Motivation

Two call sites hit the same class of ambiguity:

1. **`CustomDataFrame.to_pandas()`** — outer-joins every non-parameter flow in
   `self._d`. Allocation/scores (and similar) often share identity columns
   (`givenName`, `crsid`, …). Without a policy, `DataFrame.join` raises.
2. **`read_hstack`** — joins specifications with default `rsuffix='_right'`.
   A second source sharing `crsid` yields `crsid_right`. A third source with
   `crsid` tries to create `crsid_right` again; recent pandas raises
   `MergeError`.

referia workarounds (e.g. `WebReviewer.get_row_data()` using per-column
`get_value()`) avoid `to_pandas()` for the web renderer, but any caller that
needs a combined frame still needs a defined lynguine policy. Leaving the
behaviour as an unreviewed working-tree change violates
explicit-infrastructure: the data-join rule should be a documented decision,
not silent drop logic.

## Detailed Description

### Problem

Joining frames that share column names is under-specified in lynguine today.
Callers cannot know whether:

- the join should fail loudly,
- both sides should be kept under suffixes,
- or one side should win and the other be dropped.

hstack’s default `_right` suffix only postpones the problem to the third
source.

### Accepted decision

**Policy: earlier wins; drop later colliding columns.**

| Site | Provisional behaviour |
|------|------------------------|
| `to_pandas()` | Before `join(how="outer")`, drop from the right any columns already present on the left. If the right has only overlapping columns, join an empty frame to keep index alignment. Parameter flows still use `assign`. |
| `read_hstack` | Before `join` / `merge`, drop right columns whose `{col}{rsuffix}` (or `{col}{lsuffix}` collision) already exists on the left. Two-way `B` → `B_right` behaviour unchanged. |

Documented in code comments/docstrings; regression tests cover two-way suffixes
and three-way collisions on both the index-join and merge (`on:`) paths.

### Alternatives to consider in review

1. **Earlier wins (current provisional)** — simple; may silently discard later
   identity columns (e.g. a third `crsid`).
2. **Later / output wins** — better if scores should override allocation for
   shared names; depends on `from_flow` insertion order of `self._d`.
3. **Flow-typed suffixes** (`_input`, `_output`) — keeps both sides; noisier
   columns; Liquid/mapping must know which suffix to use.
4. **Incremental suffixes** (`_right`, `_right2`, …) — avoids MergeError;
   column set grows with each join; still ambiguous for consumers.
5. **Fail loudly** — force configs to declare ignore/rename; most explicit,
   most breaking for existing referia YAML.

### Design constraints

- Behaviour must be **explicit and documented** (lynguine tenet:
  explicit-infrastructure).
- Prefer one policy language across `to_pandas` and `read_hstack` unless review
  finds a good reason to diverge.
- Do not change referia’s web `get_row_data()` back to `to_pandas()` as part of
  this CIP; that path correctly uses `get_value()`.

## Implementation Plan

1. **Review (this CIP, Proposed)**  
   - Choose among alternatives above.  
   - Record the Accepted policy in this document.

2. **Align working tree**  
   - Keep, adjust, or replace the provisional drop helpers to match the Accepted
     policy.  
   - Ensure docstrings and user-facing docs state the rule in one place.

3. **Tests**  
   - Keep/extend regressions for two-way and three-way overlaps.  
   - Add a case that encodes the Accepted winner (earlier vs later vs suffix).

4. **Commit via backlog**  
   - Close or complete backlog items only after Accept + implementation match.

## Backward Compatibility

Any chosen policy changes what columns appear in combined frames. Existing
configs that accidentally relied on pandas raising (or on an older suffix
behaviour) may change silently under “drop” policies. Prefer documenting the
rule and adding tests over silent flips after Accept.

## Testing Strategy

- Unit: `to_pandas` overlapping flows; `read_hstack` two-way suffix; three-way
  collision under the Accepted policy.
- Integration smoke (referia, optional): Queens students hstack configs;
  finances/institutions allocation+scores style joins.

## Related Requirements

- [REQ-0002](../requirements/req0002_predictable-architecture.md) — explicit, predictable join behaviour

## Implementation Status

- [x] Problem and provisional decision written up (this CIP)
- [x] **Review**: Accept the “earlier wins” policy (2026-10-24)
- [x] Working tree aligned to Accepted decision
- [x] Backlog items updated after Accept
- [ ] Formal docs compression after Closed (if needed)

## References

- Backlog: [2026-08-19_to-pandas-overlapping-columns](../backlog/bugs/2026-08-19_to-pandas-overlapping-columns.md)
- Backlog: [2026-10-07_hstack-repeated-rsuffix-collision](../backlog/bugs/2026-10-07_hstack-repeated-rsuffix-collision.md)
- Code (provisional): `lynguine/assess/data.py` (`to_pandas`),
  `lynguine/access/io.py` (`_drop_join_suffix_collisions`,
  `_drop_merge_suffix_collisions`)
- Tenet: explicit-infrastructure

## Progress Updates

### 2026-10-07

Proposed. Working-tree earlier-wins helpers existed; CIP recorded them as
provisional pending review.

### 2026-10-24

Accepted earlier-wins for both `to_pandas` and `read_hstack`. Added a three-way
merge-path regression. Status → Implemented. Pause before Closed / compression.
