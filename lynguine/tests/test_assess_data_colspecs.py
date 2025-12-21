import pytest
import pandas as pd
from lynguine.assess.data import CustomDataFrame 

@pytest.fixture
def sample_df():
    data = pd.DataFrame({
        'A': [1, 2, 3, 3],
        'B': [4, 5, 6, 6],
        'C': [7, 8, 9, 9],
        'D': [10, 11, 12, 13],
    }, index = [0, 1, 2, 2])
    
    colspecs = {
        'input': ['A', 'B'],
        'output': ['C'],
        'series': ['D'],
    }

    return CustomDataFrame(data, colspecs=colspecs)

def test_getitem_respects_colspecs(sample_df):
    assert isinstance(sample_df['D'], pd.Series)
    assert len(sample_df['D']) == 4

def test_setitem_updates_colspecs(sample_df):
    sample_df['E'] = pd.Series([14, 15, 16, 16], index=[0, 1, 2, 2])
    assert 'E' in sample_df._colspecs['cacheseries']
    sample_df['F'] = pd.Series([14, 15, 16], index=[0, 1, 2])
    assert 'F' in sample_df._colspecs['cache']
    
def test_merge_preserves_colspecs():
    df1 = CustomDataFrame({'A': [1, 2], 'B': [3, 4]}, colspecs={'input': ['A'], 'output': ['B']})
    df2 = CustomDataFrame({'B': [3, 4], 'C': [5, 6]}, colspecs={'input': ['B'], 'output': ['C']})
    merged = df1.merge(df2, on='B')
    assert set(merged._colspecs['input']) == {'A'}
    assert set(merged._colspecs['output']) == {'B', 'C'}

def test_mathematical_operations_preserve_colspecs(sample_df):
    result = sample_df + 1
    assert result._colspecs == sample_df._colspecs


def test_to_pandas_includes_series_data(sample_df):
    pd_df = sample_df.to_pandas()
    assert 'D' in pd_df.columns
    assert len(pd_df['D']) == 4


def test_apply_respects_colspecs(sample_df):
    result = sample_df.apply(lambda x: x * 2 if x.name != 'D' else x)
    assert isinstance(result['D'], pd.Series)
    assert len(result['D']) == 4

