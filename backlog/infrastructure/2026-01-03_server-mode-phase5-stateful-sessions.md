---
id: "2026-01-03_server-mode-phase5-stateful-sessions"
title: "Server Mode Phase 5: Stateful Data Sessions"
created: "2026-01-03"
last_updated: "2026-01-03"
status: "Proposed"
priority: "Medium"
category: "infrastructure"
owner: "lawrennd"
dependencies:
- "2026-01-03_server-mode-phase3-robustness"
related_cips:
- cip0008
---

# Task: Server Mode Phase 5 - Stateful Data Sessions

## Description

Implement stateful data sessions where the server loads lynguine interface files and maintains data in memory, allowing clients to interact via lightweight index/value operations instead of transferring entire DataFrames over HTTP.

**Goal**: Efficient interactive data exploration with minimal data transfer

**Current Limitation**: Current server mode transfers entire DataFrames over HTTP for each `read_data()` call, which is inefficient for large datasets and interactive workflows.

**Proposed Solution**: 
- Server initializes with a lynguine interface file
- Server loads and maintains data in memory (session state)
- Clients send lightweight commands: `set_index()`, `get_value()`, `get_slice()`, etc.
- Only indices and values transfer over HTTP, not full DataFrames

## Acceptance Criteria

- [ ] Session management (create, list, delete sessions)
- [ ] Server can initialize sessions with lynguine interface files
- [ ] Client can send index/value operations to sessions
- [ ] Operations: `set_index()`, `get_value()`, `get_slice()`, `get_column()`, `filter()`, etc.
- [ ] Session isolation (multiple clients, separate sessions)
- [ ] Session timeout and cleanup
- [ ] Memory management (limits, monitoring)
- [ ] Tests for session lifecycle and operations
- [ ] Documentation for stateful session API

## Success Criteria

- Minimal data transfer (only indices/values, not full DataFrames)
- Support for interactive data exploration workflows
- Multiple concurrent sessions
- Clear session lifecycle management

## Motivation

### Current Approach (Stateless)

```python
# Client transfers entire DataFrame each time
df1 = client.read_data(interface_file='large_data.yml')  # Transfer 10MB
df2 = client.read_data(interface_file='large_data.yml')  # Transfer 10MB again
value = df2.loc[100, 'column']
```

**Problem**: Transfers same large dataset multiple times over HTTP

### Proposed Approach (Stateful Sessions)

```python
# Server loads data once, client sends lightweight commands
session = client.create_session(interface_file='large_data.yml')  # Transfer 10MB once

# Subsequent operations only transfer indices/values
value = session.get_value(index=100, column='column')  # Transfer ~bytes
slice_df = session.get_slice(start=100, end=200)      # Transfer only slice
filtered = session.filter(column='status', value='active')  # Transfer only filtered rows
```

**Benefits**:
- Dramatically reduced HTTP traffic
- Faster interactive exploration
- Server maintains data in memory (already loaded)
- Natural fit for iterative/exploratory workflows

## Implementation Scope

### Session Management

- **Create session**: `POST /api/sessions` with interface file
- **List sessions**: `GET /api/sessions`
- **Get session info**: `GET /api/sessions/{session_id}`
- **Delete session**: `DELETE /api/sessions/{session_id}`
- **Session metadata**: data shape, columns, memory usage, created time

### Data Operations

Stateful operations on session data:

- **get_value(index, column)**: Get single value
- **get_slice(start, end, columns)**: Get row slice
- **get_column(column)**: Get entire column
- **filter(column, operator, value)**: Filter rows
- **sort(column, ascending)**: Sort data
- **get_unique(column)**: Get unique values
- **get_stats(column)**: Get column statistics

### Client API

```python
from lynguine.client import ServerClient

client = ServerClient(auto_start=True)

# Create session
session = client.create_session(
    interface_file='large_data.yml',
    session_name='my_exploration'
)

# Use session
value = session.get_value(index=100, column='name')
slice_df = session.get_slice(start=0, end=100)
filtered = session.filter(column='age', operator='>', value=30)

# Session info
info = session.info()
print(f"Shape: {info['shape']}, Memory: {info['memory_mb']}MB")

# Cleanup
session.delete()
# Or: client.delete_session(session.id)
```

### Server Implementation

- **Session storage**: In-memory dict of session_id -> (data, metadata)
- **Session IDs**: UUID-based unique identifiers
- **Timeout**: Configurable per-session timeout (default: 1 hour)
- **Memory limits**: Configurable max total memory for all sessions
- **Cleanup**: Automatic cleanup of expired sessions

