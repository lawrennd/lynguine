"""
Session endpoint handlers for lynguine server (Phase 5)

These handlers provide the CustomDataFrame API over HTTP/REST for
stateful data sessions with crash recovery.
"""
from typing import Dict, Any
import pandas as pd
import numpy as np


def parse_session_path(path: str) -> tuple:
    """Parse session ID and operation from path.
    
    Args:
        path: Request path
    
    Returns:
        (session_id, operation) tuple
    """
    # Path format: /api/sessions/{session_id}/{operation}
    parts = path.split('/')
    if len(parts) < 4:
        return (None, None)
    
    session_id = parts[3]
    operation = parts[4] if len(parts) > 4 else None
    return (session_id, operation)


def serialize_value(value):
    """Serialize value for JSON response (handles pandas/numpy types)"""
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return value.to_dict()
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def handle_create_session(handler, session_manager, request_data: Dict[str, Any]):
    """Create a new session"""
    if not session_manager:
        handler.send_error_response(ValueError("Session management not initialized"), 500)
        return
    
    try:
        # Extract parameters
        interface_file = request_data.get('interface_file')
        if not interface_file:
            raise ValueError("Missing required parameter: interface_file")
        
        directory = request_data.get('directory', '.')
        interface_field = request_data.get('interface_field')
        timeout = request_data.get('timeout', 3600)
        
        # Create session
        session = session_manager.create_session(
            interface_file=interface_file,
            directory=directory,
            interface_field=interface_field,
            timeout=timeout
        )
        
        handler.send_json_response({
            'status': 'success',
            'session': session.get_metadata()
        })
        
    except Exception as e:
        handler.log.error(f"Error creating session: {e}")
        handler.send_error_response(e, 500)


def handle_list_sessions(handler, session_manager):
    """List all sessions"""
    if not session_manager:
        handler.send_error_response(ValueError("Session management not initialized"), 500)
        return
    
    try:
        sessions = session_manager.list_sessions()
        handler.send_json_response({
            'status': 'success',
            'sessions': sessions,
            'total_sessions': len(sessions),
            'total_memory_mb': session_manager.get_total_memory()
        })
    except Exception as e:
        handler.log.error(f"Error listing sessions: {e}")
        handler.send_error_response(e, 500)


def handle_delete_session(handler, session_manager, path: str):
    """Delete a session"""
    if not session_manager:
        handler.send_error_response(ValueError("Session management not initialized"), 500)
        return
    
    try:
        session_id, _ = parse_session_path(path)
        if not session_id:
            raise ValueError("Session ID required")
        
        session_manager.delete_session(session_id)
        
        handler.send_json_response({
            'status': 'success',
            'message': f'Session {session_id} deleted'
        })
    except KeyError as e:
        handler.send_error_response(e, 404)
    except Exception as e:
        handler.log.error(f"Error deleting session: {e}")
        handler.send_error_response(e, 500)


