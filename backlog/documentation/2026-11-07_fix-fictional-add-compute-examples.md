---
id: "2026-11-07_fix-fictional-add-compute-examples"
title: "Fix fictional function: add compute examples in docs"
status: "Proposed"
priority: "Medium"
created: "2026-11-07"
last_updated: "2026-11-07"
category: "documentation"
related_cips: ["0007"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- documentation
- compute
- vongole
---

# Task: Fix fictional `function: add` compute examples

> Companion to (not replacement of)
> `2026-10-18_align-compute-framework-docs-vongole-intent`.
> Documentation only — no registry changes in lynguine.

## Description

Lynguine’s live `_compute_functions_list` does **not** register `add`,
`multiply`, or other arithmetic. README and `docs/compute_framework.md`
still show YAML examples with `function: add`, which invents a registry name.

Fix those examples so they either:

1. Use a real lynguine access-compute name (`render_liquid`, `today`,
   `document_segment`, …), or
2. Clearly label assessment examples as **referia-today / vongole-target**
   (e.g. `sum`, and future numeric primitives).

Cross-link:

- referia interim feature:
  `referia/backlog/features/2026-11-07_yaml-numeric-compute-primitives.md`
- vongole inventory:
  `backlog/infrastructure/2026-10-18_inventory-referia-compute-for-vongole.md`
- CIP-0007 assessment-compute placement

## Acceptance Criteria

- [ ] No undocumented claim that lynguine registers `add` / `multiply` / similar
- [ ] `README.md` and `docs/compute_framework.md` examples are honest about
      live vs intended stacks
- [ ] Assessment arithmetic examples point at referia (interim) / vongole (target)
- [ ] Related Work or notes link the referia numeric primitives backlog and the
      2026-10-18 vongole inventory task
- [ ] Does not supersede or close `2026-10-18_align-compute-framework-docs-vongole-intent`;
      may be done as a focused slice of that cleanup

## Implementation Notes

- Prefer short “Live / Target” callouts over rewriting history.
- Count of lynguine registered functions is currently **six** (not five); keep
  the list accurate when touching that section.
- Do not add arithmetic to lynguine’s registry as part of this task.

## Related

- CIP: 0007
- Companion: `2026-10-18_align-compute-framework-docs-vongole-intent`
- Inventory: `2026-10-18_inventory-referia-compute-for-vongole`
- Referia feature: `2026-11-07_yaml-numeric-compute-primitives`
- Referia docs: `2026-11-07_document-numeric-compute-primitives`

## Progress Updates

### 2026-11-07

Task created after compute inventory found fictional `function: add` examples
in lynguine docs.