### Session Isolation

- Each session has isolated data and state
- Multiple clients can have separate sessions
- Sessions identified by UUID
- No data sharing between sessions (by default)

## Technical Considerations

### Memory Management

- Track memory usage per session
- Configurable limits (per-session and total)
- Automatic cleanup of old/expired sessions
- Warning logs when approaching limits

### Concurrency

- Thread-safe session access
- Multiple concurrent operations on same session
- Lock-free reads, locked writes (if needed)

### Data Transfer Optimization

Current (stateless):
- Full DataFrame: `O(rows * cols)` per request
- JSON serialization overhead

Proposed (stateful):
- Single value: `O(1)` per request
- Row slice: `O(slice_size * cols)` per request
- Column: `O(rows)` per request
- Filtered: `O(filtered_rows * cols)` per request

**Savings**: Typically 100-1000x reduction in data transfer for interactive workflows

## Use Cases

### Interactive Data Exploration

```python
# Load large dataset once
session = client.create_session('sales_data.yml')  # 1GB dataset

# Explore interactively (fast!)
stats = session.get_stats('revenue')
top_sellers = session.filter('revenue', '>', 100000).get_slice(0, 10)
unique_regions = session.get_unique('region')

session.delete()
```

### Data Quality Checks

```python
# Check data quality without transferring entire dataset
session = client.create_session('user_data.yml')

null_count = session.count_nulls('email')
duplicates = session.find_duplicates('user_id')
outliers = session.get_outliers('age', std_devs=3)

session.delete()
```

### Iterative Processing

```python
# Process data in chunks
session = client.create_session('large_file.yml')

total_rows = session.info()['shape'][0]
chunk_size = 1000

for start in range(0, total_rows, chunk_size):
    chunk = session.get_slice(start, start + chunk_size)
    process_chunk(chunk)

session.delete()
```

## API Design

### REST Endpoints

```
POST   /api/sessions                 Create session
GET    /api/sessions                 List all sessions
GET    /api/sessions/{id}            Get session info
DELETE /api/sessions/{id}            Delete session

POST   /api/sessions/{id}/get_value  Get single value
POST   /api/sessions/{id}/get_slice  Get row slice
POST   /api/sessions/{id}/get_column Get column
POST   /api/sessions/{id}/filter     Filter rows
POST   /api/sessions/{id}/sort       Sort data
POST   /api/sessions/{id}/stats      Get statistics
```

### Client API

```python
class Session:
    """Represents a stateful data session"""
    
    def __init__(self, client, session_id, metadata):
        ...
    
    def get_value(self, index, column) -> Any:
        """Get single value"""
    
    def get_slice(self, start, end, columns=None) -> pd.DataFrame:
        """Get row slice"""
    
    def get_column(self, column) -> pd.Series:
        """Get entire column"""
    
    def filter(self, column, operator, value) -> pd.DataFrame:
        """Filter rows"""
    
    def sort(self, column, ascending=True):
        """Sort data (in-place on server)"""
    
    def get_stats(self, column) -> Dict:
        """Get column statistics"""
    
    def get_unique(self, column) -> List:
        """Get unique values"""
    
    def info(self) -> Dict:
        """Get session metadata"""
    
    def delete(self):
        """Delete session"""

class ServerClient:
    def create_session(self, interface_file, session_name=None, timeout=3600):
        """Create new session"""
        # Returns Session object
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
    
    def get_session(self, session_id) -> Session:
        """Get existing session"""
    
    def delete_session(self, session_id):
        """Delete session"""
```

## Estimated Effort

- **Implementation**: 2-3 weeks
  - Session management: 1 week
  - Data operations: 1 week
  - Client API: 3-4 days
- **Testing**: 1 week
- **Documentation**: 3-4 days
- **Total**: 4-5 weeks

## Related

- **CIP**: [CIP-0008](../../cip/cip0008.md) - Server Mode implementation (Phase 5)
- **Requirement**: [REQ-0007](../../requirements/req0007_fast-repeated-access.md) - Fast repeated access
- **Previous Phase**: `2026-01-03_server-mode-phase3-robustness.md`

## Progress Updates

### 2026-01-03

Phase 5 backlog item created. Proposed stateful session architecture to reduce HTTP data transfer for interactive workflows.

Key innovation: Instead of transferring entire DataFrames, server maintains data in memory and clients send lightweight index/value operations.

