---
id: "2025-12-02_read-data-list-type-passes-dict"
title: "read_data passes dict to read_list instead of extracting filelist"
status: "Ready"
priority: "High"
created: "2025-12-02"
last_updated: "2025-12-02"
owner: "Neil Lawrence"
github_issue: ""
dependencies: ""
tags:
- backlog
- bug
- io
---

# Task: read_data passes dict to read_list instead of extracting filelist

## Diagnosis

The `read_list` function is designed to accept a list of filenames:

```python
def read_list(filelist):
    """
    Read from a list of files.

    :param filelist: The list of files to be read.
    :type filelist: list
    ...
    """
    return read_files(filelist)
```

This is confirmed by the test in `test_access_io.py`:

```python
def test_read_list(mocker):
    mocker.patch('lynguine.access.io.read_files', return_value=pd.DataFrame([{'data': 'content'}]))
    filelist = ['file1.txt', 'file2.txt']
    result = io_module.read_list(filelist)  # passes list directly
```

However, in `read_data` at line 1900:

```python
elif ftype == "list":
    df = read_list(details)  # BUG: passes dict, not list
```

The `details` parameter is the full input configuration dict, not a list of files. This causes an `AttributeError: 'dict' object has no attribute 'sort'` when `read_files` tries to call `filelist.sort()`.

## Expected Behavior

When `ftype == "list"`, `read_data` should extract the filelist from the details dict before passing to `read_list`. The interface is typically configured as:

```python
interface["input"]["filename"] = ['file1.md', 'file2.md']  # list of files
interface["input"]["type"] = "list"
interface["input"]["base_directory"] = "/path/to/base"
```

## Proposed Fix

Update `read_data` to extract and construct the full file paths:

```python
elif ftype == "list":
    filelist = details.get("filename", [])
    base_dir = details.get("base_directory", "")
    if base_dir:
        filelist = [os.path.join(base_dir, f) for f in filelist]
    df = read_list(filelist)
```

## Acceptance Criteria

- [ ] `read_data` correctly extracts filelist from details dict when `type="list"`
- [ ] Existing test `test_read_list` continues to pass
- [ ] Add integration test for `read_data` with `type="list"`
- [ ] `lamd`'s `mdlist` tool works correctly with multiple input files

## Related

- File: `lynguine/access/io.py` line 1900 (`read_data`), line 497 (`read_list`), line 535 (`read_files` calls `.sort()`)
- Test: `lynguine/tests/test_access_io.py` line 228
- Caller: `lamd/mdlist.py` sets `type="list"` for multiple files

## Progress Updates

### 2025-12-02

Task created. Issue discovered when using `lamd`'s `mdlist` tool to generate publication lists from multiple markdown files. The tool sets `interface["input"]["type"] = "list"` with a list of filenames in `interface["input"]["filename"]`, but `read_data` passes the entire details dict to `read_list`.

Bug verified through code inspection and simulation testing. Confirmed that:
1. `read_data` at line 1900 passes entire `details` dict to `read_list`
2. `read_list` expects a list parameter and passes it to `read_files`
3. `read_files` calls `filelist.sort()` at line 535, which fails with `AttributeError: 'dict' object has no attribute 'sort'`
4. This code path is untested - existing test correctly passes a list directly to `read_list`

Status updated to Ready. Ready for implementation of proposed fix.

