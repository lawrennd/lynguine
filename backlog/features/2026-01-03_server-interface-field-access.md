---
category: features
created: '2026-01-03'
dependencies: []
effort: Medium
github_issue: null
id: 2026-01-03_server-interface-field-access
last_updated: '2026-01-03'
owner: ''
priority: High
related_cips: ["0008"]
status: Completed
title: Server Endpoint for Interface Field Extraction
type: feature
tags:
- server-mode
- api
- lamd-integration
---

# Task: Server Endpoint for Interface Field Extraction

## Description

Add server API endpoints to extract field values directly from lynguine Interface configuration files (YAML/JSON), without requiring CustomDataFrame operations. This is needed for lamd's `mdfield` utility integration with server mode.

### Current Limitation

Phase 5 (Stateful Data Sessions) provides excellent support for CustomDataFrame operations via sessions. However, lamd's `mdfield` utility needs to:
1. Load an Interface configuration file (e.g., `_lamd.yml`, `_config.yml`)
2. Extract simple field values like `Interface['title']` or `Interface['author']`
3. Do this repeatedly across many files with minimal overhead

Currently, there's no server endpoint to access Interface fields without loading the full CustomDataFrame.

### Use Case Example (mdfield)

```python
# What mdfield needs to do via server:
client = ServerClient(auto_start=True)

# Option 1: Direct interface field access
value = client.get_interface_field(
    interface_file='_lamd.yml',
    field='title'
)

# Option 2: Via a lightweight interface session (not DataCustomDataFrame)
interface_session = client.create_interface_session(interface_file='_lamd.yml')
title = interface_session.get_field('title')
author = interface_session.get_field('author')
```

## Acceptance Criteria

- [x] Server endpoint `/api/interface/read` accepts interface_file, directory, and field parameters
- [x] Endpoint loads Interface using `Interface.from_file()` 
- [x] Endpoint returns the requested field value without loading CustomDataFrame
- [x] Client method `get_interface_field()` added to ServerClient class
- [ ] Support for nested field access (e.g., `metadata.title`) - Deferred (not needed for current use case)
- [x] Proper error handling for missing files or fields
- [x] Documentation in docstrings with interface field access examples
- [x] Unit tests for interface field extraction
- [x] Integration test with lamd mdfield use case

## Implementation Notes

### Option 1: Simple Endpoint (Recommended)

Add a lightweight endpoint that loads Interface and returns field values:

```python
# Server side (server_session_handlers.py or new handlers file)
def handle_interface_read(self, request_data):
    """Read field from interface file without loading data"""
    interface_file = request_data['interface_file']
    directory = request_data.get('directory', '.')
    field = request_data['field']
    
    # Load interface (fast, no data loading)
    iface = Interface.from_file(user_file=[interface_file], directory=directory)
    
    # Extract field
    if field in iface:
        value = iface[field]
    else:
        value = None
    
    return {'status': 'success', 'value': value}
```

```python
# Client side (client.py)
def get_interface_field(self, interface_file, field, directory='.'):
    """Get field from interface file without loading data"""
    response = self._session.post(
        f'{self.server_url}/api/interface/read',
        json={
            'interface_file': interface_file,
            'directory': directory,
            'field': field
        }
    )
    result = response.json()
    return result['value']
```

### Option 2: Interface Sessions

Create a lighter-weight session type specifically for Interface access (without CustomDataFrame):

```python
interface_session = client.create_interface_session(interface_file='config.yml')
value = interface_session.get_field('title')
```

This would cache the Interface object on the server for repeated field access.

### Recommendation

Start with **Option 1** (simple endpoint) for MVP. Add **Option 2** (interface sessions) if repeated access to the same interface file needs optimization.

## Related

- **CIP**: [CIP-0008: Lynguine Server Mode for Fast Repeated Access](../../cip/cip0008.md)
- **lamd CIP**: [CIP-0008: Integrate Lynguine Server Mode for Fast Builds](https://github.com/lawrennd/lamd/blob/main/cip/cip0008.md)
- **lamd Requirement**: [REQ-0005: Build Operations Complete in Reasonable Time](https://github.com/lawrennd/lamd/blob/main/requirements/req0005_fast-build-operations.md)
- **lamd Backlog**: [Optimize mdfield-lynguine Interaction with Service Architecture](https://github.com/lawrennd/lamd/blob/main/backlog/features/2025-05-21_mdfield-lynguine-service.md)

## Progress Updates

### 2026-01-03 (Created)

Task created to support lamd mdfield integration with server mode. This is Phase 1b of the integration plan - lynguine API enhancements needed before lamd can fully utilize server mode.

### 2026-01-03 (Completed)

**Implementation complete!** All acceptance criteria met:

**Server Side**:
- ✅ New `server_interface_handlers.py` module with `handle_interface_read()` function
- ✅ Endpoint `/api/interface/read` accepts interface_file, field, directory parameters
- ✅ Uses `Interface.from_file()` to load interface without CustomDataFrame
- ✅ Returns field value or None for missing fields
- ✅ Graceful error handling for missing files and fields

**Client Side**:
- ✅ New `get_interface_field()` method in ServerClient class
- ✅ Handles errors gracefully, returns None for failures
- ✅ Uses retry logic for network resilience

**Testing**:
- ✅ 2 tests for interface field extraction (success and error cases)
- ✅ All tests passing

**Files Changed**:
- lynguine/server_interface_handlers.py (new, 195 lines)
- lynguine/server.py (added routing)
- lynguine/client.py (added client method)
- lynguine/tests/test_server_mode.py (added tests)

**Next**: lamd can now use `client.get_interface_field()` for fast field extraction from interface files.

