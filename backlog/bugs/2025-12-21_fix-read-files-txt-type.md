---
id: "2025-12-21_fix-read-files-txt-type"
title: "Fix read_files failure with unrecognized .txt file type"
status: "Proposed"
priority: "Medium"
created: "2025-12-21"
last_updated: "2025-12-21"
owner: "TBD"
github_issue: ""
dependencies: ""
tags:
- backlog
- bugs
- testing
- file-io
---

# Task: Fix read_files failure with unrecognized .txt file type

## Description

The test `test_read_files` in `lynguine/tests/test_access_io.py` is failing because the `extract_file_type()` function does not recognize `.txt` files as a valid file type.

**Test Location**: `lynguine/tests/test_access_io.py:290`

**Error**:
```
ValueError: Unrecognised type of file in "file1.txt"
```

**Call Stack**:
- `io_module.read_files(filelist)` (test_access_io.py:290)
- `extract_file_type(filename)` (lynguine/access/io.py:541)
- Raises ValueError (lynguine/util/misc.py:143)

## Motivation

The `read_files()` function should be able to handle text files (`.txt`), which are a common file format. The current implementation does not recognize this file type, causing:

1. Test failures
2. Inability to read plain text files in production code
3. User-facing errors when working with `.txt` files

This is likely a simple oversight where `.txt` was not added to the list of recognized file types.

## Acceptance Criteria

- [ ] Add `.txt` file type support to `extract_file_type()` in `lynguine/util/misc.py`
- [ ] Determine appropriate type label for `.txt` files (e.g., "text", "txt", or "plaintext")
- [ ] If needed, implement a reader function for text files in `lynguine/access/io.py`
- [ ] Verify `test_read_files` passes after changes
- [ ] Add additional test cases for text file reading if not already present
- [ ] Ensure consistency with other file type handling

## Implementation Notes

1. Check `lynguine/util/misc.py:extract_file_type()` to see the current list of recognized file types
2. Add `.txt` extension to the recognized types with appropriate type label
3. Verify if a text file reader already exists or needs to be implemented
4. Consider whether other common text formats should be added (`.log`, `.dat`, etc.)

## Related

- Module: `lynguine/util/misc.py` (extract_file_type function)
- Module: `lynguine/access/io.py` (read_files function)
- Test file: `lynguine/tests/test_access_io.py`

## Progress Updates

### 2025-12-21

Test failure identified during full test suite run. The `extract_file_type()` function throws `ValueError` for `.txt` files because this file type is not in the recognized types list. Simple fix: add `.txt` to the recognized file types.

