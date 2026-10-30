---
id: "2026-10-30_cip0019-io-plugin-docs"
title: "Document writing a tabular IO plugin (CIP-0019)"
status: "Completed"
priority: "Medium"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "documentation"
related_cips: ["0019"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-30_cip0019-io-type-registry"
tags:
- backlog
- documentation
- access
- io
- plugins
- cip0019
---

# Task: Document writing a tabular IO plugin (CIP-0019)

## Description

Short user-facing page: register contract, `plugins:`, read-only write,
credentials, and how this differs from CIP-0013 strategies and CIP-0009
`source:`. CHANGELOG Unreleased entry.

## Acceptance Criteria

- [x] `docs/getting_started/io_plugins.rst` is in the getting-started toctree
- [x] CHANGELOG Unreleased mentions CIP-0019
- [x] Page does not document Trello/Gmail APIs (those are follow-on packages)

## Related

- CIP: 0019
- Backlog: 2026-10-30_cip0019-io-type-registry

## Progress Updates

### 2026-10-30

Task created with CIP-0019 implementation.

Docs page, toctree, automodule, and CHANGELOG landed.
