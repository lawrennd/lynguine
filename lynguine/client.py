"""
Lynguine Client - HTTP client for lynguine server mode

This module provides a client interface for connecting to a lynguine server,
enabling fast repeated access without startup costs.

Phase 1: Proof of Concept - basic functionality validated
Phase 2: Core Features - auto-start capability
Phase 3: Robustness - retry logic, crash recovery, graceful degradation
"""

import json
import time
import subprocess
import urllib.parse
from typing import Dict, Any, Optional, Callable
import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

from lynguine.log import Logger

# Create logger instance
log = Logger(name="lynguine.client", level="info", filename="lynguine-client.log")


class ServerClient:
    """
    Client for lynguine server mode.
    
    Provides a simple interface to connect to a running lynguine server
    and perform operations without incurring startup costs.
    
    Example:
        client = ServerClient('http://127.0.0.1:8765')
        df = client.read_data(interface_file='config.yml', directory='.')
    """
    
    def __init__(
        self, 
        server_url: str = 'http://127.0.0.1:8765',
        timeout: float = 30.0,
        auto_start: bool = False,
        idle_timeout: int = 0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the server client
        
        :param server_url: URL of the lynguine server (default: http://127.0.0.1:8765)
        :param timeout: Request timeout in seconds (default: 30.0)
        :param auto_start: Auto-start server if not running (default: False)
        :param idle_timeout: Server idle timeout in seconds when auto-starting (0=disabled, default: 0)
        :param max_retries: Maximum number of retries for failed requests (default: 3)
        :param retry_delay: Base delay between retries in seconds, uses exponential backoff (default: 1.0)
        :raises ImportError: If requests library is not installed
        """
        if not HAS_REQUESTS:
            raise ImportError(
                "requests library is required for lynguine server mode. "
                "Install it with: pip install requests"
            )
        
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.auto_start = auto_start
        self.idle_timeout = idle_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session = requests.Session()
        self._server_process = None  # Track auto-started server process
        
        log.debug(f"Initialized ServerClient for {self.server_url} (auto_start={auto_start}, max_retries={max_retries})")
    
    def _start_server(self) -> bool:
        """
        Start a lynguine server as a subprocess
        
        :return: True if server started successfully, False otherwise
        """
        # Parse server URL to get host and port
        parsed = urllib.parse.urlparse(self.server_url)
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port or 8765
        
        log.info(f"Auto-starting lynguine server on {host}:{port}")
        
        try:
            # Build command
            cmd = [
                'python', '-m', 'lynguine.server',
                '--host', host,
                '--port', str(port)
            ]
            
            if self.idle_timeout > 0:
                cmd.extend(['--idle-timeout', str(self.idle_timeout)])
            
            # Start server as subprocess
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent
            )
            
            # Wait for server to be ready (with retries)
            max_retries = 20
            for i in range(max_retries):
                time.sleep(0.5)
                if self.ping():
                    log.info(f"Server started successfully (PID: {self._server_process.pid})")
                    return True
            
            log.error("Server failed to start within timeout")
            return False
            
        except Exception as e:
            log.error(f"Failed to start server: {e}")
            return False
    
    def _ensure_server_available(self) -> bool:
        """
        Ensure server is available, auto-starting if needed
        
        :return: True if server is available, False otherwise
        """
        # Check if server is already running
        if self.ping():
            return True
        
        # If auto_start is enabled, try to start the server
        if self.auto_start:
            log.info("Server not available, attempting auto-start")
            return self._start_server()
        
        return False
    
    def _make_request_with_retry(
        self,
        request_func: Callable,
        operation_name: str = "request"
    ) -> Any:
        """
        Make a request with automatic retry logic and crash recovery
        
        :param request_func: Function that makes the actual request
        :param operation_name: Name of the operation for logging
        :return: Result from request_func
        :raises RuntimeError: If all retries exhausted and server still unavailable
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Ensure server is available before making request
                if not self._ensure_server_available():
                    raise RuntimeError(f"Server not available at {self.server_url}")
                
                # Make the request
                return request_func()
                
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Exponential backoff: delay * 2^attempt
                    delay = self.retry_delay * (2 ** attempt)
                    log.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    
                    # If auto_start is enabled, try to restart the server
                    if self.auto_start:
                        log.info("Attempting to restart server after connection failure")
                        self._start_server()
                else:
                    log.error(f"{operation_name} failed after {self.max_retries + 1} attempts")
            
            except requests.HTTPError as e:
                # HTTP errors (4xx, 5xx) shouldn't trigger retry unless it's a 5xx server error
                if e.response is not None and e.response.status_code >= 500 and attempt < self.max_retries:
                    last_exception = e
                    delay = self.retry_delay * (2 ** attempt)
                    log.warning(
                        f"{operation_name} returned server error (attempt {attempt + 1}/{self.max_retries + 1}): "
                        f"{e.response.status_code}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    # Client errors (4xx) or final server error - don't retry, raise immediately
                    raise
        
        # All retries exhausted
        if last_exception:
            raise RuntimeError(
                f"{operation_name} failed after {self.max_retries + 1} attempts: {last_exception}"
            ) from last_exception
        
        raise RuntimeError(f"{operation_name} failed for unknown reason")
    
    def ping(self) -> bool:
        """
        Test connectivity to the server
        
        :return: True if server is reachable, False otherwise
        """
        try:
            response = self._session.get(
                f'{self.server_url}/api/ping',
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            log.warning(f"Ping failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Get server health status (with automatic retry on failure)
        
        :return: Server health information
        :raises requests.HTTPError: If request fails
        :raises RuntimeError: If server is not available after retries
        """
        def _do_health_check():
            response = self._session.get(
                f'{self.server_url}/api/health',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        return self._make_request_with_retry(_do_health_check, "health_check")
    
    def read_data(
        self,
        interface_file: Optional[str] = None,
        directory: str = '.',
        interface_field: Optional[str] = None,
        data_source: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Read data via the lynguine server (with automatic retry on failure)
        
        Either provide interface_file (to load from a lynguine interface config)
        or provide data_source (to read directly from a data source).
        
        :param interface_file: Path to lynguine interface YAML file
        :param directory: Directory for resolving relative paths (default: '.')
        :param interface_field: Optional field name within interface
        :param data_source: Direct data source specification (dict with 'type', 'filename', etc.)
        :return: DataFrame containing the data
        :raises ValueError: If neither interface_file nor data_source is provided
        :raises RuntimeError: If server is not available after retries
        :raises requests.HTTPError: If request fails
        """
        # Build request
        request_data = {}
        
        if interface_file is not None:
            request_data['interface_file'] = interface_file
            request_data['directory'] = directory
            if interface_field is not None:
                request_data['interface_field'] = interface_field
        elif data_source is not None:
            request_data['data_source'] = data_source
        else:
            raise ValueError(
                "Must provide either interface_file or data_source"
            )
        
        def _do_read_data():
            # Send request
            start_time = time.time()
            response = self._session.post(
                f'{self.server_url}/api/read_data',
                json=request_data,
                timeout=self.timeout
            )
            request_time = time.time() - start_time
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get('error_message', 'Unknown error')
                log.error(f"Server error: {error_msg}")
                response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            if result['status'] != 'success':
                raise ValueError(f"Server returned error: {result}")
            
            # Convert back to DataFrame
            data = result['data']
            df = pd.DataFrame.from_records(data['records'])
            
            log.debug(
                f"read_data completed in {request_time:.3f}s, "
                f"shape={data['shape']}"
            )
            
            return df
        
        return self._make_request_with_retry(_do_read_data, "read_data")
    
    def close(self):
        """
        Close the client session
        
        Note: Does NOT stop auto-started servers by design.
        Auto-started servers remain running for other clients and will
        shut down via idle timeout if configured.
        """
        if self._session:
            self._session.close()
            log.debug("Closed ServerClient session")
        
        # Note: We intentionally do NOT terminate self._server_process
        # The server should remain running for other clients and will
        # shut down via idle timeout if configured
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Convenience function for quick usage
def create_client(server_url: str = 'http://127.0.0.1:8765') -> ServerClient:
    """
    Create a lynguine server client
    
    :param server_url: URL of the lynguine server
    :return: ServerClient instance
    """
    return ServerClient(server_url=server_url)

