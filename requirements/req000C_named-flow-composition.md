---
id: "000C"
title: "Black-box processes compose through named published flows"
status: "Proposed"
priority: "High"
created: "2026-08-19"
last_updated: "2026-08-19"
related_tenets:
- explicit-infrastructure
- flow-based-processing
stakeholders:
- Application developers (lamd, referia, other lynguine clients)
- Operators composing multiple Linguine interfaces
tags:
- requirement
- doa
- flow
- publish
- subscribe
- interface
---

# REQ-000C: Black-box processes compose through named published flows

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A lynguine `Interface` already names incoming and outgoing flows so one black-box process can connect to another. Users can *publish* an output under a stable name and *subscribe* an input to that name. Matching happens through lynguine, not through a shared filename convention or an application-owned bus. After a process writes an output, subscribers can resolve that name to the current binding (a file, a live session, or a later remote source) and continue the access-assess-address flow.

This is the missing composition layer in the Linguine / DOA picture: components interact through data, not through tightly coupled APIs. Lamd's original request to generate an interface, register it, then execute is one consumer of this outcome, not the owner of it.

**Why this matters**: The explicit-infrastructure tenet requires connections between processes to be declared, not inferred. The flow-based-processing tenet requires those connections to be resolved during flow execution (`from_flow` / `to_flow`), not during object construction. Without named publish and subscribe, every composed workflow hard-codes paths and cannot be reviewed as a graph of flows.

**Who benefits**: Lamd, referia, and other clients that emit Linguine interface files; operators who want one process's output to become another's input without editing both files when a path changes.

## Acceptance Criteria

- [ ] An interface output can declare a publish name that other processes can subscribe to. The name is a stable identifier, not a filesystem path.
- [ ] An interface input can declare a subscribe name and resolve it during flow execution before the existing read path runs.
- [ ] Explicit registration binds subscribed inputs to currently published names. It does not publish outputs (bytes may not exist yet) and does not run on import or construction.
- [ ] After a process successfully writes a published output, that name becomes resolvable to the current binding.
- [ ] Failed resolution (unpublished name, stale binding, mismatched explicit path) fails the flow with an error that names the flow and the reason.
- [ ] Existing local-file interfaces with no publish or subscribe names behave as they do today.
- [ ] Application libraries (lamd, referia) consume this capability; they do not reimplement a registry.

## Notes

This requirement is the WHAT behind the "register with the publish and subscribe service" step in [lamd#5](https://github.com/lawrennd/lamd/issues/5). The service belongs in lynguine because `Interface` is already the connection to other black-box processes. CIP-0009's `source` block (remote file fetch) is a related access-stage hook; named flows are a different `source` kind, not a download.

## References

- **Related Tenets**: explicit-infrastructure, flow-based-processing
- **External Links**: [lamd#5](https://github.com/lawrennd/lamd/issues/5), [Linguine philosophy](https://github.com/lawrennd/linguine), Cabrera et al. (2023) DOA survey

## Progress Updates

### 2026-08-19

Requirement proposed after correcting the placement of lamd CIP-0011. HOW is lynguine CIP-000C.

Review before commit: registration binds subscribers only; names become resolvable after a successful write. Names are identifiers, not paths.
