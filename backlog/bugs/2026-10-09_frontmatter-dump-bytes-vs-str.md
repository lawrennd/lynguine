---
id: "2026-10-09_frontmatter-dump-bytes-vs-str"
title: "write_markdown_file / write_letter_file fail with modern python-frontmatter"
status: "Completed"
priority: "High"
created: "2026-10-09"
last_updated: "2026-10-09"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- frontmatter
- docx
- markdown
---

# Task: write_markdown_file / write_letter_file fail with modern python-frontmatter

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

`lynguine.access.io.write_markdown_file` and `write_letter_file` opened the output file in binary mode (`"wb"`) and called `frontmatter.dump(post, stream)`.

Older `python-frontmatter` encoded to bytes before writing (binary file OK). Newer versions write a `str` into the stream, which raises:

```
TypeError: a bytes-like object is required, not 'str'
```

That breaks the docx path (`write_docx_file` → temp markdown → pandoc), seen from referia web document generation (`Create docx`).

## Acceptance Criteria

- [x] `write_markdown_file` works with current `python-frontmatter` (str dumps)
- [x] `write_letter_file` uses the same version-safe write path
- [x] `write_docx_file` can produce a `.docx` again (via the markdown temp file)
- [x] Unit tests updated for `dumps` → UTF-8 bytes → `"wb"` write

## Implementation Notes

Avoid calling `frontmatter.dump` on an open handle. Use:

1. `text = frontmatter.dumps(post, sort_keys=False)`
2. `raw = text if isinstance(text, bytes) else text.encode("utf-8")`
3. `open(filename, "wb")` + `stream.write(raw)`

Works for both old (bytes dump) and new (str dump) frontmatter.

## Related

- Triggered by: referia web `POST /generate-document/{n}` on thesis introduction configs
- Files: `lynguine/access/io.py`, `lynguine/tests/test_access_io.py`

## Progress Updates

### 2026-10-09

Bug found while testing referia CIP-000B document generation. Fix implemented and committed with this backlog entry.
