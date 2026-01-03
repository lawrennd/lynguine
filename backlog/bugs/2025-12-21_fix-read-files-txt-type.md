---
category: bugs
created: '2025-12-21'
dependencies: ''
github_issue: ''
id: 2025-12-21_fix-read-files-txt-type
last_updated: '2025-12-21'
owner: TBD
priority: Medium
related_cips: []
status: Completed
tags:
- backlog
- bugs
- testing
- file-io
title: Fix read_files failure with unrecognized .txt file type
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

- [x] Add `.txt` file type support to `extract_file_type()` in `lynguine/util/misc.py`
- [x] Determine appropriate type label for `.txt` files (e.g., "text", "txt", or "plaintext")
- [x] If needed, implement a reader function for text files in `lynguine/access/io.py`
- [x] Verify `test_read_files` passes after changes
- [x] Add additional test cases for text file reading if not already present
- [x] Ensure consistency with other file type handling

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

### 2025-12-21 - Initial Report

Test failure identified during full test suite run. The `extract_file_type()` function throws `ValueError` for `.txt` files because this file type is not in the recognized types list. Simple fix: add `.txt` to the recognized file types.

### 2025-12-21 - Completed

**Fix implemented and committed** (commit: d458ce2)

Changes made:
- Added `"txt"` to recognized file extensions in `extract_file_type()` (lynguine/util/misc.py)
- Implemented `read_txt_file()` function in `lynguine/access/io.py`
- Registered txt reader in `default_file_reader()` function
- Test `test_read_files` now passes ✅

The fix was straightforward: added txt file type recognition and a simple reader that returns file content in a dictionary format, consistent with other file type readers.