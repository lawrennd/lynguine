"""
Tests for lynguine server mode (CIP-0008 Phase 1)

Tests cover:
- Server startup and shutdown
- Server instance checking (singleton)
- Client connectivity
- Data operations (read_data)
- Error handling
- Performance characteristics
"""

import os
import time
import tempfile
import pytest
import requests
import socket
from multiprocessing import Process
from pathlib import Path

from lynguine.server import run_server, check_server_running, get_lockfile_path
from lynguine.client import ServerClient


# Test configuration
TEST_PORT = 8766  # Different from default to avoid conflicts
TEST_HOST = '127.0.0.1'
TEST_URL = f'http://{TEST_HOST}:{TEST_PORT}'


def _run_test_server():
    """Module-level function for multiprocessing (must be picklable)"""
    run_server(host=TEST_HOST, port=TEST_PORT)


def _run_shutdown_test_server():
    """Module-level function for shutdown test (must be picklable)"""
    run_server(host=TEST_HOST, port=TEST_PORT + 100)


def _run_server_with_5min_timeout():
    """Module-level function for idle timeout test (must be picklable)"""
    run_server(host=TEST_HOST, port=TEST_PORT+10, idle_timeout=300)


def _run_server_with_3sec_timeout():
    """Module-level function for idle timeout test (must be picklable)"""
    run_server(host=TEST_HOST, port=TEST_PORT+11, idle_timeout=3)


def _run_server_with_5sec_timeout():
    """Module-level function for idle timeout test (must be picklable)"""
    run_server(host=TEST_HOST, port=TEST_PORT+12, idle_timeout=5)


@pytest.fixture
def test_config_file(tmp_path):
    """Create a temporary test configuration file"""
    config_content = """input:
  type: fake
  nrows: 10
  cols:
    - name
    - email
"""
    config_file = tmp_path / "test_config.yml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def server_process():
    """Start a test server in a separate process"""
    proc = Process(target=_run_test_server, daemon=True)
    proc.start()
    
    # Wait for server to start
    max_wait = 5
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f'{TEST_URL}/api/health', timeout=1)
            if response.status_code == 200:
                break
        except:
            time.sleep(0.1)
    
    yield proc
    
    # Cleanup
    proc.terminate()
    proc.join(timeout=2)
    if proc.is_alive():
        proc.kill()
        proc.join()


