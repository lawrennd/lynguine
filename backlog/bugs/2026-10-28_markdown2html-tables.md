---
id: "2026-10-28_markdown2html-tables"
title: "markdown2html does not render GitHub-style pipe tables"
status: "Completed"
priority: "High"
created: "2026-10-28"
last_updated: "2026-10-28"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- markdown
- tables
- markdown2html
- liquid
---

# Bug: `markdown2html` collapses pipe tables to a paragraph

> Backlog tasks are DOING the work. This is a small local fix in
> `lynguine.util.misc.markdown2html`; it does not need a CIP.

Discovered while serving the AI@Cam Programme Manager written-exercise
review (`applications/2026-10-19_ai-cam_programme-manager/written-exercise/`):
the GFM mapping table at the bottom of the viewer renders as one
paragraph of pipes instead of an HTML table.

## Description

`markdown2html` calls Python-Markdown with no extensions:

```python
return markdown.markdown(text)
```

The `tables` extension is off by default, so a pipe table such as

```markdown
| Part | Interview blocks |
| --- | --- |
| 1 | community, say-no |
```

becomes a single `<p>| Part | Interview blocks | …</p>` instead of
`<table>…</table>`.

The same helper is the Liquid `markdownify` filter
(`lynguine.util.liquid.markdownify`) and is what referia web Markdown
widgets use. Review YAML that already contains correct GFM tables is
therefore not at fault.

## Acceptance Criteria

- [x] `markdown2html` enables Python-Markdown's built-in `tables`
      extension.
- [x] A GFM pipe table converts to an HTML `<table>` with header and
      body cells.
- [x] Existing heading conversion still yields `<h1>Test</h1>` for
      `# Test`.
- [x] Liquid `markdownify` continues to call `markdown2html` (no parallel
      renderer).

## Implementation Notes

One-line change in `lynguine/util/misc.py`:

```python
return markdown.markdown(text, extensions=["tables"])
```

Do not enable the `extra` bundle; that would also turn on footnotes,
fenced code, and other syntax and is a wider rendering change than this
bug needs. `markdown = "*"` in `pyproject.toml` already provides the
extension.

Add a regression test next to `test_markdown2html` in
`lynguine/tests/test_util_misc.py`.

## Related

- referia web viewer Markdown widgets
- `lynguine.util.liquid.markdownify`
- AI@Cam Programme Manager written-exercise mapping table

## Progress Updates

### 2026-10-28

Task created after diagnosing that the written-exercise mapping table
failed to render because `markdown2html` omits `extensions=["tables"]`.

Implementation on `bug-markdown2html-tables`: enable `tables` in
`markdown2html`, add a pipe-table regression test, record the change
under `[Unreleased]` in CHANGELOG.
