---
id: "2026-10-18_inventory-referia-compute-for-vongole"
title: "Inventory referia compute functions for vongole migration"
status: "Proposed"
priority: "High"
created: "2026-10-18"
last_updated: "2026-10-18"
category: "infrastructure"
related_cips: ["0007"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- infrastructure
- vongole
- compute
- inventory
---

# Task: Inventory referia compute for vongole

> Phase 0 inventory for CIP-0007. Classification only — no package creation until CIP-0007 is **Accepted**.

## Description

Produce a definitive table of every name in `referia.assess.compute.Compute._compute_functions_list` (including LLM extras) classified as:

| Bucket | Meaning |
|--------|---------|
| **lynguine** | Already access-level / stays in lynguine (or alias of one) |
| **vongole** | Assessment library — migrate when vongole exists |
| **referia** | Review-domain — stay in referia |
| **retire / alias** | Duplicate, hack, or rename candidate |

Seed list from the 2026-10-18 audit: NLP/PDF text helpers, aggregations, DF filter/sort/augment helpers, viz → vongole; generic `llm_*` + `LLMManager` → **vongole** (preferred; CIP-0004 retargeted); `llm_pdf_review` / `llm_custom_query` → referia; CIP-0013 extractors already lynguine.

## Acceptance Criteria

- [ ] Table covers every registered compute `name` in referia (non-LLM and LLM)
- [ ] Each row has: name, current module path, proposed bucket, notes
- [ ] Explicit row group for LLM: generic → vongole; review-domain → referia (per CIP-0004/0007 2026-10-18)
- [ ] Table checked into lynguine design space (preferred: subsection or appendix in CIP-0007, or `cip/cip0007/` notes) **or** linked from CIP-0007 Related Work
- [ ] No code moved as part of this task

## Implementation Notes

- Source of truth for names: `referia/assess/compute.py`
- Cross-check lynguine `_compute_functions_list` so we do not “migrate” CIP-0013 helpers
- Flag `bar_plot` (imported but unregistered) and `addsupervisor` hack if still present

## Related

- CIP: 0007 Phase 0
- Companion docs task: `2026-10-18_align-compute-framework-docs-vongole-intent`

## Progress Updates

### 2026-10-18

Task created with CIP-0007 revision. Ready once someone owns the inventory spreadsheet/table.
