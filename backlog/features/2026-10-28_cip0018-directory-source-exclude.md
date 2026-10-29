---
id: "2026-10-28_cip0018-directory-source-exclude"
title: "Directory sources can exclude matched paths by glob"
status: "Completed"
priority: "High"
created: "2026-10-28"
last_updated: "2026-10-28"
category: "features"
related_cips: ["0018"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- directory
- exclude
- yaml_directory
- cip0018
---

# Task: Directory sources can exclude matched paths by glob

> Linked CIP: 0018. Complements `include_start_directory: false` (CIP-000F), which only omits the start directory's own matches.

## Description

After glob expansion, `regexp`, and `include_start_directory`, drop matches whose path relative to the source `directory` matches any pattern in an opt-in `exclude` list.

Catalogs that auto-discover `**/_referia.yml` can then omit nested view configs (`today/**`, `year/**`) without enumerating every work folder and without lynguine knowing those names.

## Acceptance Criteria

- [ ] Source (and/or details) accepts `exclude` (list of glob strings); default absent / empty keeps today's match set
- [ ] Source `exclude` wins over top-level `details["exclude"]`
- [ ] Patterns match the path relative to the resolved source directory (`**` allowed; POSIX separators)
- [ ] `exclude: [today/**]` drops `today/x.yml` and `today/a/b.yml`; keeps `applications/x.yml`
- [ ] Works together with `include_start_directory: false` (start-dir file still omitted by that flag, not by exclude)
- [ ] Debug log records exclude patterns and drop count
- [ ] Kept paths still pass CIP-000A confinement; excluded paths are not read
- [ ] No default excludes; no special-case of `_referia.yml` or directory names
- [ ] Shared `read_directory` path so all `*_directory` readers benefit

## Implementation Notes

- Touch: `lynguine/access/io.py` — `read_directory`, after the `include_start_directory` filter
- Use `fnmatch` / `Path.match` against a relative path, not absolute host paths
- YAML alternative (enumerate work directories as separate sources) remains valid; this task is the auto-discovery omit

## Related

- CIP: 0018
- CIP-000F (`recursive`, `fields`, `include_start_directory`)
- referia CIP-001C (parent catalog will list `today/**` and `year/**`)

## Progress Updates

### 2026-10-28

Task created (Ready) from CIP-0018.
