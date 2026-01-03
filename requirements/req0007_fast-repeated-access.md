---
id: "REQ-0007"
title: "Fast Repeated Access to Lynguine Functionality"
created: "2026-01-03"
last_updated: "2026-01-03"
status: "In Progress"
priority: "High"
owner: "lawrennd"
stakeholders: "lamd developers (primary), CLI tool developers"
related_tenets:
- explicit-infrastructure
- flow-based-processing
tags:
- requirement
- performance
- architecture
- startup-time
---

# Requirement: Fast Repeated Access to Lynguine Functionality

## Description

Applications that need to access lynguine functionality multiple times in quick succession (e.g., lamd accessing multiple files, CLI tools processing batches) currently suffer from slow startup costs on each invocation. The system needs a way to provide fast, repeated access to lynguine's data loading and processing capabilities without re-initializing the entire infrastructure each time.

**Problem**: 
- Lynguine has significant startup overhead (imports, initialization)
- Applications like lamd call lynguine multiple times for file access
- Each call pays the full startup cost
- Total execution time = (startup cost × number of calls) + actual work
- This makes lynguine impractical for CLI tools and batch processing

**Desired Outcome**:
- Fast repeated access to lynguine functionality
- Startup overhead amortized across multiple operations
- Maintains lynguine's explicitness and predictability
- Works seamlessly with existing application patterns
- No breaking changes to current API

## Applicability: When This Requirement Applies

### ✅ Applications That Need This (Subprocess Pattern)

**Pattern**: Applications that make **repeated subprocess calls** to lynguine functionality

**Characteristics**:
- Multiple independent process launches from shell/make/scripts
- Each call: start Python → import lynguine → execute → exit
- Short-lived processes with no state persistence
- Startup overhead dominates execution time

**Concrete Examples**:
1. **lamd (primary use case)** - Investigated 2026-01-03:
   - Builds CVs using make with 38+ subprocess calls per build
   - Each `mdfield` call: new process to extract one field from config
   - Each `mdlist` call: new process to generate one markdown list
   - **Current cost**: ~72 seconds startup overhead per CV build
   - **Impact**: 95% of execution time is startup overhead

2. **CLI batch processing**:
   - Scripts processing multiple files with separate lynguine calls
   - Automated workflows with repeated configuration access

3. **CI/CD pipelines**:
   - Multiple validation steps each importing lynguine

### ❌ Applications That Don't Need This (Long-Running Pattern)

**Pattern**: Applications with **long-running Python processes** that already amortize startup

**Characteristics**:
- Single Python process that stays loaded
- Imports done once at process start
- Modules cached in memory for entire session
- Startup cost already amortized

**Examples**:
1. **referia (Jupyter notebooks)**:
   - Jupyter kernel runs continuously during session
   - Startup paid once when kernel starts
   - pandas/lynguine stay loaded and cached
   - **Does NOT need this requirement** - already fast
   - If slow: Different causes (I/O, data processing, not startup)

2. **Web applications**: Django/Flask apps with process pools

3. **Long-running Python scripts**: Single script with internal loops

### Investigation Results (2026-01-03)

**lamd analysis**:
- 27 `mdfield` calls per typical CV build (field extraction)
- 11 `mdlist` calls per typical CV build (list generation)
- **Total**: 38 subprocess calls × 1.9s startup = 72s overhead
- Actual work: ~5s
- **Startup represents 93% of total time**

**Conclusion**: This requirement specifically addresses the subprocess pattern. Long-running applications like referia do not have this problem and should continue using direct imports.

## Acceptance Criteria

### Phase 1-3: Basic Server Mode
- [ ] Repeated lynguine operations are significantly faster than current approach
- [ ] Startup overhead amortized across multiple calls
- [ ] Compatible with existing lynguine API (no breaking changes)
- [ ] Works for both programmatic access (lamd) and CLI usage
- [ ] Maintains data isolation between operations (no state leakage)
- [ ] Clear error messages and failure modes
- [ ] Memory usage remains reasonable with long-running processes
- [ ] Graceful shutdown and cleanup
- [ ] Performance metrics documented (startup time, operation time, memory)

