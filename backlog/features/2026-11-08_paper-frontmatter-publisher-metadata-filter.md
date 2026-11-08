---
id: "2026-11-08_paper-frontmatter-publisher-metadata-filter"
title: "paper_frontmatter: extract publisher front matter; exclude from title"
status: "Completed"
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

# Task: paper_frontmatter — publisher front-matter extract + title filter

> Extends CIP-0013 `paper_frontmatter` / `academic_paper_front.v1`.  
> Design home: CIP-0013 § Aspects → `paper_frontmatter` — publisher front matter vs title.

## Plan (summary)

1. **Tag** first-page lines that look like publisher front matter (journal name, volume/issue/pages, year, DOI) and running titles/headers; small sibling list for web-shell / nav text.
2. **Extract** BibTeX-ish fields (`journal`, `volume`, `number`, `pages`, `year`, `doi`) from tagged lines; keep `publisher_front_matter_lines` for audit.
3. **Exclude** tagged lines from title selection; prefer an untagged title line after a tagged header block when both appear.
4. If nothing untagged remains, leave `title` empty (do not promote a header).
5. Keep author extraction order of concerns unchanged for this slice.
6. Regression: existing synthetic front-matter tests stay green; fixtures cover header-before-title, header-only, clean manuscript.
7. **Eval gate:** journal vs conference title hit rates and structured-field fill rates on a held-out local corpus; conference title hit should not regress.

## Motivation

On publisher journal PDFs, first-page running titles/headers and bibliographic lines are often mistaken for the paper title. Conference-style first pages show this less often. Detecting publisher front matter is easier than recognising titles: once detected, keep the metadata as structured fields (and raw audit lines), and exclude it from title selection — not detect-and-discard.

## Description

### Pipeline

```
page-1 lines
  → tag publisher front matter / running headers / web-shell
  → parse BibTeX-ish fields + record publisher_front_matter_lines
  → title = first suitable untagged line(s)
  → authors as today
```

### In scope

- Positive detectors for journal + volume/biblio/DOI-like lines
- Structured extract: `journal`, `volume`, `number`, `pages`, `year`, `doi`
- Audit list: `publisher_front_matter_lines`
- Exclude tagged lines from title candidates
- Soft-fail (empty title) when only tagged lines remain
- Synthetic fixtures + unit tests
- Documented re-eval summary on a local corpus (do not commit corpus PDFs)

### Out of scope

- OCR / image-only titles
- Author-list completeness recovery (separate follow-on if needed)
- Changing aspect grain (still one record per document)
- Full publisher coverage guarantees

## Acceptance Criteria

- [x] Engine tags publisher front-matter / running-header lines and does not select them as `title`
- [x] When a real title follows a tagged header on the same page, that title is preferred
- [x] Header-only pages yield empty `title` (not the journal line)
- [x] Existing `paper_frontmatter` / `form_fields` / `references` tests remain green
- [x] New fixtures cover: header-before-title; header-only; clean manuscript with no publisher lines
- [x] Emits BibTeX-ish fields (`journal`, `volume`, `number`, `pages`, `year`, `doi`) when parseable; null when absent
- [x] Emits `publisher_front_matter_lines` audit list (tagged lines; web-shell included without inventing biblio fields)
- [x] Local-corpus re-eval recorded (title hit + journal/volume/doi fill rates by output type)

## Related

- CIP: 0013
- Prior task: `2026-11-08_document-paper-frontmatter-v1` (Completed)

## Progress Updates

### 2026-11-08
Task created (Ready). Design written into CIP-0013 before coding. Motivation kept to layout facts only (no consumer or corpus identifiers).

### 2026-11-08 (implementation — exclude only)
Added `is_publisher_front_matter` / `strip_leading_publisher_front_matter` and wired tag-and-exclude into `extract_frontmatter`. Unit fixtures green. Local re-eval (n=840): journal title hit ~52% → **69.4%**; conference **87.5%** unchanged. Status briefly marked Completed — **under-delivered vs intent** (detect without structured extract).

### 2026-11-08 (extract follow-through)
Reopened In Progress. Added `parse_publisher_front_matter`; `extract_frontmatter` now returns BibTeX-ish fields + `publisher_front_matter_lines` while still excluding tagged lines from title. CIP design updated to tag → extract → exclude. Unit tests extended (22 passed).

### 2026-11-08 (structured-field re-eval)
Aggregate-only n=840. Title hit unchanged vs exclude-only: overall **73.1%**; journal **69.4%**; conference **87.5%**. Journal fill rates: journal **43.8%**, volume **33.8%**, doi **21.1%**, year **31.5%**, number **15.9%**, pages **17.4%**, audit_any **85.3%**. Conference fill rates stay low (journal **1.7%**, audit_any **22.2%**) as expected. Status → Completed.
