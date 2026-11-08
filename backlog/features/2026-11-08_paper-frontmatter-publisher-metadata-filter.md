---
id: "2026-11-08_paper-frontmatter-publisher-metadata-filter"
title: "paper_frontmatter: tag publisher front matter; exclude from title"
status: "Ready"
priority: "High"
created: "2026-11-08"
last_updated: "2026-11-08"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-08_document-paper-frontmatter-v1"
tags:
- backlog
- features
- access
- documents
- cip0013
- paper-frontmatter
---

# Task: paper_frontmatter — publisher front-matter filter

> Extends CIP-0013 `paper_frontmatter` / `academic_paper_front.v1`.  
> Design home: CIP-0013 § Aspects → `paper_frontmatter` — publisher front matter vs title.

## Plan (summary)

1. **Tag** first-page lines that look like publisher front matter (journal name, volume/issue/pages, year, DOI) and running titles/headers; small sibling list for web-shell / nav text.
2. **Exclude** tagged lines from title selection; prefer an untagged title line after a tagged header block when both appear.
3. If nothing untagged remains, leave `title` empty (do not promote a header).
4. Keep author extraction order of concerns unchanged for this slice.
5. Regression: existing synthetic front-matter tests stay green; add fixtures for header-before-title and header-only pages.
6. **Eval gate:** re-check journal-heavy vs conference-style title hit rates on a held-out local corpus; running-header misses should drop; conference hit rate should not regress.

## Motivation

On publisher journal PDFs, first-page running titles/headers and bibliographic lines are often mistaken for the paper title. Conference-style first pages show this less often. Detecting publisher front matter is easier than recognising titles and should be an explicit filter, not more one-off “first line” tweaks.

## Description

### Pipeline step (insert before title choice)

```
page-1 lines
  → tag publisher front matter / running headers / web-shell
  → title = first suitable untagged line(s)
  → authors as today
```

### In scope

- Positive detectors for journal + volume/biblio/DOI-like lines
- Exclude tagged lines from title candidates
- Soft-fail (empty title) when only tagged lines remain
- Synthetic fixtures + unit tests
- Documented re-eval summary on a local corpus (do not commit corpus PDFs)

### Out of scope

- OCR / image-only titles
- Author-list completeness recovery (separate follow-on if needed)
- Changing aspect grain or `extract_paper_frontmatter` public shape
- Full publisher coverage guarantees

## Acceptance Criteria

- [ ] Engine tags publisher front-matter / running-header lines and does not select them as `title`
- [ ] When a real title follows a tagged header on the same page, that title is preferred
- [ ] Header-only pages yield empty `title` (not the journal line)
- [ ] Existing `paper_frontmatter` / `form_fields` / `references` tests remain green
- [ ] New fixtures cover: header-before-title; header-only; clean manuscript with no publisher lines
- [ ] Local-corpus re-eval recorded in task progress (journal vs conference title-hit / miss-family counts)

## Related

- CIP: 0013
- Prior task: `2026-11-08_document-paper-frontmatter-v1` (Completed)

## Progress Updates

### 2026-11-08
Task created (Ready). Design written into CIP-0013 before coding. Motivation kept to layout facts only (no consumer or corpus identifiers).
