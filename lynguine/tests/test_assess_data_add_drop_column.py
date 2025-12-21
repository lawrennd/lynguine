"""
Tests for CustomDataFrame.add_column() and drop_column() methods.
"""
import pytest
import pandas as pd
import numpy as np
from lynguine.assess.data import CustomDataFrame


def test_add_column_basic():
    """Test adding a basic column with default colspec."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    
    # Add a column with default colspec='cache'
    df.add_column('c', [7, 8, 9])
    
    assert 'c' in df.columns
    assert list(df['c']) == [7, 8, 9]
    assert df.get_column_type('c') == 'cache'


def test_add_column_with_series():
    """Test adding a column using a pandas Series."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}, index=['x', 'y', 'z']))
    
    new_data = pd.Series([10, 20, 30], index=['x', 'y', 'z'])
    df.add_column('b', new_data)
    
    assert 'b' in df.columns
    assert df['b'].tolist() == [10, 20, 30]


def test_add_column_with_colspec():
    """Test adding a column with a specific colspec."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    # Add column as 'output' type
    df.add_column('result', [10, 20, 30], colspec='output')
    
    assert 'result' in df.columns
    assert df.get_column_type('result') == 'output'
    assert df['result'].tolist() == [10, 20, 30]


def test_add_column_existing_raises_error():
    """Test that adding an existing column raises ValueError."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    with pytest.raises(ValueError, match="Column 'a' already exists"):
        df.add_column('a', [4, 5, 6])


def test_add_column_invalid_colspec_raises_error():
    """Test that invalid colspec raises ValueError."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    with pytest.raises(ValueError, match="Invalid colspec 'invalid_type'"):
        df.add_column('b', [4, 5, 6], colspec='invalid_type')


def test_add_column_with_array():
    """Test adding a column with a numpy array."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    df.add_column('b', np.array([10, 20, 30]))
    
    assert 'b' in df.columns
    assert df['b'].tolist() == [10, 20, 30]


def test_drop_column_basic():
    """Test dropping a basic column."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9]}))
    
    df.drop_column('b')
    
    assert 'b' not in df.columns
    assert 'a' in df.columns
    assert 'c' in df.columns


def test_drop_column_nonexistent_raises_error():
    """Test that dropping a non-existent column raises KeyError."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    with pytest.raises(KeyError, match="Column 'nonexistent' not found"):
        df.drop_column('nonexistent')


def test_drop_column_from_colspecs():
    """Test that dropping a column removes it from colspecs."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    df.add_column('b', [4, 5, 6], colspec='output')
    
    # Verify it's in output colspec
    assert 'b' in df._colspecs['output']
    
    # Drop it
    df.drop_column('b')
    
    # Verify it's removed from colspecs
    assert 'b' not in df._colspecs.get('output', [])
    assert 'b' not in df.columns


def test_add_then_drop_column():
    """Test adding and then dropping a column."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    # Add
    df.add_column('temp', [10, 20, 30])
    assert 'temp' in df.columns
    
    # Drop
    df.drop_column('temp')
    assert 'temp' not in df.columns


def test_add_column_different_colspecs():
    """Test adding columns to different colspec types."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}))
    
    # Add to cache (default)
    df.add_column('cache_col', [1, 2, 3])
    assert df.get_column_type('cache_col') == 'cache'
    
    # Add to output
    df.add_column('output_col', [4, 5, 6], colspec='output')
    assert df.get_column_type('output_col') == 'output'
    
    # Add to parameters
    df.add_column('param_col', [7, 8, 9], colspec='parameters')
    assert df.get_column_type('param_col') == 'parameters'


def test_drop_column_updates_column_list():
    """Test that dropping a column updates the columns list."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    
    original_columns = set(df.columns)
    assert original_columns == {'a', 'b'}
    
    df.drop_column('a')
    
    updated_columns = set(df.columns)
    assert updated_columns == {'b'}


def test_add_column_with_mismatched_index():
    """Test adding a column with a Series that has a different index."""
    df = CustomDataFrame(data=pd.DataFrame({'a': [1, 2, 3]}, index=[0, 1, 2]))
    
    # Series with different index - pandas will align by index
    new_data = pd.Series([10, 20, 30], index=[0, 1, 2])
    df.add_column('b', new_data)
    
    assert 'b' in df.columns
    # Values should align by index
    assert df['b'].tolist() == [10, 20, 30]

