---
id: "2026-10-11_document-recursive-directory-fields"
title: "Document recursive directory globs and field projection"
status: "Ready"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "documentation"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_recursive-directory-glob"
- "2026-10-11_directory-reader-field-projection"
tags:
- backlog
- documentation
- access
- directory
- cip000F
---

# Task: Document recursive directory globs and field projection

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Document CIP-000F options for Directory-of-Files readers: `recursive` and `fields`, with examples and an explicit note that defaults preserve non-recursive, full-document behaviour. Add a short release note that the change is opt-in only.

## Acceptance Criteria

- [ ] README and/or Sphinx “Directory of Files” section documents `recursive` and `fields`
- [ ] Examples show nested glob + field projection (generic filenames, not referia-specific types)
- [ ] Docs state default `recursive: false` and absent `fields` = current behaviour
- [ ] Docs note that `**` is meaningful only with `recursive: true`
- [ ] Docs note that `fields` applies to mapping-valued readers
- [ ] Release note records opt-in, no break for existing configs

## Implementation Notes

- Formal docs may wait until CIP close/compression if Sphinx targets are unclear; at minimum update the user-facing Directory-of-Files material already in-tree
- Keep examples infrastructure-generic (no `_referia.yml` requirement in lynguine docs)

## Related

- CIP: 000F
- Depends on: feature tasks for recursive glob and field projection

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-000F implementation plan steps 3–4.
