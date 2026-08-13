---
id: "0008"
title: "Complete Diagram Dependency Extraction"
status: "In Progress"
priority: "High"
created: "2026-08-09"
last_updated: "2026-08-09"
related_tenets:
- explicit-infrastructure
stakeholders:
- lamd developers
- talk and slide build tool maintainers
tags:
- requirement
- dependencies
- diagrams
- talk
- build
---

# REQ-0008: Complete Diagram Dependency Extraction

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

When applications use lynguine to discover build dependencies for talks and slide decks, the reported diagram dependencies must match the diagrams that will actually appear after document preprocessing. Today, diagram paths built with gpp-style macros (for example `\define` and `\concat` inside `\includediagram{...}`) are expanded correctly at build time but omitted from lynguine's dependency output. Downstream build systems therefore miss derived assets (such as `.emf` files needed for PowerPoint output) even when the source diagrams exist.

**Problem**: Silent omission of resolvable diagram paths creates hidden build dependencies. Make and similar tools cannot schedule conversion steps for assets lynguine never reports, leading to late failures at pandoc or packaging stages rather than at dependency planning time.

**Desired outcome**: Dependency extraction for talks returns a complete, actionable list of diagram files for both literal paths and commonly used macro-built paths, with documented boundaries so consumers know what forms are supported.

**Why this matters**: The explicit-infrastructure tenet requires traceable data flows and rejects hidden dependencies. Dropping macro-built paths while retaining literal paths is inconsistent and unpredictable for consumers such as lamd.

**Who benefits**: lamd maintainers and anyone using lynguine's talk dependency utilities to drive incremental builds.

## Acceptance Criteria

- [ ] Diagram dependencies reported by lynguine include paths that use `\define{...}{...}` and `\concat{...}{...}` in `\includediagram{...}` when those macros are defined in the same snippet file or included snippet tree being scanned.
- [ ] After standard path substitutions (such as `\diagramsDir`), reported dependencies resolve to concrete filesystem paths with no remaining unresolved macro tokens.
- [ ] Literal `\includediagram` paths continue to be reported exactly as today (no regression).
- [ ] Consumers can rely on `dependencies batch` / diagram dependency output to list derived formats (for example `.emf`) needed for talks that use macro-built diagram names.
- [ ] Supported macro forms and known limitations are documented so consumers know what dependency extraction guarantees without assuming full gpp emulation.

## User Stories

**As a lamd maintainer**, I want diagram dependency scanning to list all diagrams a talk will use so that make builds every required asset before pandoc runs.

**As a talk author**, I want to use `\define` and `\concat` to name diagram sequences so that dependency extraction still finds those diagrams without maintaining duplicate literal paths.

**As a library user**, I want dependency extraction behavior to be explicit and documented so that I know which macro patterns are supported and which require literal paths.

## Constraints

- Must not require full gpp preprocessing inside lynguine's dependency scanner.
- Must not break existing applications (referia, lamd) or change behavior for talks that use only literal diagram paths.
- Workarounds in consumer makefiles must not be required for supported macro patterns.
- Scope remains bounded: document what is supported rather than silently attempting open-ended macro expansion.

## Notes

**Observed failure** (lamd / mlfc): `basis-functions-and-generalisation.pptx` failed because `./slides/diagrams/ml/quadratic_basis000.emf` was not in the resource path. The corresponding `.svg` existed; the EMF was never a make target because macro-built paths were dropped during dependency extraction.

**Example source pattern**: snippets that define `\basisfunction` locally and reference `\includediagram{\diagramsDir/ml/\concat{\basisfunction}{000}}` alongside literal diagram paths in the same file.

**Out of scope for this requirement**:
- Full gpp emulation for arbitrary macros
- Consumer-side makefile or dependency CLI workarounds
- Path normalisation issues unrelated to macro resolution (for example double slashes after substitution)

## References

- **Related tenets**: `explicit-infrastructure`
- **Backlog task**: `backlog/features/2026-08-09_macro-aware-diagram-dependency-extraction.md`
- **Consumer context**: lamd `dependencies` / `dependencies batch` → build flags for talk output formats

## Progress Updates

### 2026-08-09

Requirement drafted from lamd pptx build diagnosis: SVG present, EMF missing from make because macro-built `\includediagram` paths were silently skipped.

### 2026-08-09

Implementation in progress: bounded `\define` / `\concat` expansion in `lynguine/util/tex.py`, wired into `extract_diagrams()` in `talk.py`, with balanced-brace parsing for `\includediagram{...}` arguments.
