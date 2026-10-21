---
id: "2026-10-21_explode-units-to-rows"
title: "Explode list fields to rows, pack columns to a corpus row, and optional file catalog"
status: "Proposed"
priority: "High"
created: "2026-10-21"
last_updated: "2026-10-21"
category: "features"
related_cips: ["0014"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- cip0014
- access
- explode
- pack
- catalog
- documents
---

# Task: Explode list fields to rows and pack columns to a corpus row

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement lynguine CIP-0014 so a flow can (1) explode a list field (e.g.
`units` from `document_segment`, or `extraction_phrases`) into a
one-row-per-item YAML store, (2) pack selected columns of a tall table into
**one corpus row of array fields**, and (3) optionally catalog local
PDF/DOCX files into a roster.

Explode and pack are Access IO write paths. They do not keep a DataFrame in
memory for the next notebook cell, and they are **not** Assess compute
(`pack_corpus_row` must not be registered in referia or vongole).

Do not change CIP-0013 segmenter design. `document_segment` still returns
`list[dict]` on the document row (cache). Do not reuse CIP-0010 wide-flatten
names: pack stacks column values into list/array cells, it does not mint
index-augmented column names.

## Acceptance Criteria

- [ ] `output.explode` in flow YAML expands a named list field into a tall
      table, inheriting declared parent columns
- [ ] Output index is `unit_id` (or the declared index); unit dict keys
      become columns
- [ ] `units_to_frame` is registered for programmatic callers; flows use
      `output.explode`
- [ ] `pack` write path stacks declared columns into aligned array cells on
      one row (`index_value` default `corpus`); missing embeddings abort
      unless `drop_incomplete: true`
- [ ] Optional `file_catalog` globs `*.pdf` / `*.docx` and infers `reader`
      from suffix; hand-written `documents.yml` remains valid
- [ ] No process-global frame; deleting the chunk or records store and
      re-running explode / pack recreates it
- [ ] CIP-0013 fixtures reused for explode; a three-row phrase table for pack

## Implementation Notes

See [CIP-0014](../../cip/cip0014.md). Referia drafts
`01_chunk/_referia.yml` (explode) and `02_embed/_referia.yml` (`pack` store)
name these clauses. Phrase-row explode after `llm_extract_phrases` reuses
the same write path.

Proposed only: do not implement until CIP-0014 is Accepted.

## Related

- CIP: 0014
- Depends on: CIP-0013 (`document_segment`, still In Progress)
- Consumer: referia REQ-0010 steps 1–3 and step 6

## Progress Updates

### 2026-10-21

Task created as Proposed from CIP-0014 (explode + catalog). Same day:
extended to pack (array columns), matching the CIP amendment that moved
pack out of referia CIP-0015.
