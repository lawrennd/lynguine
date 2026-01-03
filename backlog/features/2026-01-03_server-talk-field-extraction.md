---
category: features
created: '2026-01-03'
dependencies: ["2026-01-03_server-interface-field-access"]
effort: Medium
github_issue: null
id: 2026-01-03_server-talk-field-extraction
last_updated: '2026-01-03'
owner: ''
priority: High
related_cips: ["0008"]
status: Proposed
title: Server Endpoint for Markdown Frontmatter Field Extraction
type: feature
tags:
- server-mode
- api
- lamd-integration
- markdown
---

# Task: Server Endpoint for Markdown Frontmatter Field Extraction

## Description

Add server API endpoint to extract field values from markdown document frontmatter (YAML headers), mirroring the `lynguine.util.talk.talk_field()` functionality. This is needed for lamd's `mdfield` utility to fully leverage server mode.

### Current Limitation

lamd's `mdfield` utility extracts fields from markdown documents using `talk_field()`, which:
1. Parses YAML frontmatter from markdown files
2. Falls back to configuration files if field not found in document
3. Handles various data types and formatting

Currently, this requires direct Python function calls, incurring full startup overhead on every invocation.

### Use Case Example (mdfield)

```python
# What mdfield needs to do via server:
client = ServerClient(auto_start=True)

# Extract field from markdown frontmatter with config fallback
value = client.extract_talk_field(
    field='title',
    markdown_file='my-talk.md',
    config_files=['_lamd.yml', '_config.yml']
)

# Alternative: create a talk session for repeated field extraction
talk_session = client.create_talk_session(
    markdown_file='my-talk.md',
    config_files=['_lamd.yml', '_config.yml']
)
title = talk_session.get_field('title')
author = talk_session.get_field('author')
venue = talk_session.get_field('venue')
```

## Acceptance Criteria

- [ ] Server endpoint `/api/talk/field` accepts markdown_file, field, and config_files parameters
- [ ] Endpoint wraps `lynguine.util.talk.talk_field()` functionality
- [ ] Falls back to config files when field not in markdown frontmatter
- [ ] Handles FileFormatError gracefully (same as talk_field)
- [ ] Client method `extract_talk_field()` added to ServerClient class
- [ ] Support for array formatting (e.g., categories as string list)
- [ ] Environment variable expansion in returned paths (e.g., `$HOME`)
- [ ] Proper error handling and empty string returns for missing fields
- [ ] Documentation updated with markdown field extraction examples
- [ ] Unit tests for talk field extraction via server
- [ ] Integration test with actual lamd mdfield use case

## Implementation Notes

### Option 1: Simple Endpoint (Recommended for MVP)

Wrap the existing `talk_field()` function:

```python
# Server side (server_handlers.py or server_talk_handlers.py)
from lynguine.util.talk import talk_field
from lynguine.util.yaml import FileFormatError
from lynguine.config.interface import Interface

def handle_talk_field(self, request_data):
    """Extract field from markdown frontmatter with config fallback"""
    field = request_data['field']
    markdown_file = request_data['markdown_file']
    config_files = request_data.get('config_files', [])
    
    try:
        # Try markdown file first
        value = talk_field(field, markdown_file, user_file=config_files)
    except FileFormatError:
        # Fall back to config files
        try:
            iface = Interface.from_file(user_file=config_files, directory='.')
            value = iface[field] if field in iface else ""
        except Exception as e:
            value = ""
    except Exception as e:
        value = ""
    
    # Handle formatting (categories, env vars, etc.)
    if isinstance(value, list) and field == 'categories':
        value = "['" + "', '".join(value) + "']"
    elif isinstance(value, str):
        value = os.path.expandvars(value)
    
    return {'status': 'success', 'value': value}
```

```python
# Client side (client.py)
def extract_talk_field(
    self,
    field: str,
    markdown_file: str,
    config_files: Optional[List[str]] = None
):
    """Extract field from markdown frontmatter with config fallback"""
    response = self._session.post(
        f'{self.server_url}/api/talk/field',
        json={
            'field': field,
            'markdown_file': markdown_file,
            'config_files': config_files or []
        }
    )
    result = response.json()
    return result['value']
```

### Option 2: Talk Sessions

Create sessions that load and cache parsed frontmatter for repeated field access:

```python
talk_session = client.create_talk_session(
    markdown_file='talk.md',
    config_files=['_lamd.yml']
)

# Repeated field access without re-parsing
title = talk_session.get_field('title')
author = talk_session.get_field('author')
date = talk_session.get_field('date')
```

This would be beneficial if mdfield is called multiple times on the same markdown file.

### Recommendation

1. Start with **Option 1** (simple endpoint) for MVP and immediate mdfield integration
2. Add **Option 2** (talk sessions) if profiling shows repeated parsing overhead
3. Consider caching parsed frontmatter on server side even with Option 1

### Dependency

This task depends on **2026-01-03_server-interface-field-access** for the Interface fallback functionality.

## Related

- **Dependency**: [Server Endpoint for Interface Field Extraction](./2026-01-03_server-interface-field-access.md)
- **CIP**: [CIP-0008: Lynguine Server Mode for Fast Repeated Access](../../cip/cip0008.md)
- **lamd CIP**: [CIP-0008: Integrate Lynguine Server Mode for Fast Builds](https://github.com/lawrennd/lamd/blob/main/cip/cip0008.md)
- **lamd Requirement**: [REQ-0005: Build Operations Complete in Reasonable Time](https://github.com/lawrennd/lamd/blob/main/requirements/req0005_fast-build-operations.md)
- **lamd Backlog**: [Optimize mdfield-lynguine Interaction with Service Architecture](https://github.com/lawrennd/lamd/blob/main/backlog/features/2025-05-21_mdfield-lynguine-service.md)

## Progress Updates

### 2026-01-03

Task created to support lamd mdfield integration with server mode. This is Phase 1b of the integration plan - lynguine API enhancements needed before lamd can fully utilize server mode.

This task builds on the Interface field access endpoint to provide complete mdfield functionality via server.

