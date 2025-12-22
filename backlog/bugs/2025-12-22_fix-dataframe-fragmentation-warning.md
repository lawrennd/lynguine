---
id: "2025-12-22_fix-dataframe-fragmentation-warning"
title: "Fix DataFrame fragmentation warning in _finalize_df"
status: "Completed"
priority: "Medium"
created: "2025-12-22"
last_updated: "2025-12-22"
owner: ""
github_issue: ""
dependencies: ""
tags:
- backlog
- performance
- pandas
- bug
---

# Task: Fix DataFrame Fragmentation Warning in _finalize_df

## Description

The `_finalize_df` method in `/Users/neil/lawrennd/lynguine/lynguine/assess/data.py` (lines 3042-3044) is causing a pandas PerformanceWarning due to DataFrame fragmentation. The current implementation adds missing columns one at a time in a loop:

```python
for column in interface["columns"]:
    if column not in df.columns:
        df[column] = None
```

This approach has poor performance because each assignment causes pandas to create a new internal copy of the DataFrame's structure, leading to fragmentation.

**Warning message:**
```
/Users/neil/lawrennd/lynguine/lynguine/assess/data.py:3044: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  df[column] = None
```

## Acceptance Criteria

- [x] Replace the iterative column addition with a batch operation using `pd.concat(axis=1)` or similar
- [x] Ensure all missing columns from `interface["columns"]` are still added with `None` values
- [x] Verify that the PerformanceWarning no longer appears
- [x] Ensure existing tests pass
- [x] Add a test case that verifies multiple missing columns are added efficiently

## Implementation Notes

**Recommended approach:**

1. Collect all missing columns first:
   ```python
   missing_columns = [col for col in interface["columns"] if col not in df.columns]
   ```

2. Create a DataFrame with the missing columns and concatenate:
   ```python
   if missing_columns:
       missing_df = pd.DataFrame({col: None for col in missing_columns}, index=df.index)
       df = pd.concat([df, missing_df], axis=1)
   ```

   Or alternatively, use dictionary assignment:
   ```python
   if missing_columns:
       df = df.assign(**{col: None for col in missing_columns})
   ```

**Location:** `/Users/neil/lawrennd/lynguine/lynguine/assess/data.py`, lines 3040-3044

**Method:** `_finalize_df(self, df, interface, strict_columns=False)`

## Related

- CIP: None
- PRs: None
- Documentation: [Pandas Performance Documentation](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)

## Progress Updates

### 2025-12-22

Task created to address DataFrame fragmentation warning identified during testing.

### 2025-12-22 (Completed)

Fixed DataFrame fragmentation issue in `_finalize_df` method:
- Replaced iterative `df[column] = None` loop with batch operations using `pd.concat(axis=1)`
- Added handling for both CustomDataFrame and regular pandas DataFrames
- For CustomDataFrame: directly modify underlying `_d["cache"]` DataFrame using `pd.concat()`
- For pandas DataFrame: use `pd.concat()` directly (not `assign()` which can still cause fragmentation)
- Also fixed `set_index` issue to work with both DataFrame types
- Created comprehensive test suite (`test_finalize_df_missing_columns.py`) with 6 test cases
- All tests pass with `-W error::pandas.errors.PerformanceWarning` (treats warnings as errors)
- Existing tests still pass

