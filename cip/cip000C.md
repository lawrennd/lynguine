---
author: "Neil D. Lawrence"
created: "2026-08-19"
id: "000C"
last_updated: "2026-08-19"
status: "Proposed"
compressed: false
related_requirements: ["000C", "0002"]
related_cips: ["0008", "0009", "000A"]
tags:
- cip
- doa
- flow
- publish
- subscribe
- interface
title: "Publish and subscribe named flows through the Interface"
---

# CIP-000C: Publish and subscribe named flows through the Interface

> **Note**: CIPs describe HOW to achieve requirements (WHAT).
> Use `related_requirements` to link to the requirements this CIP implements.

## Status

- [x] Proposed - Initial idea documented
- [ ] Accepted - Approved, ready to start work
- [ ] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented (add reason, use superseded_by if replaced)
- [ ] Deferred - Postponed (use blocked_by field to indicate blocker)

## Summary

Lynguine already treats an `Interface` as the connection between black-box processes: `input` / `output` / `compute` plus `from_flow` / `to_flow`. What is missing is a **named flow registry** so one process can *publish* an output and another can *subscribe* to it without sharing a filename by convention.

This CIP adds that registry as lynguine infrastructure. It is not a message broker. It is the matching layer on top of the existing access-assess-address path. Clients such as lamd generate an interface, **register it here**, then execute.

This CIP implements [REQ-000C](../requirements/req000C_named-flow-composition.md). It also keeps [REQ-0002](../requirements/req0002_predictable-architecture.md): resolution happens during flow processing, not construction.

**Which requirements does this CIP address?** REQ-000C, REQ-0002.

## Motivation