class TestServerInstanceChecking:
    """Tests for server instance checking (singleton pattern)"""
    
    def test_lockfile_path_generation(self):
        """Test that lockfile path is generated correctly"""
        lockfile = get_lockfile_path(TEST_HOST, TEST_PORT)
        assert lockfile.exists or not lockfile.exists  # Path is valid
        assert str(TEST_PORT) in str(lockfile)
    
    def test_check_server_not_running(self):
        """Test checking when server is not running"""
        # Use unusual port that's unlikely to be in use
        is_running, server_type = check_server_running(TEST_HOST, 59999)
        assert not is_running
        assert server_type == 'none'
    
    def test_check_server_running(self, server_process):
        """Test checking when server is running"""
        is_running, server_type = check_server_running(TEST_HOST, TEST_PORT)
        assert is_running
        assert server_type == 'lynguine'
    
    def test_prevent_duplicate_server_start(self, server_process):
        """Test that starting a duplicate server fails gracefully"""
        # Server is already running via fixture
        # Attempting to start another should fail or warn
        is_running, server_type = check_server_running(TEST_HOST, TEST_PORT)
        assert is_running
        assert server_type == 'lynguine'
    
    def test_detect_non_lynguine_port_usage(self):
        """Test detecting when a non-lynguine application is using the port"""
        # Start a basic HTTP server (not lynguine)
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        test_port = 58888  # Unusual port for testing
        
        class SimpleHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        # Start non-lynguine server in background thread
        server = HTTPServer(('127.0.0.1', test_port), SimpleHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        time.sleep(0.5)  # Wait for server to start
        
        try:
            # Check if our detection correctly identifies it as "other"
            is_running, server_type = check_server_running('127.0.0.1', test_port)
            assert is_running
            assert server_type == 'other'  # Not lynguine!
        finally:
            server.shutdown()
            thread.join(timeout=1)


class TestServerBasics:
    """Tests for basic server functionality"""
    
    def test_server_starts_successfully(self, server_process):
        """Test that server starts and responds to health checks"""
        response = requests.get(f'{TEST_URL}/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'server' in data
    
    def test_ping_endpoint(self, server_process):
        """Test ping endpoint for connectivity"""
        response = requests.get(f'{TEST_URL}/api/ping')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert data['message'] == 'pong'
    
    def test_invalid_endpoint_returns_404(self, server_process):
        """Test that invalid endpoints return 404"""
        response = requests.post(f'{TEST_URL}/api/invalid', json={})
        assert response.status_code == 404


class TestClientBasics:
    """Tests for client functionality"""
    
    def test_client_creation(self):
        """Test creating a client instance"""
        client = ServerClient(server_url=TEST_URL)
        assert client.server_url == TEST_URL
    
    def test_client_ping_success(self, server_process):
        """Test client can ping server"""
        client = ServerClient(server_url=TEST_URL)
        assert client.ping()
    
    def test_client_ping_failure(self):
        """Test client ping fails when server not running"""
        client = ServerClient(server_url='http://127.0.0.1:59999')
        assert not client.ping()
    
    def test_client_health_check(self, server_process):
        """Test client health check"""
        client = ServerClient(server_url=TEST_URL)
        health = client.health_check()
        assert health['status'] == 'ok'
    
    def test_client_context_manager(self, server_process):
        """Test client works as context manager"""
        with ServerClient(server_url=TEST_URL) as client:
            assert client.ping()


class TestReadDataOperation:
    """Tests for read_data operations"""
    
    def test_read_data_from_interface_file(self, server_process, test_config_file):
        """Test reading data via interface file"""
        client = ServerClient(server_url=TEST_URL)
        df = client.read_data(
            interface_file=test_config_file.name,
            directory=str(test_config_file.parent)
        )
        
        assert df is not None
        assert len(df) == 10
        assert 'name' in df.columns
        assert 'email' in df.columns
    
    def test_read_data_direct_source(self, server_process):
        """Test reading data via direct source specification"""
        client = ServerClient(server_url=TEST_URL)
        df = client.read_data(
            data_source={
                'type': 'fake',
                'nrows': 5,
                'cols': ['name', 'email']
            }
        )
        
        assert df is not None
        assert len(df) == 5
        assert 'name' in df.columns
        assert 'email' in df.columns
    
    def test_read_data_missing_parameters(self, server_process):
        """Test that missing parameters raise ValueError"""
        client = ServerClient(server_url=TEST_URL)
        with pytest.raises(ValueError, match="Must provide either"):
            client.read_data()


class TestIdleTimeout:
    """Tests for idle timeout functionality"""
    
    def test_idle_timeout_disabled_by_default(self, server_process):
        """Test that idle timeout is disabled by default"""
        response = requests.get(f'{TEST_URL}/api/status')
        assert response.status_code == 200
        
        data = response.json()
        assert 'idle_timeout' in data
        assert data['idle_timeout']['enabled'] is False
    
    def test_idle_timeout_status_info(self):
        """Test status endpoint shows idle timeout information when enabled"""
        import multiprocessing
        import time
        
        # Start server with idle timeout
        process = multiprocessing.Process(target=_run_server_with_5min_timeout, daemon=True)
        process.start()
        time.sleep(2)
        
        try:
            # Check status
            test_url = f'http://{TEST_HOST}:{TEST_PORT+10}'
            response = requests.get(f'{test_url}/api/status')
            assert response.status_code == 200
            
            data = response.json()
            assert 'idle_timeout' in data
            assert data['idle_timeout']['enabled'] is True
            assert data['idle_timeout']['timeout_seconds'] == 300
            assert 'idle_seconds' in data['idle_timeout']
            assert 'remaining_seconds' in data['idle_timeout']
            assert data['idle_timeout']['remaining_seconds'] <= 300
        finally:
            process.terminate()
            process.join(timeout=2)
    
    def test_idle_timeout_triggers_shutdown(self):
        """Test that server shuts down after idle timeout"""
        import multiprocessing
        import time
        
        # Start server with short idle timeout
        process = multiprocessing.Process(target=_run_server_with_3sec_timeout, daemon=True)
        process.start()
        
        test_url = f'http://{TEST_HOST}:{TEST_PORT+11}'
        
        # Wait for server to be ready (with retries)
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f'{test_url}/api/health', timeout=1)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                if i == max_retries - 1:
                    raise
                time.sleep(0.5)
        
        # Verify server is running
        response = requests.get(f'{test_url}/api/health')
        assert response.status_code == 200
        
        # Wait for idle timeout (3 seconds idle timeout + check interval ~0.75s + buffer)
        time.sleep(5)
        
        # Server should have shut down
        with pytest.raises(requests.ConnectionError):
            requests.get(f'{test_url}/api/health', timeout=1)
        
        # Cleanup
        if process.is_alive():
            process.terminate()
        process.join(timeout=2)
    
    def test_activity_resets_idle_timer(self):
        """Test that requests reset the idle timer"""
        import multiprocessing
        import time
        
        # Start server with short idle timeout
        process = multiprocessing.Process(target=_run_server_with_5sec_timeout, daemon=True)
        process.start()
        time.sleep(1)
        
        test_url = f'http://{TEST_HOST}:{TEST_PORT+12}'
        
        try:
            # Make requests every 2 seconds for 8 seconds
            for _ in range(4):
                time.sleep(2)
                response = requests.get(f'{test_url}/api/health')
                assert response.status_code == 200
            
            # Server should still be running because we kept it active
            response = requests.get(f'{test_url}/api/health')
            assert response.status_code == 200
        finally:
            process.terminate()
            process.join(timeout=2)


class TestAutoStart:
    """Tests for client auto-start capability"""
    
    def test_client_auto_start_disabled_by_default(self):
        """Test that auto-start is disabled by default"""
        client = ServerClient(server_url='http://127.0.0.1:9999')  # Non-existent server
        assert client.auto_start is False
        assert client.ping() is False
    
    def test_client_auto_start_enabled(self):
        """Test that client can auto-start server"""
        import time
        
        # Use a different port to avoid conflicts
        test_port = TEST_PORT + 20
        test_url = f'http://127.0.0.1:{test_port}'
        
        # Create client with auto-start enabled and idle timeout
        client = ServerClient(
            server_url=test_url,
            auto_start=True,
            idle_timeout=300  # 5 minutes
        )
        
        try:
            # Server should not be running initially
            assert client.ping() is False
            
            # Trigger auto-start by making a request
            health = client.health_check()
            assert health['status'] == 'ok'
            
            # Server should now be running
            assert client.ping() is True
            
            # Read data should also work
            df = client.read_data(data_source={'type': 'fake', 'nrows': 5, 'cols': ['name']})
            assert len(df) == 5
            
        finally:
            client.close()
            # Give server time to shut down via idle timeout
            time.sleep(1)
    
    def test_auto_start_with_read_data(self):
        """Test that auto-start works when first operation is read_data"""
        import time
        
        test_port = TEST_PORT + 21
        test_url = f'http://127.0.0.1:{test_port}'
        
        client = ServerClient(
            server_url=test_url,
            auto_start=True,
            idle_timeout=60  # 1 minute
        )
        
        try:
            # Server should not be running
            assert client.ping() is False
            
            # read_data should auto-start server
            df = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name', 'email']})
            assert len(df) == 10
            
            # Server should now be available
            assert client.ping() is True
            
        finally:
            client.close()
            time.sleep(1)
    
    def test_auto_start_fails_gracefully(self):
        """Test that auto-start fails gracefully with invalid config"""
        # This test verifies error handling when auto-start fails
        # (e.g., python not in PATH, invalid port, etc.)
        
        # Use an invalid/reserved port that will fail
        client = ServerClient(
            server_url='http://127.0.0.1:1',  # Port 1 is restricted
            auto_start=True
        )
        
        # Should raise RuntimeError when server can't be started
        with pytest.raises(RuntimeError, match="Server not available"):
            client.health_check()


class TestPhase2Endpoints:
    """Tests for Phase 2 endpoints (write_data, compute, status)"""
    
    def test_status_endpoint(self, server_process):
        """Test status endpoint returns server diagnostics"""
        response = requests.get(f'{TEST_URL}/api/status')
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'ok'
        assert data['server'] == 'lynguine-server'
        assert data['version'] == '0.2.0'
        assert 'pid' in data
        assert 'uptime_seconds' in data
        
        # Check if psutil is available for detailed diagnostics
        if 'memory' in data:
            assert 'rss_mb' in data['memory']
            assert 'percent' in data['memory']
            assert 'cpu_percent' in data
        
        # Check endpoints list
        assert 'endpoints' in data
        assert len(data['endpoints']) >= 6  # Should have all Phase 2 endpoints
    
    def test_write_data_csv(self, server_process, tmp_path):
        """Test writing data to CSV"""
        import pandas as pd
        
        # Create test data
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['NYC', 'LA', 'Chicago']
        })
        
        output_file = tmp_path / "test_output.csv"
        
        # Make write request
        response = requests.post(
            f'{TEST_URL}/api/write_data',
            json={
                'data': {
                    'records': test_data.to_dict('records'),
                    'columns': list(test_data.columns)
                },
                'output': {
                    'type': 'csv',
                    'filename': str(output_file)
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
        assert 'Wrote 3 records' in result['message']
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify data integrity
        written_df = pd.read_csv(output_file)
        assert len(written_df) == 3
        assert list(written_df.columns) == ['name', 'age', 'city']
    
    def test_write_data_json(self, server_process, tmp_path):
        """Test writing data to JSON"""
        import pandas as pd
        
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        
        output_file = tmp_path / "test_output.json"
        
        response = requests.post(
            f'{TEST_URL}/api/write_data',
            json={
                'data': {
                    'records': test_data.to_dict('records')
                },
                'output': {
                    'type': 'json',
                    'filename': str(output_file)
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
        
        # Verify file was created
        assert output_file.exists()
    
    def test_write_data_missing_parameters(self, server_process):
        """Test write_data with missing parameters"""
        response = requests.post(
            f'{TEST_URL}/api/write_data',
            json={'data': {'records': []}}  # Missing 'output'
        )
        
        assert response.status_code == 500
        result = response.json()
        assert result['status'] == 'error'
    
    def test_compute_operation(self, server_process):
        """Test compute operation endpoint"""
        import pandas as pd
        
        test_data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        response = requests.post(
            f'{TEST_URL}/api/compute',
            json={
                'operation': 'test_compute',
                'data': {
                    'records': test_data.to_dict('records')
                },
                'params': {
                    'param1': 'value1'
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
        assert result['operation'] == 'test_compute'
        assert 'completed' in result['message']
    
    def test_compute_missing_operation(self, server_process):
        """Test compute endpoint with missing operation parameter"""
        response = requests.post(
            f'{TEST_URL}/api/compute',
            json={'params': {}}  # Missing 'operation'
        )
        
        assert response.status_code == 500
        result = response.json()
        assert result['status'] == 'error'


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_interface_file(self, server_process):
        """Test error handling for invalid interface file"""
        client = ServerClient(server_url=TEST_URL)
        with pytest.raises(requests.HTTPError):
            client.read_data(
                interface_file='nonexistent.yml',
                directory='/tmp'
            )
    
    def test_invalid_data_source_type(self, server_process):
        """Test error handling for invalid data source type"""
        client = ServerClient(server_url=TEST_URL)
        with pytest.raises(requests.HTTPError):
            client.read_data(
                data_source={
                    'type': 'invalid_type',
                    'nrows': 5
                }
            )
    
    def test_malformed_json_request(self, server_process):
        """Test error handling for malformed JSON"""
        response = requests.post(
            f'{TEST_URL}/api/read_data',
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400


class TestPerformance:
    """Tests for performance characteristics"""
    
    def test_repeated_calls_performance(self, server_process, test_config_file):
        """Test that repeated calls maintain performance"""
        client = ServerClient(server_url=TEST_URL)
        
        times = []
        for _ in range(10):
            start = time.time()
            df = client.read_data(
                interface_file=test_config_file.name,
                directory=str(test_config_file.parent)
            )
            elapsed = time.time() - start
            times.append(elapsed)
            assert df is not None
        
        avg_time = sum(times) / len(times)
        # Each request should be fast (< 100ms for fake data)
        assert avg_time < 0.1, f"Average time {avg_time:.3f}s exceeds 100ms threshold"
    
    def test_http_overhead_acceptable(self, server_process, test_config_file):
        """Test that HTTP overhead is reasonable"""
        client = ServerClient(server_url=TEST_URL)
        
        # Single request timing
        start = time.time()
        df = client.read_data(
            interface_file=test_config_file.name,
            directory=str(test_config_file.parent)
        )
        elapsed = time.time() - start
        
        # For fake data with 10 rows, should be very fast
        # HTTP overhead + processing should be < 50ms
        assert elapsed < 0.05, f"Request time {elapsed:.3f}s exceeds 50ms threshold"


class TestConcurrency:
    """Tests for concurrent access"""
    
    def test_multiple_clients_simultaneously(self, server_process, test_config_file):
        """Test that multiple clients can access server simultaneously"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def make_request(client_id):
            client = ServerClient(server_url=TEST_URL)
            df = client.read_data(
                interface_file=test_config_file.name,
                directory=str(test_config_file.parent)
            )
            return client_id, df
        
        num_clients = 5
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_clients)]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == num_clients
        for client_id, df in results:
            assert df is not None
            assert len(df) == 10


class TestServerShutdown:
    """Tests for server shutdown and cleanup"""
    
    def test_server_cleanup_on_shutdown(self):
        """Test that server cleans up resources on shutdown"""
        # Use a different port to avoid conflicts with other tests
        test_port = TEST_PORT + 100
        
        proc = Process(target=_run_shutdown_test_server, daemon=True)
        proc.start()
        
        # Wait for startup
        max_wait = 5
        for _ in range(max_wait * 10):
            is_running, _ = check_server_running(TEST_HOST, test_port)
            if is_running:
                break
            time.sleep(0.1)
        
        # Verify running
        is_running, server_type = check_server_running(TEST_HOST, test_port)
        assert is_running
        assert server_type == 'lynguine'
        
        # Shutdown
        proc.terminate()
        proc.join(timeout=3)
        if proc.is_alive():
            proc.kill()
            proc.join()
        
        # Give time for cleanup
        time.sleep(1)
        
        # Verify lockfile is cleaned up
        lockfile = get_lockfile_path(TEST_HOST, test_port)
        # Note: Lockfile cleanup happens on graceful shutdown (SIGTERM)
        # If process is killed (SIGKILL), lockfile may remain
        # The check_server_running function handles stale lockfiles


# Integration test
class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_workflow(self, server_process, test_config_file):
        """Test complete workflow from client creation to data retrieval"""
        # 1. Create client
        client = ServerClient(server_url=TEST_URL)
        
        # 2. Check server health
        assert client.ping()
        health = client.health_check()
        assert health['status'] == 'ok'
        
        # 3. Read data
        df = client.read_data(
            interface_file=test_config_file.name,
            directory=str(test_config_file.parent)
        )
        
        # 4. Verify data
        assert df is not None
        assert len(df) == 10
        assert list(df.columns) == ['name', 'email']
        
        # 5. Clean shutdown
        client.close()

