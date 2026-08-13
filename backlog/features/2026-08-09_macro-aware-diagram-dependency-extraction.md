---
id: "2026-08-09_macro-aware-diagram-dependency-extraction"
title: "Macro-aware diagram dependency extraction"
status: "In Progress"
priority: "High"
created: "2026-08-09"
last_updated: "2026-08-09"
category: "features"
related_cips: []
owner: "Neil Lawrence"
dependencies: []
tags:
- backlog
- features
- dependencies
- diagrams
- macros
- lamd
---

# Task: Macro-aware diagram dependency extraction

## Description

LaMD builds fail at the pandoc step when diagram paths are constructed with gpp macros (for example `\define{\basisfunction}{quadratic_basis}` and `\concat{\basisfunction}{000}` inside `\includediagram{...}`). gpp expands these correctly in the output markdown, but **lynguine's static dependency scanner drops them**, so make never builds the required derived assets (notably `.emf` from `.svg` for pptx).

**Observed failure** (mlfc `basis-functions-and-generalisation.pptx`):

```
File ./slides/diagrams//ml/quadratic_basis000.emf not found in resource path
```

The SVG exists (`slides/diagrams/ml/quadratic_basis000.svg`); the EMF was never a make target because it was not listed in `pptxdiagrams` from `dependencies batch`.

**Root cause** in `lynguine/util/talk.py` → `extract_diagrams()`:

1. `tex.extract_diagrams()` regex-parses `\includediagram{...}` and returns the raw first argument (e.g. `\diagramsDir/ml/\concat{\basisfunction}{000}`).
2. After substituting `\diagramsDir`, any path still containing `\` is **silently skipped** (`if "\\" not in diag_str`).
3. Literal paths in the same file (e.g. `\diagramsDir/ml/quadratic_function000`) are kept and build correctly.

This affects multiple snippets that share the animation pattern: `quadratic-basis.md`, `polynomial-basis.md`, `relu-basis.md`, `radial-basis.md`, `fourier-basis.md`, `hyperbolic-tangent-basis.md`, and related includes in `basis-functions-nn.md`.

**Scope**: Fix belongs in **lynguine** (used by lamd's `dependencies` CLI). Do not patch around this in lamd makefiles or duplicate logic in `lamd/dependencies.py`.

## Acceptance Criteria

- [ ] `\define{...}{...}` macros visible in the same file (or included snippet tree) are applied when resolving diagram paths for dependency extraction.
- [ ] `\concat{base}{suffix}` in diagram paths resolves to a concrete path (e.g. `quadratic_basis` + `000` → `quadratic_basis000`).
- [ ] After `\diagramsDir` substitution, paths like `./slides/diagrams/ml/quadratic_basis000.emf` appear in `dependencies batch` / `dependencies diagrams` output for talks that include the affected snippets.
- [ ] Literal `\includediagram` paths continue to work unchanged (no regression).
- [ ] Unit tests in `lynguine/tests/` cover at least: `\define` + `\concat` in `\includediagram`, and a mixed file with both macro-built and literal diagram names.
- [ ] Documented limitation: which macro forms are supported (start with `\define` and `\concat`; avoid full gpp emulation).

## Implementation Notes

**Suggested approach** (keep explicit and bounded — align with lynguine "no magic" tenet):

1. Add a small helper (e.g. in `lynguine/util/tex.py`) to collect `\define{name}{value}` from file lines (per file, before or while scanning includes).
2. After extracting diagram path strings and substituting `\diagramsDir`, run a **limited macro expander** on each path:
   - Replace `\name` with defined values (single-token macros).
   - Expand `\concat{a}{b}` recursively until no `\concat` remains or a depth limit is hit.
3. Only emit dependency entries when the expanded path contains no remaining `\` macros (same safety gate as today, but after expansion).
4. Consider scoping `\define` per file first; only promote to cross-file if needed (many snippets define `\basisfunction` locally immediately before use).

**Files likely touched**:

- `lynguine/util/talk.py` — `extract_diagrams()`
- `lynguine/util/tex.py` — optional shared expander + tests
- `lynguine/tests/test_util_talk.py`, `lynguine/tests/test_util_tex.py`

**Out of scope for this task**:

- Full gpp preprocessing in the dependency scanner
- lamd-side workarounds (manual EMF builds, makefile hacks)
- Fixing double-slash path normalisation (`diagrams//ml/`) — separate issue if still present after this fix

## Related

- **Requirement**: [REQ-0008: Complete Diagram Dependency Extraction](../../requirements/req0008_complete-diagram-dependency-extraction.md)
- Consumer: lamd `dependencies` / `dependencies batch` → `PPTXDEPS` in `make-talk-flags.mk`
- Example source: `snippets/_ml/includes/quadratic-basis.md` (macro vs literal `\includediagram` in same file)
- Related lamd context: CIP-0005 (validation / dependency visibility); lamd backlog `2026-01-04_optimize-dependency-scanning` (batch extraction — already uses lynguine; benefits from correct diagram list)

## Progress Updates

### 2026-08-09

Task created after diagnosing missing `quadratic_basis*.emf` in mlfc pptx build: SVG present, dependency scanner dropped macro-built paths.

### 2026-08-09

Implemented bounded macro expansion in lynguine (`collect_define_macros`, `expand_diagram_path`, balanced-brace `\includediagram` parsing). Unit tests added; pending validation against lamd build.
