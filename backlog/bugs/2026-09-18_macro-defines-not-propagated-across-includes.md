---
id: "2026-09-18_macro-defines-not-propagated-across-includes"
title: "Macro defines not propagated across includes in diagram dependency extraction"
status: "In Progress"
priority: "High"
created: "2026-09-18"
last_updated: "2026-09-18"
category: "bugs"
related_cips: []
owner: "Neil Lawrence"
dependencies:
- "2026-08-09_macro-aware-diagram-dependency-extraction"
tags:
- backlog
- bugs
- dependencies
- diagrams
- macros
- includes
- lamd
---

# Task: Macro defines not propagated across includes in diagram dependency extraction

## Description

Macro-aware diagram dependency extraction in lynguine expands `\define` / `\concat` **only from macros collected in the same file** that contains `\includediagram{...}`. That is not enough for the common snippet pattern where a parent file defines the stem and a child include holds the diagram sequence.

**Observed failure** (`talks/_business/ai-and-commercial-applications-ceibs-global-ceo.pptx`, 2026-09-18):

```
pandoc: .../slides/diagrams/anne-bob-conversation000.emf: openBinaryFile: does not exist
```

- SVGs exist (`anne-bob-conversation000.svg` … `007.svg`).
- mdpp expands paths correctly into the PPTX markdown.
- `dependencies batch` omits those `.emf` paths from `pptxdiagrams`, so make never runs Inkscape.
- Literal-path diagrams in the same talk *are* converted (e.g. `ai/atomic-eye.emf`).

**Reproducing include pattern**:

```markdown
% snippets/_ai/includes/conversation-tedx.md
\define{\stubname}{anne-bob-conversation}
\include{_ai/includes/anne-bob-talk.md}
```

```markdown
% snippets/_ai/includes/anne-bob-talk.md
\includediagram{\diagramsDir/\concat{\stubname}{000}}
```

When `extract_diagrams()` scans `anne-bob-talk.md`, `collect_define_macros()` only sees macros local to that file (`divoptions`, `widthVal`). `\stubname` is invisible. Expansion leaves `\stubname000` (still contains `\`), and the path is dropped by the safety gate.

Same-file cases (e.g. `\basisfunction` defined immediately above `\concat` in `quadratic-basis.md`) work with the 2026-08-09 expander. Cross-include does not.

**Root cause** in `lynguine/util/talk.py` → `extract_diagrams()`:

1. Each input file is scanned independently for diagrams and for `\define`.
2. Parent-file macros are not accumulated into a scope when descending through `\include` / `\includetalkfile`.
3. Child-file `\concat{\stubname}{...}` therefore cannot resolve.

## Acceptance Criteria

- [x] `\define` macros from an including file are available when resolving `\includediagram` paths in files reached via `\include` / `\includetalkfile` (included snippet tree), not only same-file defines.
- [ ] `dependencies batch` on a talk that includes `conversation-tedx.md` / `anne-bob-talk.md` lists `anne-bob-conversation000.emf` … `007.emf` (after `\diagramsDir` substitution) in `pptxdiagrams`.
- [x] Same-file `\define` + `\concat` behaviour from `2026-08-09_macro-aware-diagram-dependency-extraction` remains intact (no regression).
- [x] Unit test covers parent-define / child-`\includediagram` across an include boundary (mirroring `conversation-tedx.md` → `anne-bob-talk.md`).
- [x] Documented limitation updated: which include edges propagate macros, and that this is still bounded expansion (not full gpp).

## Implementation Notes

**Suggested approach** (keep explicit — lynguine “no magic”):

1. When walking the include tree in `extract_diagrams()`, maintain an **inherited macro map** (parent scope ∪ current-file defines; later local defines override).
2. Pass that map into `expand_diagram_path()` for each diagram path found in the current file.
3. Prefer accumulating while traversing includes already discovered by `extract_inputs()`, rather than re-implementing include resolution.
4. Avoid full gpp emulation; only `\define` name substitution and `\concat` as today.

**Validation target**:

```bash
cd talks/_business
dependencies batch ai-and-commercial-applications-ceibs-global-ceo.md \
  --snippets-path "$HOME/lawrennd/snippets/" \
  --diagrams-dir ../slides/diagrams/ \
  | grep anne-bob-conversation
```

Expect EMF paths under `pptxdiagrams:`.

**Files likely touched**:

- `lynguine/util/talk.py` — `extract_diagrams()` include-scoped macros
- `lynguine/util/tex.py` — only if helper API needs a merge/scope helper
- `lynguine/tests/test_util_talk.py` — cross-include case

## Related

- Depends on / residual of: [2026-08-09_macro-aware-diagram-dependency-extraction](../features/2026-08-09_macro-aware-diagram-dependency-extraction.md)
- Requirement: [REQ-0008](../../requirements/req0008_complete-diagram-dependency-extraction.md) (acceptance already requires “included snippet tree”)
- Consumer: lamd `dependencies batch` → `PPTXDEPS`
- Snippets: `_ai/includes/conversation-tedx.md`, `_ai/includes/anne-bob-talk.md` (also `conversation.md`, `conversation-computer.md`)

## Progress Updates

### 2026-09-18

Bug filed after CEIBS Global CEO talk pptx build: Inkscape conversion skipped for anne–bob conversation frames because cross-include `\stubname` was not visible to the dependency scanner. Same-file macro expansion from August landed; include-boundary propagation did not.

### 2026-09-18

`extract_diagrams()` now walks the include tree with an inherited macro map. Parent `\define`s are visible in included files; a child's defines do not leak to siblings; a local `\define` overrides the parent. Unit tests cover the anne–bob include pattern (including a middle include), the sibling boundary, and the local override. Docstrings on `extract_diagrams()` and `expand_diagram_path()` state which include edges carry the map, and that this is still bounded `\define` / `\concat` expansion. Live `dependencies batch` on the CEIBS talk is still unchecked.
