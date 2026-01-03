# Lynguine Server Mode - Phase 2

This directory contains examples and benchmarks for lynguine server mode (CIP-0008).

## Overview

Server mode keeps lynguine loaded in memory, avoiding startup costs for repeated operations. This is particularly beneficial for applications like `lamd` that call lynguine multiple times via subprocesses.

**Phase 1 (Complete)**: Proof of Concept - Basic server/client, instance checking, benchmarks
**Phase 2 (Complete)**: Core Features - New endpoints, idle timeout, auto-start, diagnostics

## Quick Start

### 1. Install dependencies

```bash
pip install requests
```

### 2. Start the server

```bash
# From the lynguine root directory
python -m lynguine.server

# Or with custom host/port
python -m lynguine.server --host 127.0.0.1 --port 8765

# With idle timeout (auto-shutdown after inactivity)
python -m lynguine.server --idle-timeout 300  # 5 minutes
```

**Note**: With auto-start (Phase 2), you can skip manual server startup - the client will start it automatically!

### 3. Run the benchmark

```bash
# In a new terminal
python examples/server_mode/benchmark.py

# Or with custom options
python examples/server_mode/benchmark.py --iterations 20
```

## Files

- `test_config.yml` - Test configuration for benchmarking
- `benchmark.py` - Performance benchmark script
- `README.md` - This file

## Expected Results

Based on profiling in CIP-0008:
- Baseline startup: ~1.947s (pandas 1.223s + lynguine 0.548s)
- Expected speedup: 10-20x for repeated operations
- Target speedup: >5x
- Target HTTP overhead: <5ms

## Usage from Python

### Basic Usage (Manual Server Start)

```python
from lynguine.client import ServerClient

# Connect to server
client = ServerClient('http://127.0.0.1:8765')

# Read data
df = client.read_data(
    interface_file='config.yml',
    directory='.'
)

# Close connection
client.close()
```

### Phase 2: Auto-Start (Recommended)

```python
from lynguine.client import ServerClient

# Client automatically starts server if not running
client = ServerClient(
    server_url='http://127.0.0.1:8765',
    auto_start=True,           # Enable auto-start
    idle_timeout=300           # Server auto-shuts down after 5min idle
)

# Read data - server starts automatically if needed
df = client.read_data(
    interface_file='config.yml',
    directory='.'
)

# Server remains running for other clients
client.close()
```

### Phase 2: New Endpoints

```python
# Health check
health = client.health_check()
print(health['status'])  # 'ok'

# Server diagnostics
status = requests.get('http://127.0.0.1:8765/api/status').json()
print(f"Uptime: {status['uptime_seconds']}s")
print(f"Memory: {status['memory']['rss_mb']}MB")
print(f"Idle timeout: {status['idle_timeout']}")
```

## Testing

Run the test suite:

```bash
# All tests
pytest lynguine/tests/test_server_mode.py -v

# Specific test classes
pytest lynguine/tests/test_server_mode.py::TestIdleTimeout -v
pytest lynguine/tests/test_server_mode.py::TestAutoStart -v
pytest lynguine/tests/test_server_mode.py::TestPhase2Endpoints -v
```

**Test Coverage**:
- **Phase 1**: Instance checking (singleton), connectivity, data operations, error handling, performance (24 tests)
- **Phase 2**: Idle timeout (4 tests), auto-start (4 tests), new endpoints (6 tests)
- **Total**: 38 tests, all passing ✅

## Phase 2 Features Summary

### Server Enhancements
- **Idle Timeout**: Auto-shutdown after configurable idle period
- **Server Diagnostics**: `/api/status` endpoint with uptime, memory, CPU, idle time
- **Write Data**: `/api/write_data` endpoint for writing DataFrames
- **Compute**: `/api/compute` endpoint (placeholder for compute framework)
- **Adaptive Check Interval**: Responsive shutdown for short timeouts

### Client Enhancements
- **Auto-Start**: Client can automatically start server if not running
- **Configurable Idle Timeout**: Set server idle timeout when auto-starting
- **Graceful Degradation**: Clear error messages when server unavailable

### Performance
- **156.3x speedup** vs. direct subprocess calls (1.532s → 9.8ms)
- **HTTP overhead**: ~9.4ms (0.48% of original startup time)

## Related Documentation

- [CIP-0008](../../cip/cip0008.md) - Full implementation plan
- [REQ-0007](../../requirements/req0007_fast-repeated-access.md) - Requirement
- [Phase 1 Backlog](../../backlog/infrastructure/2026-01-03_server-mode-phase1-poc.md) - Phase 1 PoC (Completed)
- [Phase 2 Backlog](../../backlog/infrastructure/2026-01-03_server-mode-phase2-core.md) - Phase 2 Core Features (In Progress)

