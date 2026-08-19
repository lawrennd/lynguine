---
author: "Neil D. Lawrence"
created: "2026-08-19"
id: "000A"
last_updated: "2026-08-19"
status: "In Progress"
compressed: false
related_requirements: ["000A", "0002", "0009"]
related_cips: ["0008", "0009"]
tags:
- cip
- security
- filesystem
- path-traversal
- access
title: "Explicit path confinement in the access flow"
---

# CIP-000A: Explicit path confinement in the access flow

> **Note**: CIPs describe HOW to achieve requirements (WHAT).
> Use `related_requirements` to link to the requirements this CIP implements.

## Status

- [x] Proposed - Initial idea documented
- [x] Accepted - Approved, ready to start work
- [x] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented (add reason, use superseded_by if replaced)
- [ ] Deferred - Postponed (use blocked_by field to indicate blocker)

## Summary

Introduce an explicit path-resolution helper and apply it at the flow boundaries that currently feed `open()`, `os.path.exists()`, and writers: `Interface.from_file`, `SessionManager.create_session`, and access-stage read/write that take configured filenames. Primitive I/O helpers that remain trusted-caller APIs keep their current signatures, with recorded CodeQL dismissals rather than a breaking wrap of every `open()`.

This CIP implements [REQ-000A](../requirements/req000A_constrained-filesystem-access.md). It is a prerequisite for safely accepting [CIP-0008](cip0008.md) server sessions and [CIP-0009](cip0009.md) config-driven downloads.

**Which requirements does this CIP address?** REQ-000A (primary), REQ-0002 (predictable, explicit flow), REQ-0009 (remote source cache paths stay inside a root).

## Motivation

GitHub CodeQL reports 15 high-severity `py/path-injection` alerts (CWE-022/023/036/073). They are not 15 independent bugs. They are one missing invariant: **configured paths are not checked against an allowed root**.

| Alert | Location | Role |
|-------|----------|------|
| 20–22 | `config/interface.py` 834, 839, 840 | `from_file` joins `directory` + `user_file` and opens YAML |
| 23 | `access/io.py` 566 | `read_files` existence check on each `filename` |
| 24–33 | `access/io.py` 667–1406 | json/yaml/bibtex/markdown/csv readers and writers |
| 34 | `session_manager.py` 288 | `os.path.join(directory, interface_file)` then `exists` |

Two different threat models are being conflated:

1. **Trusted local caller.** `read_yaml_file("/Users/me/data.yml")` is the API. The user chose the file. Treating this as path injection is CodeQL applying a web-app query to a data library.
2. **Untrusted or config-supplied names.** An interface YAML, a session `interface_file` argument, or a downloaded cache path can name `../../.ssh/id_rsa`. That is a real traversal once lynguine is a server or loads third-party config.

CIP-0005 secured credentials. It did not confine the access stage. Without this CIP, CIP-0008 and CIP-0009 enlarge the same hole.

## Detailed Description

### Design choice: confine at flow boundaries, not every primitive

Wrapping every `open()` in `lynguine/access/io.py` would either break the public I/O helpers or invent a hidden global root (forbidden by the explicit-infrastructure tenet). The data flow already has a natural place for the check:

```
session / from_flow
    → Interface.from_file(user_file, directory=...)
    → access io (read_data / write_data / read_files)
        → primitive readers (read_yaml_file, ...)
```

Confinement belongs on the first two arrows. Primitive readers remain "open this path" tools for trusted callers.

### Helper (explicit, no magic)

Add a small module, for example `lynguine/access/paths.py`, with a single obvious function:

```python
def resolve_under_roots(path: str, roots: list[str]) -> str:
    """Expand, resolve, and require the path to sit under one of roots.

    Raises PathEscapeError with the requested path and the allowed roots.
    """
```

Behaviour:

- `os.path.expandvars` / `expanduser`, then `os.path.realpath`
- Compare `realpath(path)` to `realpath(root) + os.sep` (or equality) for each root
- Reject empty path, NUL bytes, and empty roots
- Do not consult a process-global default; the caller passes `roots`

`Interface` and `SessionManager` store `allowed_roots` on the object so later access-stage reads use the same list. Default when the caller omits it:

- `Interface.from_file`: `[expanded_directory]` (the directory already used to join the config file)
- `SessionManager.create_session`: roots captured at manager construction (process cwd unless the operator passes `allowed_roots`). The request `directory` is resolved under those roots; it is not itself a root (a client sending `directory=/` must not enlarge the jail).

That default matches how paths are already joined today, so local referia/lamd use stays working, while `interface_file="../etc/passwd"` relative to a session directory is rejected.

### Where to call it

1. **`Interface.from_file`**: resolve `directory`; resolve each candidate `user_file` under that directory (or the provided roots). Open the resolved path only.
2. **`SessionManager.create_session`**: resolve `interface_file` under the session directory **before** `exists` / `from_file`. Do not take the interface file's own contents as a source of extra roots (that would let a malicious YAML enlarge the jail).
3. **Access-stage configured files**: `read_data` / `write_data` / `read_files` / `extract_full_filename` paths that come from interface details are resolved under the interface's `allowed_roots`. This is the check that actually covers most of the `io.py` alert *sources* even if primitive `open()` sites remain.

