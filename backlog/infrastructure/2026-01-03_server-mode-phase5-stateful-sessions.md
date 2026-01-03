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

Based on lynguine's existing `DataObject` API (which lamd's `mdfield`/`mdlist` tools use):

**Navigation & Focus**:
- **set_index(index)**: Set current row focus
- **set_column(column)**: Set current column focus
- **get_index()**: Get current row focus
- **get_column()**: Get current column focus

**Data Access** (at current focus):
- **get_value()**: Get value at current (index, column) focus
- **set_value(value)**: Set value at current focus
- **get_value_at(index, column)**: Get specific value without changing focus

**Bulk Operations**:
- **get_slice(start, end, columns)**: Get row slice
- **get_column_data(column)**: Get entire column as list
- **get_row_data(index)**: Get entire row as dict
- **filter(column, operator, value)**: Filter rows
- **get_shape()**: Get (rows, cols) dimensions

**Series Operations** (for series columns):
- **set_selector(column)**: Set selector column for series
- **set_subindex(value)**: Set subindex within series
- **get_subseries()**: Get subseries data

**Metadata**:
- **get_columns()**: Get list of all columns
- **get_indices()**: Get list of all indices
- **get_info()**: Session info (shape, memory, columns, etc.)

### Client API

**Pattern 1: Focus-based access (mirrors `DataObject` API, for `mdfield`-style usage)**:

```python
from lynguine.client import ServerClient

client = ServerClient(auto_start=True)

# Create session (loads interface file once)
session = client.create_session(interface_file='cv_config.yml')

# Navigate to specific value (like mdfield does)
session.set_index('person_1')
session.set_column('name')
value = session.get_value()  # Returns just the value, ~bytes over HTTP
print(value)  # "Neil Lawrence"

# Or use convenience method
value = session.get_value_at(index='person_1', column='email')

# Cleanup
session.delete()
```

**Pattern 2: Bulk operations (for data exploration)**:

```python
# Create session
session = client.create_session(interface_file='large_data.yml')

# Get slices
slice_df = session.get_slice(start=0, end=100)  # Only slice transfers
filtered = session.filter(column='age', operator='>', value=30)

# Get column
ages = session.get_column_data('age')  # Just the column, not whole DataFrame

# Session info
info = session.get_info()
print(f"Shape: {info['shape']}, Memory: {info['memory_mb']}MB")

# Cleanup
session.delete()
```

**Pattern 3: Series navigation (for complex data)**:

```python
# For series columns (lists within cells)
session.set_index('person_1')
session.set_column('publications')  # This is a series column
session.set_selector('year')
session.set_subindex(2023)
pub_2023 = session.get_value()  # Gets 2023 publication for person_1
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

### 1. lamd's `mdfield` Tool (Primary Use Case)

**Current (stateless)**: Every field extraction pays full startup + transfers entire DataFrame

```python
# Each mdfield call (38 times per CV build):
# 1. Start Python process (1.9s startup)
# 2. Import lynguine
# 3. Read interface file → full DataFrame
# 4. Extract one field
# 5. Exit

# Result: 72s startup overhead + unnecessary data transfer
```

**With Phase 5 (stateful)**: Load once, extract fields via focus-based API

```python
from lynguine.client import ServerClient

client = ServerClient(auto_start=True)

# Create session once (loads CV config)
session = client.create_session(interface_file='neil-lawrence.yml')

# Extract 27 fields (like mdfield does) - minimal transfer per field
fields = {}
for field in ['name', 'email', 'affiliation', 'title', 'phone', ...]:
    session.set_column(field)
    fields[field] = session.get_value()  # Transfer: ~bytes per field

# Result: 1.9s startup + minimal transfer (27 × ~bytes instead of 27 × full DataFrame)
```

**Savings for lamd**:
- **Before**: 38 calls × (1.9s startup + DataFrame transfer) = 72s + data overhead
- **After**: 1 session + 38 lightweight operations = 1.9s + ~bytes
- **Improvement**: ~35-40x faster

### 2. lamd's `mdlist` Tool

```python
# Generate publication list from multiple markdown files
session = client.create_session(interface_file='publications.yml')

# Get filtered slice
session.set_column('year')
pubs_2023 = session.filter(column='year', operator='==', value=2023)

# Get specific fields from slice
pub_list = []
for idx in range(len(pubs_2023)):
    session.set_index(idx)
    pub_list.append({
        'title': session.get_value_at(idx, 'title'),
        'venue': session.get_value_at(idx, 'venue'),
        'authors': session.get_value_at(idx, 'authors')
    })
```

### 3. Interactive Data Exploration

```python
# Load large dataset once
session = client.create_session('sales_data.yml')  # 1GB dataset

