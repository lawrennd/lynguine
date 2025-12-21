---
id: "2025-12-21_fix-network-error-test-download"
title: "Fix test_network_errors_in_download_url test failure"
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
- download
---

# Task: Fix test_network_errors_in_download_url test failure

## Description

The test `test_network_errors_in_download_url` in `lynguine/tests/test_access_download.py` is failing because it expects a `ValueError` to be raised when network errors occur during URL download, but the exception is not being raised.

**Test Location**: `lynguine/tests/test_access_download.py:169`

**Error**:
```
Failed: DID NOT RAISE <class 'ValueError'>
```

## Motivation

This test is verifying that the download functionality properly handles network errors and raises appropriate exceptions. Currently, the test indicates that network errors may not be properly caught and re-raised as `ValueError`, which could lead to:

1. Unclear error messages for users
2. Improper error handling in calling code
3. Potential for silent failures

## Acceptance Criteria

- [ ] Review the test to understand expected behavior
- [ ] Examine `lynguine/access/download.py` to identify network error handling
- [ ] Determine if the test expectations are correct or if the implementation needs fixing
- [ ] Update either the test or the implementation to ensure network errors are properly handled
- [ ] Verify the test passes after fixes
- [ ] Ensure no other tests are broken by the changes

## Implementation Notes

1. Check what types of network errors should be caught (connection errors, timeouts, etc.)
2. Verify that these errors are being converted to `ValueError` as expected by the test
3. Consider whether `ValueError` is the most appropriate exception type or if a custom exception would be better
4. Ensure error messages are informative for debugging

## Related

- Module: `lynguine/access/download.py`
- Test file: `lynguine/tests/test_access_download.py`

## Progress Updates

### 2025-12-21

Test failure identified during full test suite run. Test expects `ValueError` to be raised on network errors but exception is not being raised. Need to investigate whether test expectations are correct or if error handling needs to be implemented/fixed.

