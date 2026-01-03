---
category: bugs
created: '2025-12-02'
dependencies: ''
github_issue: ''
id: 2025-12-02_read-files-default-reader-wrong-arg
last_updated: '2025-12-02'
owner: Neil Lawrence
priority: High
related_cips: []
status: Completed
tags:
- backlog
- bug
- io
title: read_files passes full filename to default_file_reader instead of file type
---

# Task: read_files passes full filename to default_file_reader instead of file type

## Diagnosis

In `lynguine/access/io.py`, the `read_files` function at line 541 passes the full filename to `default_file_reader`:

```python
for filename in filelist:
    if not os.path.exists(filename):
        log.warning(f'File "{filename}" is not a file or a directory.')
    if filereader is None:
        filereader = default_file_reader(filename)  # BUG: passes full path
```

But `default_file_reader` expects a file **type** (e.g., `"markdown"`, `"yaml"`), not a filename:

```python
def default_file_reader(typ):
    """
    Return the default file reader for a given type.
    
    :param typ: The type of file to be read.
    :type typ: str
    """
    if typ == "markdown":
        return read_markdown_file
    if typ == "yaml":
        return read_yaml_file
    # ...
    raise ValueError(f'Unrecognised type of file "{typ}".')
```

This results in the error:
```
ValueError: Unrecognised type of file "/Users/neil/lawrennd/publications/_posts/1998-01-01-bishop-mixtures97.md".
```

## Expected Behavior

`read_files` should extract the file type from the filename extension and pass that to `default_file_reader`.

## Proposed Fix

Update `read_files` to derive the type from the filename extension:

```python
if filereader is None:
    # Extract type from filename extension
    _, ext = os.path.splitext(filename)
    ext = ext.lower().lstrip('.')
    # Map extension to type
    ext_to_type = {
        'md': 'markdown',
        'markdown': 'markdown',
        'yml': 'yaml',
        'yaml': 'yaml',
        'json': 'json',
        'bib': 'bibtex',
        'docx': 'docx',
    }
    file_type = ext_to_type.get(ext)
    if file_type is None:
        raise ValueError(f'Unrecognised file extension "{ext}" for file "{filename}".')
    filereader = default_file_reader(file_type)
```

Alternatively, a helper function could be added to derive the type from a filename.

## Acceptance Criteria

- [x] `read_files` correctly derives file type from extension
- [x] `.md` files are recognized as markdown
- [x] `.yml` and `.yaml` files are recognized as yaml
- [ ] Existing tests continue to pass (to be verified)
- [ ] `lamd`'s `mdlist` can read publication markdown files (to be verified)

## Related

- File: `lynguine/access/io.py` line 541 (`read_files`)
- File: `lynguine/access/io.py` line 526 (`default_file_reader`)
- Caller: `lamd/mdlist.py` uses `type="list"` to read multiple markdown files

## Progress Updates

### 2025-12-02

Task created. Issue discovered when testing `mdlist` publication list generation. The fix for `read_list` (passing dict instead of list) revealed this underlying issue in `read_files`.