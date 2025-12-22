---
id: "2025-12-22_missing-get-compute-index-method"
title: "Implement missing get_compute_index() method in CustomDataFrame"
status: "Proposed"
priority: "High"
created: "2025-12-22"
last_updated: "2025-12-22"
owner: ""
github_issue: ""
dependencies: ""
tags:
- backlog
- bug
- compute
- critical
---

# Task: Implement missing get_compute_index() method in CustomDataFrame

## Description

The `CustomDataFrame` class is missing the `get_compute_index()` method which is called by referia's `compute_onchange()` function in `review.py`. This causes repeated errors when field widgets change values, preventing PDF generation and other compute-dependent operations from working correctly.

**Error message:**
```
ERROR:referia.util.widgets:2025-12-22 08:50:58,686:An error occurred in FieldWidget.on_value_change: 'CustomDataFrame' object has no attribute 'get_compute_index'
```

**Location of error:** `/Users/neil/lawrennd/referia/referia/assess/review.py`, line 1145

**Calling code:**
```python
def compute_onchange(self):
    if self.index is not None:
        data = self._data
        compute_index = data.get_compute_index(self.index)  # ← Missing method
        if "compute" in self._interface and data is not None:
            if compute_index is not None:
                if self.column_name is not None:
                    self._system.compute.run_onchange(data, compute_index, self.column_name)
```

**Purpose:**
The method should identify whether a given index has compute operations that need to run on change (e.g., timestamp updates, computed fields). It's used to determine if `compute.run_onchange()` should be called when a field value changes.

## Acceptance Criteria

- [ ] Implement `get_compute_index(index)` method in `CustomDataFrame` class
- [ ] Method returns the index if it exists in the dataframe and is valid for compute operations
- [ ] Method returns `None` if the index doesn't exist or isn't valid for compute
- [ ] Method handles both series and non-series type indices appropriately
- [ ] Add comprehensive test suite that would have caught this missing method error
- [ ] Tests cover cases with and without compute operations
- [ ] Tests cover valid and invalid indices
- [ ] Tests verify integration with `compute.run_onchange()`
- [ ] Existing tests still pass
- [ ] Verify fix resolves PDF generation issues in referia

## Implementation Notes

**Inferred behavior:**
Based on the calling context and the fact that it's used to gate `run_onchange()` calls, the method should:

1. Check if the provided `index` exists in the dataframe's indices
2. Return the index if it's valid and the dataframe has compute operations
3. Return `None` if:
   - The index doesn't exist
   - The dataframe has no compute operations defined
   - The index is not valid for compute operations

**Implementation location:** `/Users/neil/lawrennd/lynguine/lynguine/assess/data.py`

**Suggested implementation:**
```python
def get_compute_index(self, index):
    """
    Get the compute index for a given index if it's valid for compute operations.
    
    This method is used by compute_onchange() to determine if compute operations
    should run when a field value changes at a specific index.
    
    :param index: The index to check for compute operations.
    :type index: object
    :return: The index if valid for compute operations, None otherwise.
    :rtype: object or None
    """
    # Check if index exists in the dataframe
    if index not in self.index:
        return None
    
    # Check if compute operations are defined
    if self.compute is None or not self.compute._computes:
        return None
    
    # Return the index if it's valid for compute operations
    return index
```

**Test scenarios:**
1. Index exists and compute is defined → return index
2. Index doesn't exist → return None
3. Compute not defined → return None
4. Empty dataframe → return None
5. Series-type indices → handle appropriately
6. Integration test with actual compute operations

## Related

- CIP: None
- PRs: None
- Related issue: Chapter 1 PDF not produced in ~/OneDrive/referia/theses/drafts/introduction/
- Error log: ~/OneDrive/referia/theses/drafts/introduction/lynguine.log (536,071 lines with repeated errors)

## Progress Updates

### 2025-12-22

Task created to address missing `get_compute_index()` method preventing PDF generation and compute operations from working correctly. Error appears hundreds of times in referia logs.

