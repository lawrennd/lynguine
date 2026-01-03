"""
Server handlers for interface and markdown field extraction.

These handlers provide lightweight field access without loading full CustomDataFrame,
optimized for lamd's mdfield utility integration.
"""

import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from lynguine.config.interface import Interface
from lynguine.util.talk import talk_field
from lynguine.util.yaml import FileFormatError
from lynguine.log import Logger

# Create logger instance
log = Logger(name="lynguine.server_interface_handlers", level="info")


def handle_interface_read(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read field from interface file without loading data.
    
    Loads Interface configuration and extracts a single field value,
    without the overhead of loading CustomDataFrame data.
    
    Args:
        request_data: Dictionary containing:
            - interface_file: Path to interface file (required)
            - field: Field name to extract (required)
            - directory: Working directory (default: '.')
            
    Returns:
        Dictionary with status and extracted value
        
    Example:
        >>> handle_interface_read({
        ...     'interface_file': '_lamd.yml',
        ...     'field': 'title',
        ...     'directory': '.'
        ... })
        {'status': 'success', 'value': 'My Document Title'}
    """
    try:
        interface_file = request_data['interface_file']
        field = request_data['field']
        directory = request_data.get('directory', '.')
        
        log.info(f"Reading field '{field}' from interface '{interface_file}'")
        
        # Load interface (fast, no data loading)
        iface = Interface.from_file(user_file=[interface_file], directory=directory)
        
        # Extract field
        if field in iface:
            value = iface[field]
            log.info(f"Field '{field}' found: {value}")
        else:
            value = None
            log.warning(f"Field '{field}' not found in interface")
        
        return {
            'status': 'success',
            'value': value
        }
        
    except FileNotFoundError as e:
        log.error(f"Interface file not found: {e}")
        return {
            'status': 'error',
            'error': f"Interface file not found: {str(e)}",
            'value': None
        }
    except KeyError as e:
        log.error(f"Missing required parameter: {e}")
        return {
            'status': 'error',
            'error': f"Missing required parameter: {str(e)}",
            'value': None
        }
    except Exception as e:
        log.error(f"Error reading interface field: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'value': None
        }


def handle_talk_field(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract field from markdown frontmatter with config fallback.
    
    Wraps lynguine.util.talk.talk_field() functionality, providing:
    - Markdown frontmatter parsing
    - Fallback to interface config files
    - Array formatting for categories
    - Environment variable expansion
    
    Args:
        request_data: Dictionary containing:
            - field: Field name to extract (required)
            - markdown_file: Path to markdown file (required)
            - config_files: List of config files for fallback (optional)
            
    Returns:
        Dictionary with status and extracted value
        
    Example:
        >>> handle_talk_field({
        ...     'field': 'title',
        ...     'markdown_file': 'talk.md',
        ...     'config_files': ['_lamd.yml']
        ... })
        {'status': 'success', 'value': 'My Talk Title'}
    """
    try:
        field = request_data['field']
        markdown_file = request_data['markdown_file']
        config_files = request_data.get('config_files', [])
        
        log.info(f"Extracting field '{field}' from '{markdown_file}'")
        
        value = ""
        
        try:
            # Try markdown file first
            value = talk_field(field, markdown_file, user_file=config_files)
            log.info(f"Field '{field}' found in markdown: {value}")
            
        except FileFormatError as e:
            # Fall back to config files
            log.info(f"Markdown parse error, falling back to config files: {e}")
            try:
                if config_files:
                    iface = Interface.from_file(user_file=config_files, directory='.')
                    value = iface[field] if field in iface else ""
                    if value:
                        log.info(f"Field '{field}' found in config: {value}")
                    else:
                        log.warning(f"Field '{field}' not found in config")
            except Exception as config_error:
                log.warning(f"Config fallback failed: {config_error}")
                value = ""
                
        except FileNotFoundError as e:
            # Markdown file not found, try config only
            log.warning(f"Markdown file not found, trying config: {e}")
            try:
                if config_files:
                    iface = Interface.from_file(user_file=config_files, directory='.')
                    value = iface[field] if field in iface else ""
            except Exception as config_error:
                log.warning(f"Config fallback failed: {config_error}")
                value = ""
                
        except Exception as e:
            log.warning(f"Error extracting field, returning empty: {e}")
            value = ""
        
        # Handle formatting (categories, env vars, etc.)
        if isinstance(value, list) and field == 'categories':
            value = "['" + "', '".join(value) + "']"
        elif isinstance(value, str):
            value = os.path.expandvars(value)
        
        return {
            'status': 'success',
            'value': value
        }
        
    except KeyError as e:
        log.error(f"Missing required parameter: {e}")
        return {
            'status': 'error',
            'error': f"Missing required parameter: {str(e)}",
            'value': ""
        }
    except Exception as e:
        log.error(f"Unexpected error in talk field extraction: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'value': ""
        }

