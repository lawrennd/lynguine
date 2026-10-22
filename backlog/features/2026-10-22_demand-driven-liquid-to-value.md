---
id: "2026-10-22_demand-driven-liquid-to-value"
title: "Make liquid_to_value demand-driven"
status: "Completed"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0016"]
owner: "lawrennd"
dependencies:
- "2026-10-22_mapping-names-subset"
- "2026-10-22_liquid-root-identifiers"
tags:
- backlog
- cip0016
- liquid
- mapping
---

# Task: Make liquid_to_value demand-driven

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

When `liquid_to_value` is not given kwargs, bind only root identifiers
the template names (plus `local`). Empty identifier set renders with
`local` only — no `get_value`. Parse failure logs WARNING and falls back
to full `mapping()`. `view_to_value` must not eagerly call full
`mapping()` before a liquid view, or referia still pays the packed-row
cost.

A template mentioning only `title` must not contain `embeddings` in the
render context. A template that names `embeddings` still receives it.

## Acceptance Criteria

- [x] kwargs omitted: identifiers → `mapping(names=...)` → merge `local` → render
- [x] Empty identifier set → render with `local` only (no `get_value`)
- [x] Parse failure → WARNING + full `mapping()`
- [x] `liquid_to_value` does not `get_value` unmentioned columns
- [x] Mentioned packed-like arrays are still returned
- [x] `view_to_value` liquid path does not pre-build the full-row mapping

## Implementation Notes

See [CIP-0016](../../cip/cip0016.md) Implementation Plan step 4. Treat
`kwargs is None` and `kwargs == {}` as omitted. Referia
`render_viewer_html` calls `view_to_value` with no kwargs.

## Related

- CIP: 0016

## Progress Updates

### 2026-10-22

CIP-0016 accepted. Task created.

### 2026-10-22

Implemented demand-driven `liquid_to_value` and stopped `view_to_value` from eagerly calling full `mapping()`.
