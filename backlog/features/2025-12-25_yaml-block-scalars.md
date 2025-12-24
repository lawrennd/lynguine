---
id: 2025-12-25_yaml-block-scalars
title: "Use block scalars for multiline strings in YAML output"
status: Completed
priority: Medium
created: 2025-12-25
updated: 2025-12-25
owner: 
tags:
  - yaml
  - io
  - formatting
dependencies: []
---

## Description

When lynguine writes YAML files using `write_yaml_file()`, multiline strings are currently output with escaped newlines (`\n`) in quoted format. This makes the YAML files harder to read for text-heavy content like comments or descriptions.

**Current output:**
```yaml
Summary Comment: "This thesis covers the challenges of integrating machine\
    \ learning solutions into affective robotics. In particular the case\
    \ where the robots continually learn is considered."
```

**Desired output:**
```yaml
Summary Comment: |-
  This thesis covers the challenges of integrating machine
  learning solutions into affective robotics. In particular the case
  where the robots continually learn is considered.
```

*(Note: `|-` is literal block scalar with trailing newlines stripped - cleaner than `|`)*

## Motivation

- **Readability**: Block scalars are much easier to read for multiline text
- **Git diffs**: Cleaner diffs when text content changes
- **Standard practice**: Most YAML formatters prefer block scalars for multiline strings
- **User experience**: Better for content-heavy applications like referia reviews

## Implementation

Modify `lynguine/access/io.py::write_yaml_file()` to use a custom YAML representer:

```python
def write_yaml_file(data, filename):
    """
    Write a yaml file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the yaml file.
    :type filename: str
    """
    
    # Custom representer for multiline strings
    def str_representer(dumper, data):
        if '\n' in data:
            # Use literal block scalar for multiline strings
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    
    yaml.add_representer(str, str_representer)
    
    writedata = yaml_prep(data)
    with open(filename, "w") as stream:
        try:
            log.debug(f'Writing yaml file "{filename}".')
            yaml.dump(writedata, stream, sort_keys=False, allow_unicode=True, width=70)
        except yaml.YAMLError as exc:
            log.warning(exc)
```

**Considerations:**
- PyYAML produces `|-` (literal, strip trailing newlines) with `style='|'` - this is correct
- Could use `>` (folded) for paragraph text, but `|` is safer
- May want to make this configurable via `details` parameter
- Consider adding `default_flow_style=False` for nested structures

**Verified behavior:**
```python
# Tested with PyYAML - produces:
# short: single line
# long: |-
#   This is a long string
#   with multiple lines
#   of text.
```

## Acceptance Criteria

- [x] Multiline strings in YAML output use `|` block scalar style
- [x] Short single-line strings remain inline
- [x] Existing YAML reading functionality unchanged
- [x] Tests added for multiline string formatting
- [x] Documentation updated

## Implementation Notes

**Files to modify:**
- `lynguine/access/io.py` - `write_yaml_file()` function

**Testing:**
- Test with multiline strings containing newlines
- Test with single-line strings
- Test with edge cases (trailing newlines, empty strings)
- Verify referia review outputs format correctly

## Related

- Affects all lynguine YAML output
- Particularly important for referia review outputs
- Related to data-oriented architecture principles (human-readable data)

## Progress Updates

### 2025-12-25
Task created with Proposed status. Identified during referia YAML output development.

**Status: Completed**

Implementation completed with the following changes:

1. **Initial Bug Fix**: Fixed `write_yaml_file()` to use `Dumper=yaml.SafeDumper`
   - Previously, the custom `multiline_str_representer` was defined but never used
   - This fixed short multiline strings but revealed a deeper issue

2. **Root Cause Discovered**: PyYAML's Emitter overrides representer style choices for long strings
   - Long multiline strings (>500 chars) were still using quoted format with escaped `\n`
   - PyYAML falls back to quoted strings when complexity threshold is exceeded
   - The `width=70` parameter was also removed to give PyYAML more flexibility

3. **Final Solution - Custom Dumper**: Created `LynguineSafeDumper` class
   - Subclasses `yaml.SafeDumper` to preserve safety features
   - Overrides `choose_scalar_style()` to force block scalar style for multiline strings
   - Prevents PyYAML from falling back to quoted strings for long text
   - Handles strings of any length (tested up to 3000+ characters)

4. **Tests Added**: Added comprehensive tests in `lynguine/tests/test_access_io.py`:
   - `test_write_yaml_file` - Updated to verify LynguineSafeDumper is used
   - `test_write_yaml_file_multiline_strings` - Tests block scalar formatting for multiline strings
   - `test_write_yaml_file_special_characters` - Tests tabs, quotes, backslashes, and mixed content
   - `test_write_yaml_file_unicode_preservation` - Tests Chinese characters, emoji, and multiline unicode

5. **Verification**: All 15 YAML tests pass, confirming:
   - ✅ Multiline strings use `|-` or `|` block scalar format
   - ✅ Works for strings of any length (short and 2500+ char strings)
   - ✅ Single-line strings remain inline
   - ✅ Unicode characters (世界, 🌍) preserved correctly with `allow_unicode=True`
   - ✅ Special characters (tabs, quotes, backslashes, asterisks) handled correctly
   - ✅ Round-trip reading/writing maintains data integrity
   - ✅ Referia review output now uses clean block scalar format

**Technical Details**:
- Uses `|` (literal) style for all multiline strings (preserves line breaks exactly)
- Does not use `>` (folded) style - this is intentional for safety and predictability
- Unicode support via `allow_unicode=True` parameter
- Tabs remain escaped as `\t` in YAML (correct behavior)
- Custom dumper approach works around PyYAML's internal style overriding for long strings

