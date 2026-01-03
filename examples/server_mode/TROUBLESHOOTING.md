# Troubleshooting Guide: Lynguine Server Mode

This guide helps you diagnose and fix common issues with lynguine server mode.

## Table of Contents

1. [Server Won't Start](#server-wont-start)
2. [Connection Refused Errors](#connection-refused-errors)
3. [Server Crashes or Stops Unexpectedly](#server-crashes-or-stops-unexpectedly)
4. [Slow Performance](#slow-performance)
5. [Memory Issues](#memory-issues)
6. [Auto-Start Not Working](#auto-start-not-working)
7. [Retry Logic Not Working](#retry-logic-not-working)
8. [Port Already in Use](#port-already-in-use)
9. [Data Inconsistencies](#data-inconsistencies)
10. [General Debugging Tips](#general-debugging-tips)

---

## Server Won't Start

### Symptom

```bash
$ python -m lynguine.server
ERROR: Port 8765 is already in use...
```

### Causes & Solutions

#### 1. Port Already in Use by Another Application

**Check what's using the port**:
```bash
# macOS/Linux
lsof -i :8765

# Or netstat
netstat -an | grep 8765
```

**Solutions**:
```bash
# Option A: Use a different port
python -m lynguine.server --port 8766

# Option B: Stop the other application
kill <PID>  # Use PID from lsof output

# Option C: Use client with matching port
from lynguine.client import ServerClient
client = ServerClient('http://127.0.0.1:8766')
```

####2. Lynguine Server Already Running

**Check if lynguine server is running**:
```bash
# Check for lockfile
ls /tmp/lynguine-server-*

# Try to connect
curl http://127.0.0.1:8765/api/health
```

**Solutions**:
```bash
# Option A: Use existing server
from lynguine.client import ServerClient
client = ServerClient('http://127.0.0.1:8765')

# Option B: Stop existing server
# Find the PID from lockfile
cat /tmp/lynguine-server-127-0-0-1-8765.lock
kill <PID>

# Then start new server
python -m lynguine.server
```

#### 3. Permission Denied

**Symptom**:
```
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# Don't use privileged ports (< 1024)
python -m lynguine.server --port 8765  # Good
python -m lynguine.server --port 80    # Bad (requires root)

# Check directory permissions
ls -la /tmp  # Should be writable for lockfiles
```

---

## Connection Refused Errors

### Symptom

```python
requests.exceptions.ConnectionError: Connection refused
```

### Causes & Solutions

#### 1. Server Not Running

**Check**:
```bash
curl http://127.0.0.1:8765/api/health
```

**Solutions**:
```python
# Option A: Start server manually
# Terminal 1: python -m lynguine.server

# Option B: Use auto-start
client = ServerClient(auto_start=True)
```

#### 2. Wrong URL or Port

**Check your configuration**:
```python
# Wrong
client = ServerClient('http://127.0.0.1:8764')

# Correct
client = ServerClient('http://127.0.0.1:8765')
```

#### 3. Firewall Blocking Connection

**Check firewall (macOS)**:
```bash
# Allow Python through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
```

---

## Server Crashes or Stops Unexpectedly

### Symptom

Server was running, now connection refused or "Server not available"

### Causes & Solutions

#### 1. Idle Timeout Triggered

**Check if idle timeout is configured**:
```bash
# Server shows this on startup if enabled:
# Idle timeout: 300s (5.0 minutes)
```

**Solutions**:
```bash
# Option A: Disable idle timeout
python -m lynguine.server --idle-timeout 0

# Option B: Increase idle timeout
python -m lynguine.server --idle-timeout 3600  # 1 hour

# Option C: Use auto-start (recommended)
client = ServerClient(auto_start=True, idle_timeout=300)
```

#### 2. Out of Memory

**Check server logs**:
```bash
# Look for OOM killer messages
dmesg | grep python

# Check memory usage
ps aux | grep lynguine.server
```

**Solutions**:
```python
# Use idle timeout to prevent memory buildup
python -m lynguine.server --idle-timeout 600

# Restart server periodically in production
```

#### 3. Uncaught Exception

**Check server logs**:
```bash
# Server logs to lynguine-server.log
tail -f lynguine-server.log
```

**Solutions**:
```python
# Use retry logic to auto-restart
client = ServerClient(
    auto_start=True,
    max_retries=3,
    retry_delay=1.0
)
```

---

## Slow Performance

### Symptom

Server mode not significantly faster than direct mode

### Causes & Solutions

#### 1. First Call is Always Slow

**This is expected**:
- First call: ~2s (server startup)
- Subsequent calls: ~10ms

**Verify**:
```python
import time
from lynguine.client import ServerClient

client = ServerClient(auto_start=True)

# First call (slow)
start = time.time()
df1 = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
print(f"First call: {time.time() - start:.3f}s")  # ~2s

# Subsequent calls (fast)
start = time.time()
df2 = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
print(f"Second call: {time.time() - start:.3f}s")  # ~0.01s

client.close()
```

#### 2. Network Overhead

**If using remote server**:
```python
# Check network latency
curl -w "@curl-format.txt" -o /dev/null -s http://server:8765/api/health
```

**Solutions**:
```python
# Use localhost for best performance
client = ServerClient('http://127.0.0.1:8765')  # Good
client = ServerClient('http://remote-server:8765')  # Slower
```

#### 3. Large Data Transfer

**HTTP overhead increases with data size**

**Solutions**:
```python
# For very large datasets, consider:
# 1. Data source directly on server
# 2. Streaming responses (Phase 4)
# 3. Direct mode for single large reads
```

---

## Memory Issues

### Symptom

Server using too much memory or growing over time

### Diagnosis

```bash
# Monitor server memory
ps aux | grep lynguine.server

# Or use top/htop
top -p <PID>
```

### Solutions

#### 1. Use Idle Timeout

```bash
python -m lynguine.server --idle-timeout 600  # 10 minutes
```

#### 2. Restart Periodically

```bash
# In production, use a process manager
# supervisord, systemd, etc.
```

#### 3. Monitor and Alert

```python
# Check server status
response = requests.get('http://127.0.0.1:8765/api/status')
memory_mb = response.json()['memory']['rss_mb']

if memory_mb > 1000:  # 1GB threshold
    # Alert or restart
    pass
```

---

## Auto-Start Not Working

### Symptom

```python
client = ServerClient(auto_start=True)
df = client.read_data(...)  # Fails, server doesn't start
```

### Causes & Solutions

#### 1. Python Not in PATH

**Check**:
```bash
which python
python --version
```

**Solutions**:
```bash
# Ensure python is in PATH
export PATH="/usr/local/bin:$PATH"

# Or use absolute path in client code (advanced)
```

#### 2. Wrong Python Environment

**Client starts server in different environment**

**Solutions**:
```python
# Ensure same environment for both client and server
# Use virtual env activation before running
source venv/bin/activate
python your_script.py
```

#### 3. Port Already in Use

**Auto-start fails if port is occupied**

**Check**:
```bash
lsof -i :8765
```

**Solutions**:
```python
# Use different port
client = ServerClient(
    server_url='http://127.0.0.1:8766',
    auto_start=True
)
```

---

## Retry Logic Not Working

### Symptom

Client fails immediately instead of retrying

### Causes & Solutions

#### 1. max_retries=0

**Check configuration**:
```python
client = ServerClient(max_retries=0)  # No retries!
```

**Solution**:
```python
client = ServerClient(max_retries=3)  # Enable retries
```

#### 2. 4xx Errors Don't Retry

**This is intentional** - client errors (4xx) indicate invalid requests

**Example**:
```python
# This will NOT retry (400 Bad Request)
client.read_data()  # Missing required params

# This WILL retry (server crash = connection error)
# Server crashes mid-request
```

#### 3. Check Retry Logs

**Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# You'll see retry attempts:
# WARNING lynguine.client read_data failed (attempt 1/4): Connection refused. Retrying in 1.0s...
```

---

## Port Already in Use

### Detailed Diagnosis

```bash
# Find what's using the port
sudo lsof -i :8765

# Or
netstat -tulpn | grep 8765

# Check lynguine lockfile
cat /tmp/lynguine-server-127-0-0-1-8765.lock
```

### Solutions

#### 1. Stop the Conflicting Process

```bash
# Kill by PID
kill <PID>

# Or kill all Python processes (careful!)
pkill -f "python.*lynguine.server"
```

#### 2. Use a Different Port

```bash
# Server
python -m lynguine.server --port 8766

# Client
from lynguine.client import ServerClient
client = ServerClient('http://127.0.0.1:8766')
```

#### 3. Clean Up Stale Lockfiles

```bash
# If server crashed and left lockfile
rm /tmp/lynguine-server-*

# Then start server
python -m lynguine.server
```

---

## Data Inconsistencies

### Symptom

Data returned by server mode differs from direct mode

### This Should Never Happen

Server mode should be **functionally identical** to direct mode.

### Diagnosis

```python
# Compare outputs
from lynguine.access import io
from lynguine.client import ServerClient

# Direct mode
df_direct = io.read('config.yml')

# Server mode
client = ServerClient(auto_start=True)
df_server = client.read_data(interface_file='config.yml')
client.close()

# Compare
assert df_direct.equals(df_server), "Data mismatch!"
```

### Report as Bug

If you find data inconsistencies, please report with:
1. Configuration file (if safe to share)
2. Direct mode output
3. Server mode output
4. Lynguine version
5. Steps to reproduce

---

## General Debugging Tips

### Enable Debug Logging

```python
import logging

# Client-side
logging.basicConfig(level=logging.DEBUG)

# Or just lynguine logs
logging.getLogger('lynguine').setLevel(logging.DEBUG)
```

### Check Server Logs

```bash
# Server logs to lynguine-server.log
tail -f lynguine-server.log

# Or run server in foreground
python -m lynguine.server
```

### Test Server Manually

```bash
# Health check
curl http://127.0.0.1:8765/api/health

# Ping
curl http://127.0.0.1:8765/api/ping

# Status (detailed)
curl http://127.0.0.1:8765/api/status | python -m json.tool
```

### Verify Versions

```python
import lynguine
import requests
import pandas

print(f"Lynguine: {lynguine.__version__}")
print(f"Requests: {requests.__version__}")
print(f"Pandas: {pandas.__version__}")
```

### Run Tests

```bash
# Verify your installation
pytest lynguine/tests/test_server_mode.py -v

# Run specific test class
pytest lynguine/tests/test_server_mode.py::TestRetryLogic -v
```

### Monitor Server Status

```python
import requests

response = requests.get('http://127.0.0.1:8765/api/status')
status = response.json()

print(f"Server: {status['server']} v{status['version']}")
print(f"PID: {status['pid']}")
print(f"Uptime: {status['uptime_seconds']:.0f}s")
print(f"Memory: {status['memory']['rss_mb']:.1f}MB")
print(f"CPU: {status['cpu_percent']:.1f}%")

if status['idle_timeout']['enabled']:
    remaining = status['idle_timeout']['remaining_seconds']
    print(f"Idle timeout: {remaining:.0f}s remaining")
```

---

## Still Having Issues?

1. **Check the migration guide**: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
2. **Review the README**: [README.md](./README.md)
3. **Check the CIP**: [CIP-0008](../../cip/cip0008.md)
4. **Run the tests**: `pytest lynguine/tests/test_server_mode.py -v`
5. **Check GitHub issues**: Look for similar problems
6. **File a bug report**: Include logs, config, and steps to reproduce

## Quick Reference: Common Commands

```bash
# Start server
python -m lynguine.server

# Start with options
python -m lynguine.server --port 8766 --idle-timeout 300

# Check if server is running
curl http://127.0.0.1:8765/api/health

# Find what's using a port
lsof -i :8765

# Kill server by PID
kill <PID>

# Clean up lockfiles
rm /tmp/lynguine-server-*

# Run tests
pytest lynguine/tests/test_server_mode.py -v

# Watch server logs
tail -f lynguine-server.log
```

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| Port in use | `python -m lynguine.server --port 8766` |
| Server not starting | `rm /tmp/lynguine-server-* && python -m lynguine.server` |
| Connection refused | `client = ServerClient(auto_start=True)` |
| Slow first call | Expected - subsequent calls are fast |
| Memory growing | `python -m lynguine.server --idle-timeout 600` |
| Auto-start failing | Check `which python` and environment |
| Retries not working | `client = ServerClient(max_retries=3)` |
| Data mismatch | Report as bug - should never happen |

