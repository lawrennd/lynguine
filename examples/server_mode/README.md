# Lynguine Server Mode - Examples

This directory contains examples and benchmarks for lynguine server mode (CIP-0008).

## Documentation

**📚 Complete documentation is available in Sphinx:**

https://lynguine.readthedocs.io/en/latest/server_mode/

- **Quick Start**: https://lynguine.readthedocs.io/en/latest/server_mode/quickstart.html
- **Migration Guide**: https://lynguine.readthedocs.io/en/latest/server_mode/migration.html
- **API Reference**: https://lynguine.readthedocs.io/en/latest/server_mode/api.html
- **Troubleshooting**: https://lynguine.readthedocs.io/en/latest/server_mode/troubleshooting.html
- **Examples**: https://lynguine.readthedocs.io/en/latest/server_mode/examples.html

## Overview

Server mode keeps lynguine loaded in memory, avoiding startup costs for repeated operations. This is particularly beneficial for applications like `lamd` that call lynguine multiple times via subprocesses.

**Phase 1-3 Performance**: 156.3x speedup for repeated operations (1.532s → 9.8ms)

**Phase 5 (New!)**: Stateful Data Sessions with crash recovery - mirrors `CustomDataFrame` API for 35-40x lamd improvement

## Quick Start

```bash
# Install dependencies
pip install requests
```

```python
from lynguine.client import ServerClient

# Zero-setup client (auto-starts server)
client = ServerClient(auto_start=True, idle_timeout=300)
df = client.read_data(interface_file='config.yml')
client.close()
```

**See the [Quick Start Guide](https://lynguine.readthedocs.io/en/latest/server_mode/quickstart.html) for complete instructions.**

## Phase 5: Stateful Data Sessions

```python
from lynguine.client import ServerClient

# Create client and session
client = ServerClient(auto_start=True)
session = client.create_session(interface_file='config.yml')

# Focus-based navigation (mirrors CustomDataFrame API)
session.set_index('person_1')
session.set_column('name')
value = session.get_value()  # Transfers ~bytes, not full DataFrame!

# Extract multiple fields (lamd mdfield pattern)
for field in ['name', 'email', 'affiliation']:
    session.set_column(field)
    print(f"{field}: {session.get_value()}")

session.delete()
```

**Key Benefits**:
- Mirrors `CustomDataFrame` API exactly
- Minimal HTTP traffic (~bytes per operation)
- 35-40x faster for lamd (72s → 2s for CV builds)
- Automatic crash recovery (sessions persist to disk)
- Multiple concurrent sessions

## Files in This Directory

- `test_config.yml` - Test configuration for benchmarking
- `benchmark.py` - Performance benchmark script  
- `benchmark_subprocess.py` - Realistic subprocess benchmark (simulates `lamd`)
- `example_phase5_sessions.py` - Phase 5 stateful sessions example
- `README.md` - This file

## Running Examples

```bash
# Phase 1-3: Basic server mode benchmarks
python examples/server_mode/benchmark.py
python examples/server_mode/benchmark_subprocess.py

# Phase 5: Stateful sessions example
python examples/server_mode/example_phase5_sessions.py
```

## Testing

```bash
# All server mode tests (60 tests: 44 Phase 1-3 + 16 Phase 5)
pytest lynguine/tests/test_server_mode.py -v

# Phase 1-3 tests
pytest lynguine/tests/test_server_mode.py::TestRetryLogic -v
pytest lynguine/tests/test_server_mode.py::TestIdleTimeout -v
pytest lynguine/tests/test_server_mode.py::TestAutoStart -v

# Phase 5 tests
pytest lynguine/tests/test_server_mode.py::TestPhase5Sessions -v
pytest lynguine/tests/test_server_mode.py::TestPhase5CrashRecovery -v
pytest lynguine/tests/test_server_mode.py::TestPhase5Integration -v
```

## Performance Results

**Phase 1-3 (Stateless)**:
- **156.3x speedup** for repeated calls (1.532s → 9.8ms)
- **HTTP overhead**: ~9.4ms (0.48% of original startup time)
- **First call**: ~2s (server startup)
- **Subsequent calls**: ~10ms each

**Phase 5 (Stateful Sessions)**:
- **35-40x improvement for lamd** (72s → 2s for CV builds)
- **Minimal HTTP traffic**: ~bytes per `get_value()` vs MB per DataFrame
- **Focus-based navigation**: set_index + set_column + get_value ≈ 10ms
- **Multiple field extraction**: 4 fields in ~40ms vs 7.6s (4 × 1.9s)
- **Crash recovery**: Sessions persist and auto-recover on server restart

## Documentation Links

- **📚 Sphinx Documentation**: https://lynguine.readthedocs.io/en/latest/server_mode/
- **Technical Specification**: [CIP-0008](../../cip/cip0008.md)
- **Requirements**: [REQ-0007](../../requirements/req0007_fast-repeated-access.md)
- **Backlog**: 
  - [Phase 1](../../backlog/infrastructure/2026-01-03_server-mode-phase1-poc.md) ✅ Completed
  - [Phase 2](../../backlog/infrastructure/2026-01-03_server-mode-phase2-core.md) ✅ Completed
  - [Phase 3](../../backlog/infrastructure/2026-01-03_server-mode-phase3-robustness.md) ✅ Completed
  - [Phase 5](../../backlog/infrastructure/2026-01-03_server-mode-phase5-stateful-sessions.md) ✅ Completed