### Phase 5: Stateful Sessions (Advanced Use Case - Mirrors CustomDataFrame API)

**Session Management**:
- [ ] Server can load interface files and maintain CustomDataFrame state in memory
- [ ] Create, list, retrieve, and delete sessions
- [ ] Session isolation (multiple clients, separate sessions)
- [ ] Session timeout and automatic cleanup
- [ ] Memory limits and monitoring per session

**Focus-Based Navigation** (mirrors `CustomDataFrame` API):
- [ ] `set_index(index)` - Set current row focus
- [ ] `set_column(column)` - Set current column focus
- [ ] `get_index()` - Get current row focus
- [ ] `get_column()` - Get current column focus
- [ ] `get_value()` - Get value at current (index, column) focus
- [ ] `set_value(value)` - Set value at current focus

**Bulk Operations**:
- [ ] `get_value_at(index, column)` - Direct value access without changing focus
- [ ] `get_slice(start, end, columns)` - Get row slice
- [ ] `get_column_data(column)` - Get entire column as list
- [ ] `get_row_data(index)` - Get entire row as dict
- [ ] `filter(column, operator, value)` - Server-side filtering
- [ ] `get_shape()` - Get (rows, cols) dimensions

**Series Operations** (for complex data):
- [ ] `set_selector(column)` - Set selector column for series
- [ ] `set_subindex(value)` - Set subindex within series
- [ ] `get_subseries()` - Get subseries data

**Metadata**:
- [ ] `get_columns()` - Get all column names
- [ ] `get_indices()` - Get all index values
- [ ] `get_input_columns()`, `get_output_columns()`, `get_series_columns()` - Get typed columns
- [ ] `get_column_type(column)` - Get column specification type

**Performance**:
- [ ] Only indices and values transfer over HTTP, not full DataFrames
- [ ] 100-1000x reduction in data transfer for interactive workflows
- [ ] 35-40x improvement for lamd's field extraction pattern

## User Stories

### Subprocess Pattern (Primary Use Case)

**As a lamd maintainer**, I want to reduce CV build times from 72s to <5s so that users don't wait unnecessarily for repeated subprocess calls to complete.

**As a make/shell workflow author**, I want to call lynguine utilities (like `mdfield`) multiple times without paying 1.9s startup per call so that my workflows are practical.

**As a CLI tool developer**, I want to process batches of files by calling lynguine for each file without prohibitive startup costs so that my tool scales to large datasets.

**As a CI/CD pipeline author**, I want to run multiple lynguine validation steps quickly so that my pipeline completes in reasonable time.

### General

**As an application developer**, I want backward compatibility so that I can adopt the fast-access mode incrementally without rewriting existing code.

**As a user**, I want predictable performance so that I can estimate how long operations will take.

### Stateful Sessions (Advanced Use Case - Focus-Based Navigation)

**As a lamd developer**, I want to use focus-based navigation (`set_index`, `set_column`, `get_value`) to extract fields from CV configs so that I don't transfer the entire DataFrame 38 times per build (reducing 72s to 2s).

**As an mdfield tool user**, I want the server to load my interface file once and let me navigate to specific (index, column) positions to extract individual values so that each field extraction takes ~10ms instead of 1.9s.

**As an mdlist tool user**, I want to use server-side filtering and slicing to generate publication lists without transferring all publications over HTTP so that list generation is fast even for large datasets.

**As a data analyst**, I want to navigate through datasets using `set_index`/`set_column`/`get_value` just like I do with `CustomDataFrame` locally so that remote data exploration feels identical to local exploration.

**As a data quality engineer**, I want to check data quality by navigating to specific cells and columns without transferring full datasets so that validation is fast and bandwidth-efficient.

**As a developer using series columns**, I want to use `set_selector` and `set_subindex` to navigate complex nested data structures so that I can extract specific subseries values without transferring entire series.

### Non-Use Cases (for clarity)

