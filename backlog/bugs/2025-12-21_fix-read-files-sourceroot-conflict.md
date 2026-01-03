---
category: bugs
created: '2025-12-21'
dependencies: ''
github_issue: ''
id: 2025-12-21_fix-read-files-sourceroot-conflict
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
- field-mapping
title: Fix read_files_extracts_file_type test failure with sourceRoot field conflict
---

# Task: Fix read_files_extracts_file_type test failure with sourceRoot field conflict

## Description

The test `test_read_files_extracts_file_type` in `lynguine/tests/test_access_io.py` is failing due to a field name conflict where the field "sourceRoot" already exists in the data and is also being registered as the root field.

**Test Location**: `lynguine/tests/test_access_io.py:319` (line 298 in current file)

**Error**:
```
ValueError: The field "sourceRoot" is already in the data and is registered for setting as the root field.
```

**Call Stack**:
- `io_module.read_files(filelist)` (test_access_io.py:319)
- Raises ValueError (lynguine/access/io.py:552)

## Motivation

This error indicates a conflict in the field naming and mapping system where:

1. A data field named "sourceRoot" already exists in the input data
2. The system is trying to use "sourceRoot" as the name for the root directory field
3. This creates a collision that the validation correctly catches

This could be caused by:
- Test data accidentally including a "sourceRoot" field
- The system choosing a poor name for the root field that conflicts with user data
- Changes to how root fields are handled

## Acceptance Criteria

- [x] Examine the test at line 319 to understand what data is being passed
- [x] Review `lynguine/access/io.py:552` to see the validation logic
- [x] Determine if "sourceRoot" is a reserved field name or if the conflict is legitimate
- [x] Either:
  - Fix the test data to not include "sourceRoot" if it's reserved ✅
  - Change the internal field name for root to avoid conflicts (e.g., "_sourceRoot", "source_root_dir")
  - Update the validation to handle this case more gracefully
- [x] Verify the test passes after changes
- [x] Ensure no other tests break
- [x] Document any reserved field names if applicable

## Implementation Notes

1. The error message suggests explicit validation for field name conflicts
2. Need to determine the design intent: should "sourceRoot" be reserved, or should internal fields use a different naming convention?
3. Consider whether this affects other field names (e.g., "source", "root", etc.)
4. Check if this is related to recent changes in field mapping or root directory handling

## Related

- Module: `lynguine/access/io.py` (read_files function, line 552)
- Test file: `lynguine/tests/test_access_io.py` (line 319/298)
- Related to field mapping and root directory handling

## Progress Updates

### 2025-12-21 - Initial Report

Test failure identified during full test suite run. The test triggers a field name conflict where "sourceRoot" exists both as user data and as an internal field name for the root directory. Need to investigate whether this is a test issue or a design issue with field naming conventions.

### 2025-12-21 - Completed

**Fix implemented and committed** (commit: 397d3d9)

Root cause identified: **Two separate bugs**

1. **Code bug in `read_files()`**: The filereader was determined once from the first file and then reused for all subsequent files. This meant `extract_file_type()` was only called once instead of per-file.
   - **Fix**: Changed to determine reader per file by using `current_reader` variable instead of reassigning `filereader`

2. **Test bug in mock**: The mock was returning the same dictionary object for all calls, so after processing the first file (which added `sourceRoot`), the second file received the same dict object that already contained `sourceRoot`.
   - **Fix**: Changed mock to use `side_effect=lambda x: {'content': 'test'}` to return a new dict for each call

Test `test_read_files_extracts_file_type` now passes ✅

This was a real production bug - files of different types in the same list would all be read using the first file's reader!