def handle_session_operation(handler, session_manager, path: str, request_data: Dict[str, Any]):
    """Handle session-specific operations (mirrors CustomDataFrame API)"""
    if not session_manager:
        handler.send_error_response(ValueError("Session management not initialized"), 500)
        return
    
    try:
        session_id, operation = parse_session_path(path)
        if not session_id:
            raise ValueError("Session ID required")
        
        # Get session
        session = session_manager.get_session(session_id)
        cdf = session.cdf
        
        # Route to specific operation
        if operation is None:
            # GET /api/sessions/{id} - get session info
            handler.send_json_response({
                'status': 'success',
                'session': session.get_metadata()
            })
        
        elif operation == 'set_index':
            index = request_data.get('index')
            if index is None:
                raise ValueError("Missing required parameter: index")
            cdf.set_index(index)
            handler.send_json_response({'status': 'success'})
        
        elif operation == 'get_index':
            index = cdf.get_index()
            handler.send_json_response({
                'status': 'success',
                'index': serialize_value(index)
            })
        
        elif operation == 'set_column':
            column = request_data.get('column')
            if column is None:
                raise ValueError("Missing required parameter: column")
            cdf.set_column(column)
            handler.send_json_response({'status': 'success'})
        
        elif operation == 'get_column':
            column = cdf.get_column()
            handler.send_json_response({
                'status': 'success',
                'column': column
            })
        
        elif operation == 'get_value':
            value = cdf.get_value()
            handler.send_json_response({
                'status': 'success',
                'value': serialize_value(value)
            })
        
        elif operation == 'set_value':
            value = request_data.get('value')
            if value is None:
                raise ValueError("Missing required parameter: value")
            cdf.set_value(value)
            handler.send_json_response({'status': 'success'})
        
        elif operation == 'get_value_at':
            index = request_data.get('index')
            column = request_data.get('column')
            if index is None or column is None:
                raise ValueError("Missing required parameters: index, column")
            
            # Temporarily set focus, get value, restore focus
            old_index = cdf.get_index()
            old_column = cdf.get_column()
            cdf.set_index(index)
            cdf.set_column(column)
            value = cdf.get_value()
            cdf.set_index(old_index)
            cdf.set_column(old_column)
            
            handler.send_json_response({
                'status': 'success',
                'value': serialize_value(value)
            })
        
        elif operation == 'get_shape':
            shape = cdf.get_shape()
            handler.send_json_response({
                'status': 'success',
                'shape': shape
            })
        
        elif operation == 'get_columns':
            columns = list(cdf.columns)
            handler.send_json_response({
                'status': 'success',
                'columns': columns
            })
        
        elif operation == 'get_indices':
            indices = [serialize_value(idx) for idx in cdf.index]
            handler.send_json_response({
                'status': 'success',
                'indices': indices
            })
        
        elif operation == 'get_input_columns':
            columns = cdf.get_input_columns()
            handler.send_json_response({
                'status': 'success',
                'columns': columns
            })
        
        elif operation == 'get_output_columns':
            columns = cdf.get_output_columns()
            handler.send_json_response({
                'status': 'success',
                'columns': columns
            })
        
        elif operation == 'get_series_columns':
            columns = cdf.get_series_columns()
            handler.send_json_response({
                'status': 'success',
                'columns': columns
            })
        
        elif operation == 'get_column_type':
            column = request_data.get('column')
            if column is None:
                raise ValueError("Missing required parameter: column")
            col_type = cdf.get_column_type(column)
            handler.send_json_response({
                'status': 'success',
                'column_type': col_type
            })
        
        elif operation == 'set_selector':
            column = request_data.get('column')
            if column is None:
                raise ValueError("Missing required parameter: column")
            cdf.set_selector(column)
            handler.send_json_response({'status': 'success'})
        
        elif operation == 'get_selector':
            selector = cdf.get_selector()
            handler.send_json_response({
                'status': 'success',
                'selector': selector
            })
        
        elif operation == 'set_subindex':
            value = request_data.get('value')
            if value is None:
                raise ValueError("Missing required parameter: value")
            cdf.set_subindex(value)
            handler.send_json_response({'status': 'success'})
        
        elif operation == 'get_subindex':
            subindex = cdf.get_subindex()
            handler.send_json_response({
                'status': 'success',
                'subindex': serialize_value(subindex)
            })
        
        elif operation == 'get_subseries':
            subseries = cdf.get_subseries()
            # Convert to dict for JSON serialization
            handler.send_json_response({
                'status': 'success',
                'subseries': {
                    'records': subseries.to_dict('records'),
                    'shape': subseries.shape
                }
            })
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
    except KeyError as e:
        handler.send_error_response(e, 404)
    except Exception as e:
        handler.log.error(f"Error in session operation '{operation}': {e}")
        import traceback
        traceback.print_exc()
        handler.send_error_response(e, 500)