**As a referia user (Jupyter)**, I do NOT need this optimization because my kernel stays loaded and startup is already amortized.

**As a web app developer**, I do NOT need this optimization because my application server keeps modules loaded.

## Constraints

- Must maintain lynguine's explicitness (no hidden state)
- Must ensure data isolation between operations
- Must work within lynguine's flow-based processing model
- Must not break existing applications (referia, lamd)
- Should work on all platforms (Unix, Windows)
- Must handle process crashes gracefully
- Must have reasonable memory footprint

## Implementation Notes

### What a CIP Should Address

A CIP addressing this requirement should include:

1. **Investigation and Analysis**:
   - Performance profiling to identify bottlenecks
   - Usage pattern analysis (how lamd and other applications use lynguine)
   - Baseline performance benchmarks
   - Import cost analysis

2. **Solution Design**:
   - Proposed architectural approach(es)
   - Trade-offs between options
   - Performance improvement estimates
   - Compatibility considerations

3. **Implementation Plan**:
   - Phased approach if needed
   - Backward compatibility strategy
   - Testing and validation approach

### Phase 5: Mirroring CustomDataFrame Interface

**Design Principle**: Phase 5 stateful sessions must mirror lynguine's existing `CustomDataFrame` interface to ensure:

1. **API Consistency**:
   - Server sessions expose the same methods as `CustomDataFrame`
   - `set_index()`, `set_column()`, `get_value()` work identically
   - Series operations (`set_selector`, `set_subindex`) preserved
   - Column type queries (`get_input_columns`, `get_series_columns`) available

2. **Minimal Learning Curve**:
   - lamd's `mdfield`/`mdlist` already use `CustomDataFrame` API
   - No API translation needed for integration
   - Developers familiar with `CustomDataFrame` can immediately use sessions

3. **Implementation Approach**:
   - Server maintains `CustomDataFrame` instances (created via `from_flow()`)
   - Session operations delegate to underlying `CustomDataFrame` methods
   - HTTP/REST endpoints wrap `CustomDataFrame` API
   - Focus state (current index, column, selector, subindex) maintained per session

**Example - Local vs Remote**:

```python
# Local (current)
from lynguine.config.interface import Interface
from lynguine.assess.data import CustomDataFrame

interface = Interface.from_file('cv_config.yml', directory='.')
cdf = CustomDataFrame.from_flow(interface)
cdf.set_index('person_1')
cdf.set_column('name')
value = cdf.get_value()

# Remote (Phase 5) - Same API via session
from lynguine.client import ServerClient

client = ServerClient(auto_start=True)
session = client.create_session(interface_file='cv_config.yml', directory='.')
session.set_index('person_1')
session.set_column('name')
value = session.get_value()  # Same method, transfers ~bytes over HTTP
```

**Key Methods to Mirror** (from `CustomDataFrame`):
- Focus navigation: `set_index()`, `get_index()`, `set_column()`, `get_column()`
- Data access: `get_value()`, `set_value()`
- Series operations: `set_selector()`, `get_selector()`, `set_subindex()`, `get_subindex()`, `get_subseries()`
- Metadata: `get_shape()`, `get_columns()`, `get_indices()`
- Column types: `get_input_columns()`, `get_output_columns()`, `get_series_columns()`, `get_column_type()`

### Tenet Alignment

**Explicit Infrastructure**:
- Any solution must make data flows explicit
- No hidden state or magic caching
- Clear lifecycle management

**Flow-Based Processing**:
- Maintain access-assess-address pattern
- Fast access shouldn't bypass flow processing
- Explicit data transformations

## Related

- CIP: [CIP-0008](../cip/cip0008.md) - Lynguine Server Mode for Fast Repeated Access
  - Investigation complete (profiling, benchmarking)
  - Architecture: HTTP/REST server mode
  - Performance validated: 10-20x improvement
  - Cross-platform: Unix, macOS, Windows
