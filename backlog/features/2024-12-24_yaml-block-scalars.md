---
id: 2024-12-24_yaml-block-scalars
title: "Use block scalars for multiline strings in YAML output"
status: Proposed
priority: Medium
created: 2024-12-24
updated: 2024-12-24
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
Summary Comment: |
  This thesis covers the challenges of integrating machine
  learning solutions into affective robotics. In particular the case
  where the robots continually learn is considered.
```

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
- Use `|` (literal) to preserve line breaks
- Could use `>` (folded) for paragraph text, but `|` is safer
- May want to make this configurable via `details` parameter
- Consider adding `default_flow_style=False` for nested structures

## Acceptance Criteria

- [ ] Multiline strings in YAML output use `|` block scalar style
- [ ] Short single-line strings remain inline
- [ ] Existing YAML reading functionality unchanged
- [ ] Tests added for multiline string formatting
- [ ] Documentation updated

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

### 2024-12-24
Task created with Proposed status. Identified during referia YAML output development.

