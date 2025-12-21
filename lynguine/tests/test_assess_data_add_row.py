import pytest
import pandas as pd
import numpy as np
from lynguine.assess.data import CustomDataFrame

@pytest.fixture
def sample_custom_df():
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}, index=['x', 'y', 'z'])
    cdf = CustomDataFrame(df, colspecs = {'input': ['A', 'B']})
    cdf.augment_with_df(pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]}, index=['x', 'y', 'z']), 
                        colspecs = {'output': ['C', 'D']})
    cdf.augment_with_df(pd.DataFrame({'E': [13, 14, 15, 16], 'F': [17, 18, 19, 20]}, index=['x', 'y', 'z', 'x']),
                        colspecs = {'series': ['E', 'F']})
    cdf.augment_with_df(pd.DataFrame({'G': [21, 21, 21, 21], 'H': [22, 22, 22, 22]}, index=['x', 'y', 'z', 'x']), 
                        colspecs = {'parameters': ['G', 'H']})
    
    return cdf

def test_add_row_to_output(sample_custom_df):
    sample_custom_df.set_column('C')
    sample_custom_df.add_row('w', values={'C': 100, 'D': 200})
    assert 'w' in sample_custom_df._d['output'].index
    assert sample_custom_df._d['output'].loc['w', 'C'] == 100
    assert sample_custom_df._d['output'].loc['w', 'D'] == 200

def test_add_row_to_series(sample_custom_df):
    sample_custom_df.set_column('E')
    sample_custom_df.add_row('w', values={'E': 300, 'F': 400})
    assert 'w' in sample_custom_df._d['series'].index
    assert sample_custom_df._d['series'].loc['w', 'E'] == 300
    assert sample_custom_df._d['series'].loc['w', 'F'] == 400

def test_add_row_to_series_existing_index(sample_custom_df):
    sample_custom_df.set_column('E')
    sample_custom_df.add_row('x', values={'E': 500, 'F': 600})
    assert len(sample_custom_df._d['series'][sample_custom_df._d['series'].index == 'x']) == 3
    assert 500 in sample_custom_df._d['series'].loc['x', 'E'].values
    assert 600 in sample_custom_df._d['series'].loc['x', 'F'].values

def test_add_row_to_input_raises_error(sample_custom_df):
    sample_custom_df.set_column('A')
    with pytest.raises(ValueError, match="Cannot add row to input type"):
        sample_custom_df.add_row('w')

def test_add_row_to_parameters_raises_error(sample_custom_df):
    sample_custom_df.set_column('G')
    with pytest.raises(ValueError, match="Cannot add row to parameters type"):
        sample_custom_df.add_row('w')

def test_add_row_existing_index_non_series_raises_error(sample_custom_df):
    sample_custom_df.set_column('C')
    with pytest.raises(ValueError, match="Index \"x\" already exists"):
        sample_custom_df.add_row('x')

def test_add_row_without_values(sample_custom_df):
    sample_custom_df.set_column('C')
    sample_custom_df.add_row('w')
    assert 'w' in sample_custom_df._d['output'].index
    assert pd.isna(sample_custom_df._d['output'].loc['w', 'C'])
    assert pd.isna(sample_custom_df._d['output'].loc['w', 'D'])

def test_add_row_partial_values(sample_custom_df):
    sample_custom_df.set_column('C')
    sample_custom_df.add_row('w', values={'C': 100})
    assert 'w' in sample_custom_df._d['output'].index
    assert sample_custom_df._d['output'].loc['w', 'C'] == 100
    assert pd.isna(sample_custom_df._d['output'].loc['w', 'D'])

def test_add_row_invalid_column_raises_error(sample_custom_df):
    with pytest.raises(KeyError, match="Attempting to add column \"Z\" as a set request has been given to non existent column."):
        sample_custom_df.set_column('Z')  # Z is not a valid column
    with pytest.raises(ValueError, match="Cannot add row to input type \"input\"."):
        sample_custom_df.add_row('w')