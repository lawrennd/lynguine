---
author: "Neil D. Lawrence"
created: "2026-08-19"
id: "000D"
last_updated: "2026-08-19"
status: "In Progress"
compressed: false
related_requirements: ["000A"]
related_cips: ["000A", "0008", "000B"]
tags:
- cip
- security
- codeql
- path-injection
- static-analysis
title: "Make CodeQL path-injection analysis match the CIP-000A confinement model"
---

# CIP-000D: Make CodeQL path-injection analysis match the CIP-000A confinement model

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

[CIP-000A](cip000A.md) added an explicit path jail at flow boundaries (`resolve_under_roots`, `Interface.from_file` / `from_cwd_file`, `SessionManager`, access-stage configured paths). That is the security design. GitHub CodeQL `py/path-injection` still reports high-severity alerts because the query does not treat that jail as a sanitizer.

This CIP is the follow-on that static analysis showed was still needed, in the same sense that [CIP-000B](cip000B.md) followed CIP-0005: do not reopen the confinement CIP; document what the analyzer actually accepts, then either dismiss with a recorded rationale or change structure so the query can see a barrier. REQ-000A's last acceptance criterion is exactly this: alerts are resolved by confinement CodeQL can see, or dismissed with that rationale.

**Which requirements does this CIP address?** REQ-000A (the recorded-rationale / CodeQL-visible remainder).

## Motivation

PR #22 merged the CIP-000A jail, then spent three follow-up commits trying to satisfy CodeQL by inlining `normpath`/`realpath`/`startswith` and moving HTTP loaders off `from_file`. Each change closed some alerts and opened others on the next sink (40 → 41 → 42–45 → 46–49). That is analyzer churn, not a missing jail.

Open `py/path-injection` alerts on `main` after the merge (2026-08-19):

| Cluster | Alerts | Location | What it actually is |
|---------|--------|----------|---------------------|
| A. Trusted-caller primitives | 23–33 | `access/io.py` `exists`/`open` in `read_json_file`, `write_json_file`, … | Public I/O helpers. CIP-000A left these as trusted-caller APIs on purpose. |
| B. Shared `from_file` | 21, 22, 42, 43 | `config/interface.py` unbounded `exists`, confined `exists`, confined `open` | Library loader. HTTP no longer calls it, but `__init__` inherit still does, and CodeQL treats the function as tainted if any path from `do_POST` can reach it. |
| C. Shared YAML helper | 46, 47 | `config/interface.py` `_read_yaml_or_empty` | Same taint funnel: a helper `exists`/`open` whose `fname` argument is a parameter. |
| D. Explicit unbounded opt-out | 48, 49 | `session_manager.py` `exists`/`open` on the `if unbounded:` branch | Operator opt-out. Default SessionManager is *not* unbounded. CodeQL still flags the branch because it shares a function with HTTP `create_session`. |

CIP-000A already predicted cluster A. Clusters B–D are what we learned from trying to make the query happy inside the confinement CIP: **GitHub's sanitizer is narrower than a correct jail.**

## Detailed Description

### What CodeQL actually accepts

