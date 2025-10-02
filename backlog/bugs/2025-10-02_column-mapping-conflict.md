---
id: "2025-10-02_column-mapping-conflict"
title: "Column Mapping Conflict with Auto-Generated Names"
status: "Completed"
priority: "High"
created: "2025-10-02"
last_updated: "2025-10-02"
owner: "AI Assistant"
github_issue: ""
dependencies: ""
tags:
- backlog
- bug
- mapping
- column-names
---

# Task: Column Mapping Conflict with Auto-Generated Names

## Description

The `update_name_column_map` method in `CustomDataFrame` prevents overwriting auto-generated column mappings, causing conflicts when users want to provide explicit mappings for columns with invalid names.

### Problem Details

1. **Auto-Generation**: When column names contain invalid characters (spaces, question marks, parentheses), the system auto-generates camelCase names using `to_camel_case()`
2. **Conflict Prevention**: The `update_name_column_map` method prevents overwriting existing mappings to protect against accidental overwrites
3. **User Intent**: Users want to provide explicit, meaningful names for important columns instead of using auto-generated names
4. **Exception Case**: This is an exceptional situation where the user legitimately wants to override auto-generated mappings

### Example

```python
# Column name with invalid characters
"What is your name (primary organiser and point of contact)?"

# Auto-generated name
"whatIsYourNamePrimaryOrganiserAndPointOfContact"

# User wants to map to
"Name"

# Results in conflict error
ValueError: Column "What is your name (primary organiser and point of contact)?" already exists in the name-column map...
```

## Acceptance Criteria

- [x] Users can override auto-generated column mappings with explicit mappings
- [x] System still prevents accidental overwrites of user-defined mappings
- [x] Auto-generation continues to work for unmapped columns
- [x] Clear logging when auto-generated mappings are overwritten
- [x] No breaking changes to existing functionality

## Implementation Notes

The solution detects auto-generated names by comparing the existing mapping with the result of `to_camel_case(column)`. If they match, the system allows overwriting and logs a warning.

### Code Changes

Modified `update_name_column_map` method in `lynguine/assess/data.py`:
- Added detection logic for auto-generated names
- Allow overwriting when original name matches auto-generated name
- Clear old mapping before adding new one
- Maintain protection for user-defined mappings

## Related

- Issue discovered during referia application processing
- Affects any use case with columns containing invalid characters

## Progress Updates

### 2025-10-02
Task created after identifying the mapping conflict issue during referia application processing.

### 2025-10-02
Fixed the issue by modifying the `update_name_column_map` method to detect and allow overwriting of auto-generated mappings while maintaining protection for user-defined mappings.

## Testing

The fix was tested with a real referia application that had columns with invalid names:
- Successfully processed 56 rows of data
- Explicit mappings now override auto-generated ones
- System continues to auto-generate for unmapped columns
