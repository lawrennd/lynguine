---
id: "2026-10-28_cip0018-document-inherit-bind-and-exclude"
title: "Document inherit bind for glob sources and directory exclude"
status: "Completed"
priority: "Medium"
created: "2026-10-28"
last_updated: "2026-10-28"
category: "documentation"
related_cips: ["0018"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-28_cip0018-bind-directory-sources"
- "2026-10-28_cip0018-directory-source-exclude"
tags:
- backlog
- documentation
- directory
- inherit
- cip0018
---

# Task: Document inherit bind for glob sources and directory exclude

> Linked CIP: 0018.

## Description

Document the two CIP-0018 behaviours next to existing Directory-of-Files options (`recursive`, `fields`, `include_start_directory`):

1. Inherited specs with `glob` bind relative `directory` to `inherit.directory`, same as filename specs.
2. Source `exclude` globs omit matched paths after discovery.

## Acceptance Criteria

- [ ] Directory-of-Files docs describe `exclude` with a generic example (not referia-specific names as the only example)
- [ ] Inherit / data-directory bind docs state that `glob` specs bind, not only `filename`
- [ ] Release note: both opt-in; defaults unchanged
- [ ] Sphinx page updated if that is where Directory-of-Files currently lives (`docs/getting_started/directory_sources.rst`)

## Implementation Notes

- Follow CIP-000F compression: README pointer + Sphinx page
- Do not document referia `inherit.reuse` here (that is referia CIP-001C)

## Related

- CIP: 0018
- CIP-000F documentation (`2026-10-11_document-recursive-directory-fields`)

## Progress Updates

### 2026-10-28

Task created (Ready) from CIP-0018.
