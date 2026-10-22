---
id: "2026-10-22_liquid-root-identifiers"
title: "Extract Liquid root identifiers from the parse tree"
status: "Ready"
priority: "High"
created: "2026-10-22"
last_updated: "2026-10-22"
category: "features"
related_cips: ["0016"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- cip0016
- liquid
---

# Task: Extract Liquid root identifiers from the parse tree

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Add `liquid_root_identifiers(source: str) -> set[str]` that parses a
Liquid template with the existing environment and collects root variable
names. Dot paths contribute only the first segment. Do not regex-replace
Liquid. If python-liquid has no stable visitor, walk the parsed template
in lynguine.

## Acceptance Criteria

- [ ] `{{ store_status.output.path }}` → `{"store_status"}`
- [ ] `{% if selected_doc %}...{% endif %}` → `{"selected_doc"}`
- [ ] `{{ embeddings[0] }}` → `{"embeddings"}`
- [ ] Static HTML with no `{{` / `{%` → empty set

## Implementation Notes

See [CIP-0016](../../cip/cip0016.md) identifier extraction. Use
`self.compute._liquid_env` (or the same Environment class) to parse.

## Related

- CIP: 0016

## Progress Updates

### 2026-10-22

CIP-0016 accepted. Task created.