# Navigate interactively (minimal transfer)
session.set_index(0)
session.set_column('revenue')
first_revenue = session.get_value()  # ~bytes

# Get slice
top_10 = session.get_slice(start=0, end=10)  # Only 10 rows transfer

session.delete()
```

### 4. Data Quality Checks

```python
# Check data quality without transferring entire dataset
session = client.create_session('user_data.yml')

# Get column for analysis
emails = session.get_column_data('email')  # Just one column
null_count = sum(1 for e in emails if e is None)

session.delete()
```

### 5. Iterative Processing

```python
# Process data in chunks
session = client.create_session('large_file.yml')

shape = session.get_shape()
total_rows = shape[0]
chunk_size = 1000

for start in range(0, total_rows, chunk_size):
    chunk = session.get_slice(start, start + chunk_size)
    process_chunk(chunk)

session.delete()
```

## API Design

### REST Endpoints

**Session Management**:
```
POST   /api/sessions                  Create session
GET    /api/sessions                  List all sessions
GET    /api/sessions/{id}             Get session info
DELETE /api/sessions/{id}             Delete session
```

**Focus Operations** (mirrors DataObject API):
```
POST   /api/sessions/{id}/set_index    Set current row focus
POST   /api/sessions/{id}/set_column   Set current column focus
GET    /api/sessions/{id}/get_index    Get current row focus
GET    /api/sessions/{id}/get_column   Get current column focus
GET    /api/sessions/{id}/get_value    Get value at current focus
POST   /api/sessions/{id}/set_value    Set value at current focus
```

**Bulk Operations**:
```
POST   /api/sessions/{id}/get_value_at    Get specific value (index, column)
POST   /api/sessions/{id}/get_slice       Get row slice
POST   /api/sessions/{id}/get_column_data Get entire column
POST   /api/sessions/{id}/get_row_data    Get entire row
POST   /api/sessions/{id}/filter          Filter rows
GET    /api/sessions/{id}/get_shape       Get dimensions
```

**Series Operations**:
```
POST   /api/sessions/{id}/set_selector   Set selector for series
POST   /api/sessions/{id}/set_subindex   Set subindex for series
GET    /api/sessions/{id}/get_subseries  Get subseries data
```

**Metadata**:
```
GET    /api/sessions/{id}/get_columns    Get all column names
GET    /api/sessions/{id}/get_indices    Get all index values
GET    /api/sessions/{id}/get_info       Get session metadata
```

### Client API

```python
class Session:
    """Represents a stateful data session (mirrors DataObject API)"""
    
    def __init__(self, client, session_id, metadata):
        ...
    
    # Focus-based navigation (like DataObject)
    def set_index(self, index) -> None:
        """Set current row focus"""
    
    def set_column(self, column) -> None:
        """Set current column focus"""
    
    def get_index(self) -> Any:
        """Get current row focus"""
    
    def get_column(self) -> str:
        """Get current column focus"""
    
    # Data access at current focus
    def get_value(self) -> Any:
        """Get value at current (index, column) focus"""
    
    def set_value(self, value) -> None:
        """Set value at current focus"""
    
    # Convenience methods
    def get_value_at(self, index, column) -> Any:
        """Get specific value without changing focus"""
    
    # Bulk operations
    def get_slice(self, start, end, columns=None) -> pd.DataFrame:
        """Get row slice"""
    
    def get_column_data(self, column) -> List:
        """Get entire column as list"""
    
    def get_row_data(self, index) -> Dict:
        """Get entire row as dict"""
    
    def filter(self, column, operator, value) -> pd.DataFrame:
        """Filter rows"""
    
    def get_shape(self) -> Tuple[int, int]:
        """Get (rows, cols) dimensions"""
    
    # Series operations
    def set_selector(self, column) -> None:
        """Set selector column for series"""
    
    def set_subindex(self, value) -> None:
        """Set subindex within series"""
    
    def get_subseries(self) -> pd.DataFrame:
        """Get subseries data"""
    
    # Metadata
    def get_columns(self) -> List[str]:
        """Get all column names"""
    
    def get_indices(self) -> List[Any]:
        """Get all index values"""
    
    def get_info(self) -> Dict:
        """Get session metadata (shape, memory, columns, etc.)"""
    
    def delete(self):
        """Delete session"""

class ServerClient:
    def create_session(
        self, 
        interface_file: str,
        directory: str = '.',
        interface_field: Optional[str] = None,
        session_name: Optional[str] = None,
        timeout: int = 3600
    ) -> Session:
        """Create new session by loading interface file"""
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
    
    def get_session(self, session_id: str) -> Session:
        """Get existing session"""
    
    def delete_session(self, session_id: str):
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

