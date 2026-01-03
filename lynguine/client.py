"""
Lynguine Client - HTTP client for lynguine server mode

This module provides a client interface for connecting to a lynguine server,
enabling fast repeated access without startup costs.

This is Phase 1: Proof of Concept - minimal implementation for validation.
"""

import json
import time
from typing import Dict, Any, Optional
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
        timeout: float = 30.0
    ):
        """
        Initialize the server client
        
        :param server_url: URL of the lynguine server (default: http://127.0.0.1:8765)
        :param timeout: Request timeout in seconds (default: 30.0)
        :raises ImportError: If requests library is not installed
        """
        if not HAS_REQUESTS:
            raise ImportError(
                "requests library is required for lynguine server mode. "
                "Install it with: pip install requests"
            )
        
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self._session = requests.Session()
        
        log.debug(f"Initialized ServerClient for {self.server_url}")
    
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
        Get server health status
        
        :return: Server health information
        :raises requests.HTTPError: If request fails
        """
        response = self._session.get(
            f'{self.server_url}/api/health',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def read_data(
        self,
        interface_file: Optional[str] = None,
        directory: str = '.',
        interface_field: Optional[str] = None,
        data_source: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Read data via the lynguine server
        
        Either provide interface_file (to load from a lynguine interface config)
        or provide data_source (to read directly from a data source).
        
        :param interface_file: Path to lynguine interface YAML file
        :param directory: Directory for resolving relative paths (default: '.')
        :param interface_field: Optional field name within interface
        :param data_source: Direct data source specification (dict with 'type', 'filename', etc.)
        :return: DataFrame containing the data
        :raises ValueError: If neither interface_file nor data_source is provided
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
    
    def close(self):
        """Close the client session"""
        if self._session:
            self._session.close()
            log.debug("Closed ServerClient session")
    
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

