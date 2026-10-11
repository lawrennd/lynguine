---
id: "2026-10-11_directory-reader-field-projection"
title: "Project explicit fields when reading directory sources"
status: "Ready"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_recursive-directory-glob"
tags:
- backlog
- features
- access
- directory
- fields
- projection
- cip000F
---

# Task: Project explicit fields when reading directory sources

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement CIP-000F field projection: when `fields` is set on a directory source (or details), keep only the listed top-level keys after each file is loaded as a mapping, then normalize. Absent `fields` keeps today's full `yaml.safe_load` + `json_normalize` behaviour.

This lets catalog flows request `title`, `description`, `date`, `current` (or any caller-chosen list) without exploding rich configs into noisy columns.

## Acceptance Criteria

- [ ] When `fields` is present, mapping-valued file results are reduced to `{k: data.get(k) for k in fields}` before normalize
- [ ] Missing listed keys appear as null/NaN consistently
- [ ] When `fields` is absent, full-document normalize behaviour is unchanged
- [ ] `fields` resolves from the active `source` entry, else `details`
- [ ] `store_fields` still append path metadata after projection; name collisions still error as today
- [ ] Non-mapping payloads: `fields` is a no-op or warning (documented); no crash
- [ ] Unit tests cover projection, missing keys, and `store_fields` population
- [ ] `meta_directory` left unchanged (out of scope)

## Implementation Notes

- Touch `read_files` / post-read path in `lynguine/access/io.py` after the per-file reader returns a dict
- Canonical form: presence of `fields` implies project mode (optional `load: project` only if cheap)
- Soft dependency on recursive glob task for end-to-end nested catalog fixtures; projection itself can land independently on flat directories

## Related

- CIP: 000F
- Depends on: 2026-10-11_recursive-directory-glob (for nested catalog E2E; not a hard code dependency)
- Downstream: referia CIP-0010 field list on `**/_referia.yml`

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-000F implementation plan step 2.