- Backlog: [2026-01-03_profile-lynguine-startup-performance](../backlog/infrastructure/2026-01-03_profile-lynguine-startup-performance.md) (Completed)
- Tenets:
  - `explicit-infrastructure`: Solution must maintain explicit behavior
  - `flow-based-processing`: Must work within flow-based processing model

## Implementation Status

- [x] Not Started
- [x] In Progress (CIP-0008 investigation complete, ready for implementation decision)
- [ ] Implemented
- [ ] Validated

## Progress Updates

### 2026-01-03 - Initial Creation

Requirement created based on lamd performance issues.

### 2026-01-03 - Investigation Complete

**CIP-0008 created** with comprehensive investigation:

**Profiling Results**:
- Startup time: 1.947s (pandas 1.223s, lynguine 0.548s)
- Memory overhead: 117 MB (pandas/numpy)
- Current performance: 100 ops = 200 seconds (95% overhead)
- Target performance: 100 ops = 12 seconds (10-20x improvement)

**Architectural Decision**:
- HTTP/REST server mode (not Unix sockets)
- Cross-platform: Works on Unix, macOS, Windows
- Remote access capability: Local-only default, authenticated remote optional
- Backward compatible: Transparent fallback to direct mode

**Status**: CIP-0008 ready for implementation decision.

**Acceptance Criteria Status** (verified against CIP-0008):
- ✅ Significantly faster: 10-20x improvement validated
- ✅ Startup overhead amortized: Server mode design
- ✅ Backward compatible: Transparent client API
- ✅ Programmatic + CLI: Both supported
- ✅ Data isolation: Stateless server design
- ✅ Error handling: Comprehensive strategy
- ✅ Memory reasonable: 132 MB measured
- ✅ Graceful shutdown: Idle timeout, health checks
- ✅ Performance documented: Full profiling in CIP
- ✅ Cross-platform: HTTP works on all platforms

**All acceptance criteria addressed by CIP-0008.**

### 2026-01-03 - lamd Investigation and Applicability Clarification

**lamd Use Case Analysis**:
- Analyzed actual lamd usage pattern: 38 subprocess calls per CV build
- 27 `mdfield` calls (field extraction) + 11 `mdlist` calls (list generation)
- Each call: new Python process → import lynguine → execute → exit
- Measured: 1.9s startup × 38 calls = 72s overhead per build
- Actual work: ~5s
- **Startup represents 93% of total execution time**

**Applicability Refinement**:
Added clear distinction between two patterns:

1. **✅ Subprocess Pattern** (NEEDS this optimization):
   - lamd (primary use case): Multiple make/shell calls
   - CLI batch tools
   - CI/CD pipelines with multiple steps
   - **Problem**: Repeated startup overhead

2. **❌ Long-Running Pattern** (does NOT need this):
   - referia (Jupyter notebooks): Single kernel stays loaded
   - Web applications: Process pools keep modules loaded
   - Long Python scripts: Single process with internal loops
   - **No problem**: Startup already amortized

**User Stories Updated**: More specific to subprocess pattern; added non-use case examples

**Stakeholders Updated**: "lamd developers (primary)" reflecting main use case

**Status Updated**: Proposed → In Progress (PoC validated)

### 2026-01-03 - Phase 1 PoC Complete

**Implementation**:
- ✅ HTTP/REST server (lynguine/server.py)
- ✅ Client library (lynguine/client.py)
- ✅ Instance checking (singleton with lockfiles)
- ✅ Comprehensive tests (23 tests covering all aspects)
- ✅ Example configurations and benchmarks

**Performance Results** (realistic subprocess benchmark):
- Subprocess mode: 1.476s per operation (cold start each time)
- Server mode: 0.009s per operation (server stays loaded)
- **Speedup: 156x** (far exceeds 5x target)
- HTTP overhead: 9.4ms (acceptable vs 1476ms startup)

**Decision**: ✅ **GO for Phase 2** - Core Features

**Next Steps**:
- Phase 2: Additional endpoints, enhanced error handling
- Integration examples for lamd (mdfield/mdlist wrappers)
- Cross-platform testing (Windows, Linux)

