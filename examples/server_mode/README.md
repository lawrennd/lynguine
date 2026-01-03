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

**Performance**: 156.3x speedup for repeated operations (1.532s → 9.8ms)

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

## Files in This Directory

- `test_config.yml` - Test configuration for benchmarking
- `benchmark.py` - Performance benchmark script  
- `benchmark_subprocess.py` - Realistic subprocess benchmark (simulates `lamd`)
- `README.md` - This file

## Running Benchmarks

```bash
# Basic benchmark
python examples/server_mode/benchmark.py

# Subprocess benchmark (simulates lamd usage)
python examples/server_mode/benchmark_subprocess.py
```

## Testing

```bash
# All server mode tests (44 tests)
pytest lynguine/tests/test_server_mode.py -v

# Specific test classes
pytest lynguine/tests/test_server_mode.py::TestRetryLogic -v
pytest lynguine/tests/test_server_mode.py::TestIdleTimeout -v
pytest lynguine/tests/test_server_mode.py::TestAutoStart -v
```

## Performance Results

- **156.3x speedup** for repeated calls (1.532s → 9.8ms)
- **HTTP overhead**: ~9.4ms (0.48% of original startup time)
- **First call**: ~2s (server startup)
- **Subsequent calls**: ~10ms each

## Documentation Links

- **📚 Sphinx Documentation**: https://lynguine.readthedocs.io/en/latest/server_mode/
- **Technical Specification**: [CIP-0008](../../cip/cip0008.md)
- **Requirements**: [REQ-0007](../../requirements/req0007_fast-repeated-access.md)
- **Backlog**: [Phase 1](../../backlog/infrastructure/2026-01-03_server-mode-phase1-poc.md) | [Phase 2](../../backlog/infrastructure/2026-01-03_server-mode-phase2-core.md) | [Phase 3](../../backlog/infrastructure/2026-01-03_server-mode-phase3-robustness.md)

