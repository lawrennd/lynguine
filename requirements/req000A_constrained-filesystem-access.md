---
id: "000A"
title: "Constrained Filesystem Access"
status: "In Progress"
priority: "High"
created: "2026-08-19"
last_updated: "2026-08-19"
related_tenets:
- explicit-infrastructure
- flow-based-processing
stakeholders:
- Library users
- Application developers (referia, lamd)
- Maintainers
- Anyone exposing lynguine via server or untrusted config
tags:
- requirement
- security
- filesystem
- path-traversal
- access
---

# REQ-000A: Constrained Filesystem Access

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

Lynguine reads and writes files whose paths come from configuration, function arguments, and (in server mode) external callers. Those paths must not be able to escape an explicitly declared allowed root. Untrusted or remotely supplied names must not open, create, or overwrite files outside that root.

Today the access layer treats a path as an opaque string and opens it. That is acceptable when the caller is a local user pointing at their own files. It is not acceptable once an interface file, session API, or downloaded source can name a path. GitHub CodeQL currently reports 15 high-severity `py/path-injection` findings on this surface (`lynguine/access/io.py`, `lynguine/config/interface.py`, `lynguine/session_manager.py`).

**Why this matters**: Explicit infrastructure means the allowed location of data is part of the data flow, not an implicit side effect of `open()`. Flow-based processing means confinement happens when a path is used, not as hidden constructor magic.

**Who benefits**: Users running lynguine locally keep current behaviour when they declare (or inherit) a root. Applications that serve sessions or load untrusted YAML cannot be used as a path-traversal proxy. Maintainers can treat remaining CodeQL path alerts as recorded decisions rather than an undifferentiated pile.

## Acceptance Criteria

- [ ] Every file open, existence check, or write that consumes a configured or caller-supplied path is either confined to an explicit allowed root, or the unbounded case is an explicit, documented opt-out
- [ ] Server/session creation cannot load an interface file or data file outside the session's allowed roots
- [ ] Config-driven reads and writes (including future remote-source caches from REQ-0009) cannot traverse out of the declared root with `..`, symlink escape, or absolute paths unless that root allows them
- [ ] Errors name the rejected path and the allowed root; they do not fail silently
- [ ] Primitive I/O helpers that remain trusted-caller APIs have a recorded rationale if static analysis still flags them
- [ ] High-severity path-injection alerts are either resolved by confinement CodeQL can see, or dismissed with that recorded rationale

## Notes

This requirement does not demand that every low-level `open()` in the library become a security boundary. It demands that the **flow** (interface load, session create, access-stage read/write) has an explicit root, and that unbounded primitives are an honest, documented contract rather than the default for untrusted inputs.

Related but separate: credential storage paths (REQ-0004) and GitHub Actions token scope (REQ-000B).

## References

- **Related Tenets**: `explicit-infrastructure`, `flow-based-processing`
- **CodeQL**: [open path-injection alerts](https://github.com/lawrennd/lynguine/security/code-scanning)
- **Related CIPs**: CIP-0008 (server mode), CIP-0009 (config-driven remote access)

## Progress Updates

### 2026-08-19

Requirement proposed after reviewing 34 open CodeQL alerts (15 of them `py/path-injection`).

### 2026-08-19 (later)

Accepted. CIP-000A accepted as the implementation plan. Status moved to In Progress.
