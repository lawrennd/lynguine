"""
Tests for get_compute_index() method in CustomDataFrame.

This test suite ensures the method correctly validates indices for compute operations,
which is critical for preventing errors in referia's compute_onchange() functionality.

The get_compute_index() method acts as a validation gate to ensure compute operations
only run on valid, focused indices when they are actually defined.
"""

import pytest
import pandas as pd
import lynguine.assess.data
from lynguine.assess.compute import Compute
from lynguine.config.interface import Interface


def test_get_compute_index_with_valid_index_and_compute():
    """Test that get_compute_index returns the focused index when valid and compute is defined."""
    # Create a CustomDataFrame with some data
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Set the focused index to the first one
    df.set_index(0)
    
    # Call get_compute_index with the full Index object
    result = df.get_compute_index(df.index)
    
    # Should return the focused index
    assert result == 0


def test_get_compute_index_with_no_focused_index():
    """Test that get_compute_index returns None when no index is focused."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Don't set a focused index (it will be None or 0 by default)
    # Force it to None to test
    df._index = None
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None
    assert result is None


def test_get_compute_index_with_invalid_focused_index():
    """Test that get_compute_index returns None when focused index is not in the Index."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Set focused index to something not in the dataframe
    df._index = 999  # Bypass validation by setting directly
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None because 999 is not in the Index
    assert result is None


def test_get_compute_index_with_no_compute_attribute():
    """Test that get_compute_index returns None when compute attribute doesn't exist."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Override compute attribute to simulate it not existing
    # (Can't delete it since it's a property, so we set to an object without _computes)
    class NoCompute:
        pass
    df._compute = NoCompute()
    
    # Set a valid focused index
    df.set_index(0)
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None
    assert result is None


def test_get_compute_index_with_none_compute():
    """Test that get_compute_index returns None when compute is None."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set compute to None
    df.compute = None
    
    # Set a valid focused index
    df.set_index(0)
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None
    assert result is None


def test_get_compute_index_with_empty_compute():
    """Test that get_compute_index returns None when compute has no operations."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute with empty operations
    df.compute = Compute({})
    
    # Set a valid focused index
    df.set_index(0)
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None because no compute operations are defined
    assert result is None


def test_get_compute_index_with_different_focused_indices():
    """Test that get_compute_index returns the correct focused index for different values."""
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Test with first index
    df.set_index(0)
    result = df.get_compute_index(df.index)
    assert result == 0
    
    # Test with second index
    df.set_index(1)
    result = df.get_compute_index(df.index)
    assert result == 1
    
    # Test with third index
    df.set_index(2)
    result = df.get_compute_index(df.index)
    assert result == 2


def test_get_compute_index_with_string_indices():
    """Test that get_compute_index works with string indices."""
    # Create a CustomDataFrame with string indices
    df = lynguine.assess.data.CustomDataFrame(
        pd.DataFrame({
            'value': [10, 20, 30]
        }, index=['a', 'b', 'c'])
    )
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Set focused index to 'b'
    df.set_index('b')
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return 'b'
    assert result == 'b'


def test_get_compute_index_empty_dataframe():
    """Test that get_compute_index handles empty dataframes gracefully."""
    # Create an empty CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({})
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return None
    assert result is None


def test_get_compute_index_integration_scenario():
    """
    Integration test simulating the actual usage pattern in referia's compute_onchange().
    
    This tests the full pattern:
    1. Check if Index exists (has any indices)
    2. Validate focused index is valid for compute
    3. Only proceed if validation passes
    """
    # Create a CustomDataFrame simulating real usage
    df = lynguine.assess.data.CustomDataFrame({
        'title': ['Doc 1', 'Doc 2', 'Doc 3'],
        'score': [0, 0, 0],
        'modified': [None, None, None]
    })
    
    # Set up compute operations (simulating timestamp updates)
    df.compute = Compute({
        'compute': [
            {'field': 'modified', 'function': 'now'}
        ]
    })
    
    # Simulate the pattern from review.py compute_onchange()
    if df.index is not None:  # Check: Does Index exist?
        compute_index = df.get_compute_index(df.index)  # Validate: Is focused index valid?
        if compute_index is not None:  # Only proceed if validated
            # This is where run_onchange would be called
            assert compute_index in df.index
            assert df.compute is not None
            # Success - validation passed and we have a valid compute_index
    
    # Test with different focused indices
    for idx in df.index:
        df.set_index(idx)
        compute_index = df.get_compute_index(df.index)
        assert compute_index == idx


def test_get_compute_index_prevents_stale_index_error():
    """
    Test that get_compute_index prevents errors from stale indices.
    
    This simulates the bug scenario where an index might have been removed
    but is still set as the focused index.
    """
    # Create a CustomDataFrame
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Set focused index
    df.set_index(0)
    
    # Simulate the focused index becoming stale (set to something not in Index)
    df._index = 999
    
    # This should NOT raise an error - it should return None
    result = df.get_compute_index(df.index)
    assert result is None
    
    # Verify we can detect this condition before calling run_onchange
    if result is None:
        # Would skip run_onchange, preventing error
        pass
    else:
        # Would call run_onchange
        pytest.fail("Should have returned None for stale index")


def test_get_compute_index_with_series_type_dataframe():
    """Test get_compute_index with series-type dataframes (multiple rows per index)."""
    # Create a series-type CustomDataFrame with duplicate indices
    df = lynguine.assess.data.CustomDataFrame(
        pd.DataFrame({
            'subindex': [1, 2, 3, 4],
            'value': [10, 20, 30, 40]
        }, index=['a', 'a', 'b', 'b']),
        colspecs={'series': ['subindex', 'value']}
    )
    
    # Set up compute operations
    df.compute = Compute({'compute': [{'field': 'value', 'function': 'sum'}]})
    
    # Set focused index to 'a'
    df.set_index('a')
    
    # Call get_compute_index
    result = df.get_compute_index(df.index)
    
    # Should return 'a' (the focused index value, not the full multi-index)
    assert result == 'a'