[lamd#5](https://github.com/lawrennd/lamd/issues/5) asked for three steps: generate an interface file, register it with a publish/subscribe service, execute from that file. Lamd CIP-0006 is the right HOW for generate and execute. Registration does not belong in lamd.

The lynguine README already states the intended architecture:

> `interface` defines the `Interface` object that's used for defining inputs and outputs which defines connections to other 'black box processes'.

Data-oriented architecture (Cabrera et al., 2023) decouples components by having them interact through data, typically via publish/subscribe of named streams. Linguine's `input` and `output` flows *are* those streams. Today they only bind to local files (and Google Sheets). Composition across processes therefore collapses to "both files happen to name the same path."

That is implicit coupling. The right move is to make publish and subscribe **named**, **explicit**, and **resolved at flow time** in lynguine, then let lamd (and referia) consume the API.

A first draft of this decision lived in lamd as CIP-0011 and argued there was no service, so files plus Make would do. That put the HOW in the wrong library and treated the absence of a registry as a reason not to build one. This CIP replaces that.

## Detailed Description

### What already exists (build on this)

| Piece | Role today | Role after this CIP |
|---|---|---|
| `Interface` YAML | Declares `input` / `output` / `compute` | Same, plus `publish` on outputs and `source.type: flow` on inputs |
| `CustomDataFrame.from_flow` | Access-stage read | Resolves subscribed names, then existing `read_data` |
| `CustomDataFrame.to_flow` | Address-stage write | Writes, then updates the registry for published names |
| CIP-0009 `source` block | Proposed: `url` / `github` fetch before read | Add `source.type: flow` as another materialiser |
| `SessionManager` | Live `CustomDataFrame` from an interface file | Optional binding target for a published name (not required for v1) |

Do not invent a second interface format. Do not replace `from_flow` / `to_flow`. The registry answers "where is this named flow bound right now?" The existing I/O answers "read or write those bytes."

### Publish and subscribe in the interface

Subscribe uses the CIP-0009 `source` hook so all "where does this item come from?" questions stay in one place:

```yaml
input:
  type: markdown
  source:
    type: flow
    name: talk.notes
```

Publish is declared on the output that `to_flow` writes:

```yaml
output:
  type: markdown
  filename: notes.md
  directory: _notes
  publish:
    name: talk.notes
```

`publish.name` is a stable identifier, not a path. Paths can change; names should not. Names must be dotted tokens (`talk.notes`); they must not contain path separators. The registry stores one file per name under its own directory, so a slash in a name would be a traversal, not a topic.

`publish` and `source` apply per data item. When `input` or `output` is a list (hstack), each element may publish or subscribe independently.

If `directory` / `filename` are omitted, they are filled from the publisher's last binding during `from_flow`. If they are present, they must match the binding or the flow fails (explicit, no silent overwrite).

### Registry

A `FlowRegistry` maps `name → binding`.

A binding in the first delivery is:

```yaml
name: talk.notes
kind: file
directory: /abs/path/_notes
filename: notes.md
publisher: /abs/path/talk.interface.yml
updated: 2026-08-19T08:00:00Z
```

Later kinds (not v1): `session` (CIP-0008 session id), `url` (CIP-0009 remote). The schema should allow `kind` so those can be added without renaming the store.

**Store.** Default: a directory of one YAML file per name, under a path taken from `Context` (for example `~/.lynguine/flows/`). Project-local override via context/config so a talk repo can keep its own registry next to the content. The store is inspectable files, not a hidden daemon. That keeps "show me the data flow."

Name-to-filename mapping must confine the file to that directory (CIP-000A). When `from_flow` copies `directory` / `filename` from a binding onto an item, those paths pass through the same path-resolution helper as other configured files.

**Overwrite.** `publish(name, binding)` replaces any previous binding for that name. Rebuilds and re-runs must not fail because the name already exists. The stored `publisher` path makes the last writer inspectable. A later revision may add fail-if-different-publisher; v1 does not.

**API** (names can vary; behaviour must not):

```python
from lynguine.flow.registry import FlowRegistry

reg = FlowRegistry.from_context(ctxt)
reg.publish(name, binding)           # write/replace binding
binding = reg.subscribe(name)        # raise if missing
reg.register_interface(interface, path=None)
```

`register_interface` is fail-fast, not the write:

1. For each output with `publish.name`, do **not** publish yet (the bytes may not exist). Validate the name. Do not write a binding.
2. For each input with `source.type: flow`, resolve `source.name` now and materialise `directory` / `filename` on the in-memory interface so a missing name fails before compute starts.

Publication happens in `to_flow`, after a successful write.

`from_flow` still resolves `source.type: flow` at read time. If `register_interface` already filled `directory` / `filename`, `from_flow` checks they still match the current binding. If they were left unset, it fills them. A binding published by another process between register and read is therefore visible, and a stale fill is not silently kept.

Registration is an explicit call from the client (`lamd talk --execute`, a referia flow, a test). Loading an `Interface` from disk does not register it. That would be construction-time magic.

### Flow algorithm

In `from_flow`, for each valid data item, before `data_exists` / `read_data` (same insertion point CIP-0009 uses for `url` / `github`):

1. If `source` is absent, current behaviour.
2. If `source.type` is `flow`, call `registry.subscribe(source.name)`.
3. Copy `directory` / `filename` from the binding onto the item if they were omitted; if they were set and differ, raise `ValueError` naming the flow and both paths.
4. Continue to `read_data`.

In `to_flow`, after a successful `write_data` for an output that has `publish.name`:

1. `registry.publish(name, file binding from the item + publisher path)`.

Failed subscribe fails the flow. Do not create an empty input frame for a missing published name.

### What this is not

- **Not Redis, MQTT, Kafka, or an in-process callback list.** Those are control-plane buses. DOA composition is named data.
- **Not "the YAML file on disk is the only publication."** A file is one *binding*. The *name* is what subscribers declare. Make and git remain useful; they are not the matching layer.
- **Not automatic fan-out of events.** A subscriber runs its own `from_flow` when it executes. The registry does not invoke listeners.
- **Not a lamd feature.** Lamd CIP-0006 generate writes `publish` / `source.type: flow` into the interface; execute calls `register_interface` then `from_flow` / compute / `to_flow`.

### Relationship to other CIPs

- **CIP-0009 (Proposed)**: `source.type: url | github | flow`. Same hook, different materialiser. The type registry is shared. Neither blocks the other. If CIP-0009 lands first, this CIP adds a type to the existing dispatch; if this lands first, CIP-0009 adds types beside `flow`.
- **CIP-000A (Accepted)**: configured paths, including bindings copied into an item and registry filenames derived from publish names, stay inside an explicit root. A publish name is not a path.
- **CIP-0008 (server / sessions)**: a published flow may later bind `kind: session`. V1 is files only so clients work without a server. Sessions are an optimisation for repeated access (REQ-0007), not the composition contract.
- **CIP-0007 (package split)**: registry stays in lynguine (infrastructure). vongole does not own flow names.

### Alternatives considered

1. **Leave matching to shared filenames and Make.** Rejected: that is implicit coupling and leaves lamd#5's "register" step as theatre.
2. **Build the registry in lamd.** Rejected: `Interface` and `from_flow` already live here; lamd would reimplement infrastructure.
3. **A message broker.** Rejected: we need named data bindings, not queued events. A broker would hide the flow.

## Implementation Plan

1. **Schema**
   - Document `publish.name` on output types and `source.type: flow` with `source.name` on input types.
   - Reject unknown `source.type` (shared with CIP-0009) and missing `name` with a clear error.

2. **Registry**
   - Add `lynguine.flow.registry.FlowRegistry` with file-backed store, `from_context`, `publish`, `subscribe`, `register_interface`.
   - Context key for the store directory; default under the user lynguine dir.

3. **Wire flows**
   - `from_flow`: resolve `source.type: flow` before read.
   - `to_flow`: update registry after successful write of a published output.

4. **Client contract** (documented, not implemented in this CIP)
   - Lamd CIP-0006 `--execute` calls `register_interface` then existing execute.
   - Generate should emit `publish` / `subscribe` names for the talk/cv outputs and inputs it already knows.

5. **Tests** (see Testing Strategy)

## Backward Compatibility

Interfaces without `publish` or `source.type: flow` are unchanged. No existing `from_flow` caller must register. New behaviour is opt-in via those keys plus an explicit `register_interface` (or the `from_flow` resolution of `source.type: flow`, which requires a binding that some earlier `to_flow` published).

## Testing Strategy

- Unit: publish then subscribe returns the same binding; subscribe of an unknown name raises with the name in the message; `register_interface` binds inputs from previously published outputs; a name containing `/` or `..` is rejected.
- Flow: interface A publishes `talk.notes` via `to_flow`; interface B with `source.type: flow` reads that file via `from_flow`.
- Negative: `from_flow` does not register; constructing `Interface` does not write the store; mismatched explicit path vs binding fails; `register_interface` does not publish outputs.
- Isolation: tests use a temporary registry directory, never the user default.

## Related Requirements

- [REQ-000C](../requirements/req000C_named-flow-composition.md): named publish and subscribe between processes.
- [REQ-0002](../requirements/req0002_predictable-architecture.md): resolution during flow execution, infrastructure stays explicit.

Specifically, it implements:

- Publish names on outputs and subscribe names on inputs.
- Explicit registration, not construction-time magic.
- Client libraries consume the registry rather than owning one.

## Implementation Status

- [ ] Schema for `publish` and `source.type: flow`
- [ ] `FlowRegistry` with inspectable file store
- [ ] `from_flow` / `to_flow` wiring
- [ ] Tests with an isolated registry directory
- [ ] Document the client contract for lamd CIP-0006

## References

- [lamd#5](https://github.com/lawrennd/lamd/issues/5) — original "register with the publish and subscribe service"
- [lamd CIP-0006](https://github.com/lawrennd/lamd/blob/main/cip/cip0006.md) — generate + execute; consumes this CIP
- [CIP-0008](cip0008.md) — sessions as a later binding kind
- [CIP-0009](cip0009.md) — `source` hook this CIP extends
- [Linguine philosophy](https://github.com/lawrennd/linguine/blob/main/docs/philosophy.md)
- Cabrera, Paleyes, Thodoroff, and Lawrence (2023), [Real-world Machine Learning Systems: A Survey from a Data-Oriented Architecture Perspective](https://arxiv.org/abs/2302.04810)
- Tenets: explicit-infrastructure, flow-based-processing
