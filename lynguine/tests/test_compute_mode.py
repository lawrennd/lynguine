"""
Tests for compute mode parameter (replace, append, prepend).

This test file covers CIP-0007: Append Mode for Compute Operations.

Note: These tests directly test the compute mode logic by creating minimal
setups. More comprehensive integration tests should be added separately.
"""

import pytest
import pandas as pd
from lynguine.assess.compute import Compute
from lynguine.assess.data import CustomDataFrame


def test_replace_mode_default():
    """Test that replace mode is default when mode is not specified."""
    # Create data with existing content
    data = pd.DataFrame({'content': ['Old content']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    # Create interface with compute (no mode specified)
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "args": {"message": "New content"}
        }
    }
    
    # Mock function
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    # Should replace, not append
    result = cdf.get_value_column("content")
    assert result == "New content"


def test_replace_mode_explicit():
    """Test explicit replace mode."""
    data = pd.DataFrame({'content': ['Old content']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "replace",
            "args": {"message": "New content"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "New content"


def test_append_mode_to_existing_content():
    """Test appending to existing non-empty content."""
    data = pd.DataFrame({'content': ['First']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "append",
            "separator": "\n",
            "args": {"message": "Second"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First\nSecond", f"Expected 'First\\nSecond', got: '{result}'"


def test_append_mode_to_empty_content():
    """Test appending to empty content (should just set the value)."""
    data = pd.DataFrame({'content': ['']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "append",
            "args": {"message": "First"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First"


def test_append_mode_default_separator():
    """Test that default separator is used when not specified."""
    data = pd.DataFrame({'content': ['First']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "append",
            # separator not specified - should use default "\n\n---\n\n"
            "args": {"message": "Second"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First\n\n---\n\nSecond"


def test_append_mode_empty_separator():
    """Test appending with empty separator (direct concatenation)."""
    data = pd.DataFrame({'content': ['First']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "append",
            "separator": "",
            "args": {"message": "Second"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "FirstSecond"


def test_prepend_mode_to_existing_content():
    """Test prepending to existing non-empty content."""
    data = pd.DataFrame({'content': ['Second']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "prepend",
            "separator": "\n",
            "args": {"message": "First"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First\nSecond"


def test_prepend_mode_to_empty_content():
    """Test prepending to empty content (should just set the value)."""
    data = pd.DataFrame({'content': ['']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "prepend",
            "args": {"message": "First"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First"


def test_multiple_appends():
    """Test multiple append operations accumulate correctly."""
    data = pd.DataFrame({'content': ['First']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": [
            {
                "function": "simple_concat",
                "field": "content",
                "mode": "append",
                "separator": "\n",
                "args": {"message": "Second"}
            },
            {
                "function": "simple_concat",
                "field": "content",
                "mode": "append",
                "separator": "\n",
                "args": {"message": "Third"}
            }
        ]
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    assert result == "First\nSecond\nThird"


def test_multiple_prepends():
    """Test multiple prepend operations accumulate correctly (newest first)."""
    data = pd.DataFrame({'content': ['Third']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": [
            {
                "function": "simple_concat",
                "field": "content",
                "mode": "prepend",
                "separator": "\n",
                "args": {"message": "Second"}
            },
            {
                "function": "simple_concat",
                "field": "content",
                "mode": "prepend",
                "separator": "\n",
                "args": {"message": "First"}
            }
        ]
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("content")
    # First is prepended last, so it appears first
    assert result == "First\nSecond\nThird"


def test_invalid_mode_raises_error():
    """Test that invalid mode value raises ValueError."""
    data = pd.DataFrame({'content': ['Content']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "content",
            "mode": "invalid_mode",
            "args": {"message": "Test"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    with pytest.raises(ValueError, match="Invalid mode 'invalid_mode'"):
        compute.run(cdf, interface)


def test_append_to_nonexistent_column():
    """Test appending to a column that doesn't exist yet."""
    data = pd.DataFrame({'existing': ['value']}, index=['A'])
    cdf = CustomDataFrame(data=data)
    
    interface = {
        "compute": {
            "function": "simple_concat",
            "field": "new_column",
            "mode": "append",
            "args": {"message": "First"}
        }
    }
    
    def simple_concat(data, message="test"):
        return message
    simple_concat.__name__ = "simple_concat"
    
    compute = Compute(interface)
    compute._list_functions = [
        {
            "name": "simple_concat",
            "function": simple_concat,
            "default_args": {},
            "context": False
        }
    ]
    
    compute.run(cdf, interface)
    
    result = cdf.get_value_column("new_column")
    # Should just set the value since column didn't exist
    assert result == "First"
