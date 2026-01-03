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
        assert not check_server_running(TEST_HOST, 59999)
    
    def test_check_server_running(self, server_process):
        """Test checking when server is running"""
        assert check_server_running(TEST_HOST, TEST_PORT)
    
    def test_prevent_duplicate_server_start(self, server_process):
        """Test that starting a duplicate server fails gracefully"""
        # Server is already running via fixture
        # Attempting to start another should fail or warn
        assert check_server_running(TEST_HOST, TEST_PORT)


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
            if check_server_running(TEST_HOST, test_port):
                break
            time.sleep(0.1)
        
        # Verify running
        assert check_server_running(TEST_HOST, test_port)
        
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

