"""
Tests for compute mode parameter (replace, append, prepend).

This test file covers CIP-0007: Append Mode for Compute Operations.
"""

import pytest
import pandas as pd
from lynguine.assess.compute import Compute
from lynguine.assess.data import CustomDataFrame


@pytest.fixture
def sample_dataframe():
    """Create a sample CustomDataFrame for testing with mutable content column."""
    data = pd.DataFrame({'content': ['Initial content']}, index=['A'])
    return CustomDataFrame(data=data, colspecs="cache")


@pytest.fixture
def empty_dataframe():
    """Create a CustomDataFrame with empty content and mutable column."""
    data = pd.DataFrame({'content': ['']}, index=['A'])
    return CustomDataFrame(data=data, colspecs="cache")


@pytest.fixture
def simple_function():
    """Create a simple test function."""
    def test_func(message="default"):
        return message
    test_func.__name__ = "test_func"
    return test_func


@pytest.fixture
def compute_instance():
    """Create a Compute instance for testing."""
    interface = {"compute": []}
    return Compute(interface)


class TestComputeReplaceMode:
    """Test replace mode (default behavior)."""
    
    def test_replace_mode_default(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test that replace mode is default when mode is not specified."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "refresh": True,  # Force refresh to run compute
                "args": {"message": "New content"}
            }
        }
        
        # Mock the function list
        mocker.patch.object(
            compute_instance, 
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "New content"
    
    def test_replace_mode_explicit(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test explicit replace mode."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "replace",
                "refresh": True,
                "args": {"message": "New content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "New content"


class TestComputeAppendMode:
    """Test append mode functionality."""
    
    def test_append_to_existing_content(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test appending to existing non-empty content."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "refresh": True,
                "separator": "\n",
                "args": {"message": "Appended content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "Initial content\nAppended content"
    
    def test_append_to_empty_content(self, empty_dataframe, simple_function, compute_instance, mocker):
        """Test appending to empty content (should just set the value)."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "args": {"message": "First content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(empty_dataframe, interface)
        
        result = empty_dataframe.get_value_column("content")
        assert result == "First content"
    
    def test_append_default_separator(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test that default separator is used when not specified."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "refresh": True,
                # separator not specified - should use default "\n\n---\n\n"
                "args": {"message": "Appended content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "Initial content\n\n---\n\nAppended content"
    
    def test_append_empty_separator(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test appending with empty separator (direct concatenation)."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "refresh": True,
                "separator": "",
                "args": {"message": " appended"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "Initial content appended"
    
    def test_multiple_appends(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test multiple append operations accumulate correctly."""
        interface = {
            "compute": [
                {
                    "function": "test_func",
                    "field": "content",
                    "mode": "append",
                    "refresh": True,
                    "separator": "\n",
                    "args": {"message": "Second"}
                },
                {
                    "function": "test_func",
                    "field": "content",
                    "mode": "append",
                    "refresh": True,
                    "separator": "\n",
                    "args": {"message": "Third"}
                }
            ]
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "Initial content\nSecond\nThird"


class TestComputePrependMode:
    """Test prepend mode functionality."""
    
    def test_prepend_to_existing_content(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test prepending to existing non-empty content."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "prepend",
                "refresh": True,
                "separator": "\n",
                "args": {"message": "Prepended content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        assert result == "Prepended content\nInitial content"
    
    def test_prepend_to_empty_content(self, empty_dataframe, simple_function, compute_instance, mocker):
        """Test prepending to empty content (should just set the value)."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "prepend",
                "args": {"message": "First content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(empty_dataframe, interface)
        
        result = empty_dataframe.get_value_column("content")
        assert result == "First content"
    
    def test_multiple_prepends(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test multiple prepend operations accumulate correctly (newest first)."""
        interface = {
            "compute": [
                {
                    "function": "test_func",
                    "field": "content",
                    "mode": "prepend",
                    "refresh": True,
                    "separator": "\n",
                    "args": {"message": "Second"}
                },
                {
                    "function": "test_func",
                    "field": "content",
                    "mode": "prepend",
                    "refresh": True,
                    "separator": "\n",
                    "args": {"message": "First"}
                }
            ]
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        # First is prepended last, so it appears first
        assert result == "First\nSecond\nInitial content"


class TestComputeModeErrors:
    """Test error handling for invalid mode values."""
    
    def test_invalid_mode_raises_error(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test that invalid mode value raises ValueError."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "invalid_mode",
                "refresh": True,
                "args": {"message": "Test"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        with pytest.raises(ValueError, match="Invalid mode 'invalid_mode'"):
            compute_instance.run(sample_dataframe, interface)


class TestComputeModeWithNewColumn:
    """Test mode parameter with columns that don't exist yet."""
    
    def test_append_to_nonexistent_column(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test appending to a column that doesn't exist yet (must pre-create with direct assignment)."""
        # Pre-create the column using direct assignment (the proper way in CustomDataFrame)
        sample_dataframe['new_column'] = pd.Series([''], index=sample_dataframe.index)
        
        interface = {
            "compute": {
                "function": "test_func",
                "field": "new_column",
                "mode": "append",
                "refresh": True,
                "args": {"message": "First content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("new_column")
        # Should just set the value since column was empty
        assert result == "First content"
    
    def test_prepend_to_nonexistent_column(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test prepending to a column that doesn't exist yet (must pre-create with direct assignment)."""
        # Pre-create the column using direct assignment (the proper way in CustomDataFrame)
        sample_dataframe['new_column'] = pd.Series([''], index=sample_dataframe.index)
        
        interface = {
            "compute": {
                "function": "test_func",
                "field": "new_column",
                "mode": "prepend",
                "refresh": True,
                "args": {"message": "First content"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("new_column")
        # Should just set the value since column was empty
        assert result == "First content"


class TestComputeModeWithRefresh:
    """Test mode parameter interaction with refresh flag."""
    
    def test_append_to_non_empty_field_without_refresh(self, sample_dataframe, simple_function, compute_instance, mocker):
        """
        Regression test for bug where append mode fails on non-empty fields.
        
        This is the primary use case for append mode: adding to existing content.
        The bug was that append only worked with refresh=True, defeating the purpose.
        
        With the fix (2025-12-21), append/prepend modes ALWAYS write, regardless
        of refresh flag, because they need to read existing content to work correctly.
        """
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "refresh": False,  # Should work WITHOUT refresh=True
                "separator": "\n---\n",
                "args": {"message": "Second entry"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        # Should append even with refresh=False (this is the fix!)
        assert result == "Initial content\n---\nSecond entry"
        assert "Initial content" in result
        assert "Second entry" in result
    
    def test_prepend_to_non_empty_field_without_refresh(self, sample_dataframe, simple_function, compute_instance, mocker):
        """
        Regression test for bug where prepend mode fails on non-empty fields.
        
        Like append, prepend should work without refresh=True because it needs
        to read existing content. Tests the same fix applied to prepend mode.
        """
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "prepend",
                "refresh": False,  # Should work WITHOUT refresh=True
                "separator": "\n---\n",
                "args": {"message": "First entry"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        # Should prepend even with refresh=False (this is the fix!)
        assert result == "First entry\n---\nInitial content"
        assert "Initial content" in result
        assert "First entry" in result
    
    def test_append_with_refresh_true_always_appends(self, sample_dataframe, simple_function, compute_instance, mocker):
        """Test that append with refresh=True always appends even if value exists."""
        interface = {
            "compute": {
                "function": "test_func",
                "field": "content",
                "mode": "append",
                "refresh": True,  # Always refresh
                "separator": " | ",
                "args": {"message": "Always appends"}
            }
        }
        
        mocker.patch.object(
            compute_instance,
            '_compute_functions_list',
            return_value=[{
                "name": "test_func",
                "function": simple_function,
                "default_args": {"message": "default"},
                "context": False
            }]
        )
        
        compute_instance.run(sample_dataframe, interface)
        
        result = sample_dataframe.get_value_column("content")
        # Should have appended because refresh=True
        assert result == "Initial content | Always appends"
