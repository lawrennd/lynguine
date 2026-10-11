---
id: "000C"
title: "Singleton and composed frames use an explicit wrapping index"
status: "In Progress"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
related_tenets:
- explicit-infrastructure
- authoritative-store-and-views
stakeholders:
- Library users
- Application developers
- Review authors
tags:
- requirement
- index
- access
- singleton
- composition
- wide-flatten
---

# REQ-000C: Singleton and composed frames use an explicit wrapping index

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

When an access step produces a **one-row** frame — scalar YAML/`local`, `stack`, and reshapes such as `wide_flatten` — the resulting row must carry an **explicit index label** declared with the same wrapping key used elsewhere: `index` on that step’s details. Silent labels such as integer `0` or the string `"value"` must not be the documented or preferred path for new configuration.

The wrapping `index` names the **result** of that step. Identity used *inside* a nested multi-row source (the tall key before a reshape) lives on the nested specification or on that tall frame, not under a second top-level synonym (for example inventing `result_index`). Composition types remain consistent with each other: authors learn one key.

Multi-row sources already declare which column is the index; this requirement does not rename common labels such as `Name`. It closes the gap where singletons and wrappers diverge from that explicit practice.

**Why this matters**: *Explicit infrastructure* forbids magic defaults that hide data identity. *Authoritative store and views* needs a named singleton when a wide snapshot or composed constants row is the presentation identity of a flow.

**Who benefits**: Config authors writing `_referia.yml` / lynguine access blocks; maintainers debugging one-row vs multi-row frames; applications that hide navigation when there is only one index choice.

## Acceptance Criteria

- [ ] One-row results from access composition/reshape steps expose a configured index label via wrapping `index` (not an undocumented second key)
- [ ] New documentation and examples do not introduce synonyms such as `result_index` for the same role as wrapping `index`
- [ ] Tall / pre-reshape identity (when needed) is declared on the nested source or tall frame, distinct from the outer result label
- [ ] Undocumented defaults (`0`, `"value"`) are deprecated for new configs; behaviour for legacy configs remains defined and documented
- [ ] Error or validation guidance makes a missing singleton `index` discoverable when the step is one-row by design

## Notes

Survey of OneDrive referia configs (2026-10-11): wrapping `index` is ubiquitous (`Name`, `index`, …); `result_index` appeared only in a draft mock. `stack` / `hstack` / `local` already use outer `index`; `wide_flatten` currently overloads outer `index` as the tall column to promote before flatten — that overload is a HOW concern for CIP-0010 (align with this WHAT).

## References

- **Related Tenets**: `explicit-infrastructure`, `authoritative-store-and-views`
- **Implementing CIPs**: link from CIP `related_requirements` (expected: lynguine CIP-0010; possibly a small follow-on if Close needs a dedicated index pass)

## Progress Updates

### 2026-10-11
Requirement drafted from index/`result_index` survey and singleton-nav discussion. Status Proposed.

### 2026-10-11 (later)
Marked **Ready**. Implementing HOW: lynguine CIP-0010 Phase 3 (wrapping `index` = singleton result label; tall key nested).

### 2026-10-11 (backlog)
Marked **In Progress**. Backlog: `2026-10-11_wide-flatten-wrapping-index`, `2026-10-11_wide-flatten-wrapping-index-tests-docs`.