The published good example for [py/path-injection](https://codeql.github.com/codeql-query-help/python/py-path-injection/) is all in one function:

```python
base_path = '/server/static/images'   # or os.getcwd() bound locally
fullpath = os.path.normpath(os.path.join(base_path, filename))
if not fullpath.startswith(base_path):
    raise Exception("not allowed")
data = open(fullpath, 'rb').read()
```

The query's barrier is not "a correct prefix check somewhere". From CodeQL's Python libraries, a path-injection sanitizer is:

- a `Path::PathNormalization` plus a `Path::SafeAccessCheck` (typically `startswith` against the **same** prefix used in `join`), or
- a models-as-data `path-injection` barrier, or
- a constant comparison.

What does **not** count, even when it is a correct jail:

- `resolve_under_roots(path, roots)` — a user helper is not a `PathNormalization` / `SafeAccessCheck` concept.
- `startswith(root)` when `root` is a **parameter** (`allowed_roots`, request `directory`). A client sending `directory=/` would make that prefix check succeed; CodeQL is right to refuse it as a sanitizer.
- Splitting unbounded vs confined in the same function, then `open` in a helper — taint follows the parameter into the helper (`_read_yaml_or_empty`).
- Context: if `LynguineHandler.do_POST` can reach function `F`, **every** `exists`/`open` in `F` is a sink, including opt-out branches that HTTP never takes at runtime.

`from_cwd_file` matches the published example (`base_path = os.path.realpath(os.getcwd())` local to the function). Remaining `from_file` alerts mean either inherit still connects HTTP → `from_file`, or default CodeQL is context-insensitive enough that a public loader with `directory`/`user_file` parameters stays a sink.

### What we will not do in this CIP

- Reopen CIP-000A's threat model (confine at flow boundaries; primitives stay trusted-caller).
- Keep moving `exists`/`open` between helpers hoping the next line number goes quiet. That multiplies alerts.
- Wrap every `open()` in `io.py` with a hidden global root.

### Design choice: classify, then either dismiss or isolate

Three honest outcomes, one per cluster:

**Cluster A — dismiss as used in production, and document the contract.** Record on each alert: trusted-caller I/O primitive; confinement is at `extract_full_filename` / flow entry; see CIP-000A. Do this first. It is the bulk of the remaining list and does not require wrapping `open()`. The primitives stay sharp; the contract is documented on the helpers themselves so a later HTTP caller cannot treat a quiet CodeQL tab as permission to pass request paths into `read_yaml_file`.

**Cluster D — isolate or dismiss the opt-out.** The unbounded `exists`/`open` in `create_session` is a real query hit because it is in an HTTP-reachable function. Options:

1. Move unbounded load to a function HTTP handlers never call (e.g. only construction-time / CLI). Default server `create_session` has no unbounded branch.
2. Dismiss: explicit `unbounded_paths=True` / `allowed_roots=None`, not the server default.

Prefer (1) if a small split is enough; otherwise (2) with the same recorded rationale as cluster A.

**Cluster B/C — make the HTTP-reachable open look like the published example, or tell CodeQL the helper is a barrier.** Options, in order of preference:

1. **Inherit must not call `from_file` from an HTTP-constructed Interface.** Load the parent YAML through the same cwd-sandbox as the child (`from_cwd_file` / a private `_open_under_local_cwd`), so `from_file` is only a local/CLI entry point. Then dismiss leftover `from_file` alerts as trusted-caller library API (same as `read_yaml_file`).
2. **Models-as-data barrier** in-repo (`.github/codeql` or `codeql-pack`) marking `resolve_under_roots` and/or `from_cwd_file` as `path-injection` sanitizers. This teaches default analysis what CIP-000A already implements. It does not change runtime behaviour. Confirm GitHub code scanning for this repo actually loads extra models (query suite / `codeql-config.yml`); if it does not, this option is theatre.
3. **Inline the published example in every HTTP handler** and never `open` in a shared library function those handlers call. That fights the explicit-infrastructure tenet (duplicated jail) and is the pattern CIP-000A already rejected as primary design.

This CIP's implementation work is (cluster A dismissals) plus whichever of B/C/D we accept. The research outcome we already have: **custom helpers and parameterized roots are invisible to `py/path-injection`; only a local untainted prefix next to `open`, or a models-as-data barrier, is visible.**

## Implementation Plan

1. **Inventory on `main`**
   - Table of open `py/path-injection` alerts with cluster A/B/C/D
   - Confirm taint source is still `do_POST` (or a broader remote source) for B/C/D

2. **Dismiss cluster A**
   - GitHub code-scanning dismissals linking CIP-000A + this CIP
   - Same text on each: trusted-caller primitive; flow boundary already confines configured names

3. **Choose B/C/D treatment** (accept this CIP with one of: inherit isolation, models-as-data, or recorded dismissals)
   - If inherit isolation: parent YAML load uses cwd-sandbox; `from_file` not on the HTTP call graph
   - If models-as-data: add config GitHub code scanning will load; verify on a PR
   - If dismiss B/C/D: rationale per cluster, no further sink-shuffling

4. **Re-scan**
   - Open `py/path-injection` is either empty or every remaining alert has a recorded dismissal
   - Close CIP-000A's leftover "CodeQL re-check" item once this is done

## Backward Compatibility

- Dismissals: none.
- Inherit isolation: HTTP-loaded interfaces with `inherit.directory` outside cwd already fail under CIP-000A roots; no new user-visible break.
- Models-as-data: none (analysis only).
- Splitting unbounded out of `create_session`: server default unchanged; operators using `unbounded_paths=True` on the HTTP manager would need the new entry point.

## Testing Strategy

- No change to CIP-000A path-escape tests for dismiss-only work.
- If inherit isolation lands: a test that HTTP/`from_cwd_file` inherit cannot `open` `/etc/passwd`, and that `from_file` is not imported by server handlers (grep/arch test).
- If models-as-data lands: a PR whose CodeQL job shows cluster B/C gone without moving `open`.

## Related Requirements

- [REQ-000A](../requirements/req000A_constrained-filesystem-access.md) — constrained filesystem access (alerts resolved or dismissed with rationale)

## Implementation Status

- [x] Inventory remaining `py/path-injection` alerts into clusters A–D
- [x] Document cluster A primitives as trusted-caller I/O
- [ ] Dismiss GitHub CodeQL alerts 23–33 with the documented rationale
- [x] Accepted treatment for B/C: inherit isolation (`from_cwd_file`, not `from_file`)
- [x] Accepted treatment for D: split unbounded off HTTP `create_session`
- [ ] Re-scan; leftover alerts all have recorded rationale

## References

- [CIP-000A](cip000A.md) path confinement (merged, PR #22)
- [CIP-000B](cip000B.md) same pattern: CodeQL did not treat the first sanitizer as one
- GitHub CodeQL: [Uncontrolled data used in path expression](https://codeql.github.com/codeql-query-help/python/py-path-injection/)
- CodeQL Python `PathInjectionCustomizations.qll` (sanitizer = SafeAccessCheck / PathNormalization / models-as-data, not a user helper)

## Progress Updates

### 2026-08-19

Proposed after PR #22 merged. CIP-000A's jail is in; `py/path-injection` remains on primitives, `from_file`, `_read_yaml_or_empty`, and the unbounded session branch. Further inlining of `startswith` inside shared loaders is the wrong CIP.

### 2026-08-19 (later)

Accepted. Cluster A dismissals first. Treatment for B/C (inherit isolation vs models-as-data vs dismiss) and D (split unbounded vs dismiss) still to be chosen before implementation.

### 2026-08-19 (cluster A)

In Progress. Cluster A accepted as: keep primitives sharp; document the trusted-caller contract on `lynguine.access.io` and `extract_full_filename`. GitHub dismissals of alerts 23–33 use that same rationale when applied.

### 2026-08-19 (B/C/D)

Inherit from a cwd-sandboxed Interface uses `from_cwd_file`, not `from_file`. HTTP `create_session` refuses unbounded managers; operator/CLI uses `create_session_unbounded`.