### What we will not do in this CIP

- Change primitive signatures (`read_yaml_file(filename)` stays).
- Introduce a global `LYNGUINE_ROOT` environment default (implicit).
- Claim CodeQL will go to zero: primitive `open()` sites may still taint. Those alerts are dismissed as "trusted-caller I/O primitive" with a link to this CIP, after the flow-boundary checks land.

### Opt-out (explicit)

A caller that truly needs unbounded paths passes `allowed_roots=None` or `unbounded_paths=True` at the flow entry point. That is a documented, greppable choice. It is not the session-manager default.

### CodeQL

GitHub's `py/path-injection` query treats a realpath-plus-prefix check as a sanitizer when the prefix is not itself tainted. Using `allowed_roots` from `SessionManager` construction (cwd / operator config) rather than from the request `directory` or the interface file keeps the prefix untainted. That should clear alerts 20–22, 34, and 40. Alerts 23–33 may remain on primitives; dismiss after the flow checks exist.

### Alternatives considered

| Approach | Why not (as the primary fix) |
|----------|------------------------------|
| Dismiss all 15 alerts now | Honest for primitives, dishonest for `session_manager` and config-joined paths |
| Force a root on every `open()` | Breaks tests and scripts that pass absolute tmp paths; hidden global root |
| `os.path.normpath` only | Does not stop absolute paths or symlink escape |
| Depend on OS user permissions | Not an application invariant; fails in shared or container deployments |

## Implementation Plan

1. **Helper and error type**
   - `PathEscapeError` with requested path and roots
   - `resolve_under_roots` with tests: `..`, absolute escape, symlink escape, equal-to-root, `expandvars`

2. **Wire `Interface.from_file`**
   - Store `allowed_roots` on the instance
   - Resolve config filename before `open`

3. **Wire `SessionManager.create_session`**
   - Resolve `interface_file` under session directory
   - Pass roots into `Interface.from_file`

4. **Wire access-stage configured paths**
   - Resolve filenames from interface details before primitive readers/writers
   - Keep primitives unchanged

5. **CodeQL follow-up**
   - Confirm alerts 20–22 and 34 close
   - Dismiss remaining primitive I/O alerts with CIP-000A rationale

6. **Docs**
   - Document `allowed_roots` and the unbounded opt-out in the access/flow docs after this CIP is closed (compression), not a parallel design doc

## Backward Compatibility

- Default roots = the directory already used to join files: existing local configs that keep data under that directory keep working.
- Absolute paths outside that directory (e.g. `/tmp/foo.yml` from an interface whose directory is the project) will start failing unless the caller adds that root or opts out. That is the intended security change; call it out in release notes.
- Primitive I/O APIs unchanged.

## Testing Strategy

- Unit tests for `resolve_under_roots` (including symlink escape where the OS allows it)
- `Interface.from_file` rejects `../` config names
- `SessionManager.create_session` rejects interface files outside the session directory
- Access-stage read/write of `../../../etc/passwd`-style details fails with `PathEscapeError`
- Existing I/O and mapping tests still pass with default roots
- After merge, re-check GitHub code-scanning for alerts 20–22 and 34

## Related Requirements

- [REQ-000A](../requirements/req000A_constrained-filesystem-access.md) — constrained filesystem access
- [REQ-0002](../requirements/req0002_predictable-architecture.md) — explicit, predictable flow
- [REQ-0009](../requirements/req0009_config-driven-remote-access.md) — downloaded caches must land inside the same root

## Implementation Status

- [x] Path helper and tests
- [x] Interface.from_file confinement
- [x] SessionManager confinement
- [x] Access-stage configured path confinement
- [ ] CodeQL re-check and recorded dismissals for primitives
- [ ] Release-note note on absolute paths outside the interface directory

## References

- CodeQL alerts 20–34, rule `py/path-injection`
- [CIP-0008](cip0008.md) server mode (session_manager is the high-value sink)
- [CIP-0009](cip0009.md) config-driven remote access
- GitHub CodeQL: [Uncontrolled data used in path expression](https://codeql.github.com/codeql-query-help/python/py-path-injection/)

## Progress Updates

### 2026-08-19

Proposed from CodeQL `py/path-injection` alerts 20–34.

### 2026-08-19 (later)

Accepted. Default roots = interface/session directory; unbounded paths are an explicit opt-out. Primitive I/O helpers stay trusted-caller APIs.

### 2026-08-19 (implementation)

In Progress. Helper `lynguine.access.paths.resolve_under_roots`, wired at `Interface.from_file`, `SessionManager.create_session`, and access-stage `extract_full_filename` / directory list paths. `from_flow` overwrites YAML `allowed_roots` so a config file cannot enlarge the jail. SessionManager and server `from_file` calls use construction-time roots (`os.getcwd()` unless the operator passes `allowed_roots`); the request `directory` is confined under those roots rather than becoming the jail.
