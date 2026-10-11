---
id: "2026-10-11_document-recursive-directory-fields"
title: "Document recursive directory globs and field projection"
status: "Completed"
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

Also close the pre-existing doc gap: README “Directory of Files” only shows generic `type: directory`, while the code exposes typed readers (`yaml_directory`, `json_directory`, `markdown_directory`, `bibtex_directory`, `meta_directory`, `docx_directory`, plain `directory`). Docs should name those types and state that discovery is non-recursive unless `recursive: true`.

## Acceptance Criteria

- [x] README and/or Sphinx “Directory of Files” section documents `recursive` and `fields`
- [x] README lists typed directory readers (not only bare `type: directory`)
- [x] Examples show nested glob + field projection (generic filenames, not referia-specific types)
- [x] Docs state default `recursive: false` and absent `fields` = current behaviour
- [x] Docs note that `**` is meaningful only with `recursive: true`
- [x] Docs note that `fields` applies to mapping-valued readers
- [x] Release note records opt-in, no break for existing configs

## Implementation Notes

- Formal docs may wait until CIP close/compression if Sphinx targets are unclear; at minimum update the user-facing Directory-of-Files material already in-tree
- Keep examples infrastructure-generic (no `_referia.yml` requirement in lynguine docs)
- Baseline survey (2026-10-11): no Sphinx narrative for directory globs; only automodule + README generic `directory` example

## Related

- CIP: 000F
- Depends on: feature tasks for recursive glob and field projection
- Related: `2026-10-11_baseline-directory-glob-behaviour` (pins behaviour docs should describe)

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-000F implementation plan steps 3–4.

Expanded scope: document typed directory readers and non-recursive default (gap found during glob survey).

README “Directory of Files” updated with typed readers, `recursive` / `fields`, nested example, and CIP-000F opt-in release note. Marked Completed.
