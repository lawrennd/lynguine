# Lynguine Server Mode - Phase 1 PoC

This directory contains the Proof of Concept for lynguine server mode (CIP-0008 Phase 1).

## Overview

Server mode keeps lynguine loaded in memory, avoiding startup costs for repeated operations. This is particularly beneficial for applications like `lamd` that call lynguine multiple times.

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
```

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

## Testing

Run the test suite:

```bash
pytest lynguine/tests/test_server_mode.py -v
```

Tests cover instance checking (singleton pattern), connectivity, data operations, error handling, and performance.

## Related Documentation

- [CIP-0008](../../cip/cip0008.md) - Full implementation plan
- [REQ-0007](../../requirements/req0007_fast-repeated-access.md) - Requirement
- [Backlog Item](../../backlog/infrastructure/2026-01-03_server-mode-phase1-poc.md) - Phase 1 task

