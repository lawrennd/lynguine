"""
Tests for CustomDataFrame._finalize_df method, specifically for adding missing columns
without causing DataFrame fragmentation.

This addresses the performance warning:
PerformanceWarning: DataFrame is highly fragmented. This is usually the result 
of calling `frame.insert` many times, which has poor performance.
"""

import pytest
import pandas as pd
import lynguine.assess.data
import lynguine.config.interface
import warnings


def test_finalize_df_adds_single_missing_column():
    """Test that _finalize_df adds a single missing column."""
    # Create a CustomDataFrame with some initial columns
    df = lynguine.assess.data.CustomDataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    
    # Create an interface that specifies an additional column
    interface = lynguine.config.interface.Interface({
        'index': 'a',
        'columns': ['a', 'b', 'c']
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe
    result = df._finalize_df(df, interface)
    
    # Check that the missing column was added
    assert 'c' in result.columns
    assert result['c'].isna().all()  # Should be None/NaN values
    assert len(result.columns) == 2  # 'b' and 'c' (after 'a' becomes index)


def test_finalize_df_adds_multiple_missing_columns():
    """Test that _finalize_df adds multiple missing columns efficiently."""
    # Create a CustomDataFrame with some initial columns
    df = lynguine.assess.data.CustomDataFrame({'id': [1, 2, 3], 'a': [4, 5, 6]})
    
    # Create an interface that specifies multiple additional columns
    interface = lynguine.config.interface.Interface({
        'index': 'id',
        'columns': ['id', 'a', 'b', 'c', 'd', 'e']
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe - this should not produce fragmentation warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = df._finalize_df(df, interface)
        
        # Check that no performance warnings were raised
        perf_warnings = [warning for warning in w 
                        if issubclass(warning.category, pd.errors.PerformanceWarning)]
        assert len(perf_warnings) == 0, f"Performance warning raised: {perf_warnings}"
    
    # Check that all missing columns were added
    assert 'b' in result.columns
    assert 'c' in result.columns
    assert 'd' in result.columns
    assert 'e' in result.columns
    
    # Check that they all have None/NaN values
    assert result['b'].isna().all()
    assert result['c'].isna().all()
    assert result['d'].isna().all()
    assert result['e'].isna().all()
    
    # Check that existing data is preserved
    assert list(result['a']) == [4, 5, 6]


def test_finalize_df_no_missing_columns():
    """Test that _finalize_df works when no columns are missing."""
    # Create a CustomDataFrame with all required columns
    df = lynguine.assess.data.CustomDataFrame({
        'id': [1, 2, 3],
        'a': [4, 5, 6],
        'b': [7, 8, 9]
    })
    
    # Create an interface with no missing columns
    interface = lynguine.config.interface.Interface({
        'index': 'id',
        'columns': ['id', 'a', 'b']
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe
    result = df._finalize_df(df, interface)
    
    # Check that all columns are still present
    assert 'a' in result.columns
    assert 'b' in result.columns
    assert list(result['a']) == [4, 5, 6]
    assert list(result['b']) == [7, 8, 9]


def test_finalize_df_preserves_dataframe_integrity():
    """Test that adding missing columns preserves DataFrame index and data integrity."""
    # Create a CustomDataFrame with a specific index
    df = lynguine.assess.data.CustomDataFrame({
        'id': ['x', 'y', 'z'],
        'value': [100, 200, 300]
    })
    
    # Create an interface that adds several columns
    interface = lynguine.config.interface.Interface({
        'index': 'id',
        'columns': ['id', 'value', 'col1', 'col2', 'col3']
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe
    result = df._finalize_df(df, interface)
    
    # Check index integrity
    assert list(result.index) == ['x', 'y', 'z']
    assert result.index.name == 'id'
    
    # Check that existing data is preserved
    assert list(result['value']) == [100, 200, 300]
    
    # Check that new columns have the correct index
    assert len(result['col1']) == 3
    assert len(result['col2']) == 3
    assert len(result['col3']) == 3


def test_finalize_df_with_large_number_of_missing_columns():
    """Test that adding many missing columns at once doesn't cause fragmentation."""
    # Create a CustomDataFrame with minimal columns
    df = lynguine.assess.data.CustomDataFrame({'id': range(10), 'a': range(10, 20)})
    
    # Create an interface that specifies many additional columns
    column_names = ['id', 'a'] + [f'col_{i}' for i in range(20)]
    interface = lynguine.config.interface.Interface({
        'index': 'id',
        'columns': column_names
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe - should handle many columns efficiently
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = df._finalize_df(df, interface)
        
        # Check that no performance warnings were raised
        perf_warnings = [warning for warning in w 
                        if issubclass(warning.category, pd.errors.PerformanceWarning)]
        assert len(perf_warnings) == 0, f"Performance warning raised with {len(column_names)} columns"
    
    # Check that all columns were added
    for i in range(20):
        col_name = f'col_{i}'
        assert col_name in result.columns
        assert result[col_name].isna().all()


def test_finalize_df_without_columns_key():
    """Test that _finalize_df works when interface doesn't have 'columns' key."""
    df = lynguine.assess.data.CustomDataFrame({'id': [1, 2, 3], 'a': [4, 5, 6]})
    
    # Create an interface without 'columns' key
    interface = lynguine.config.interface.Interface({
        'index': 'id'
    }, directory=".", user_file="test.yml")
    
    # Finalize the dataframe - should not attempt to add columns
    result = df._finalize_df(df, interface)
    
    # Check that original columns are preserved
    assert 'a' in result.columns
    assert list(result['a']) == [4, 5, 6]

