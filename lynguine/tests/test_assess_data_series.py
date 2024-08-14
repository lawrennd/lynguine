import pytest
import pandas as pd
import numpy as np
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

@pytest.fixture
def series_dataframe():

    data = {
        'date': ['2023-01-01', '2023-01-02'],
        'day': ['Sunday', 'Monday'],
    }
    
    df = pd.DataFrame(data)    
    df['date'] = pd.to_datetime(df['date'])
    index = pd.Index(df["date"], name="date")
    df.set_index(index, inplace=True)
    del df["date"]

    cdf = CustomDataFrame(df, colspecs ={
            'input': ['day']
        }
    )

    data = {
        'date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02'],
        'product': ['A', 'B', 'A', 'B'],
        'sales': [100, 150, 120, 180],
        'stock': [500, 600, 480, 570]
    }
    
    df_series = pd.DataFrame(data)    
    df_series['date'] = pd.to_datetime(df_series['date'])
    index = pd.Index(df_series["date"], name="date")
    df_series.set_index(index, inplace=True)
    
    cdf.augment_with_df(df_series, colspecs={"series" : ['product', 'sales', 'stock']})
    cdf.set_selector('product')
    return cdf


def test_series_creation(series_dataframe):
    assert isinstance(series_dataframe, CustomDataFrame)
    assert series_dataframe.shape == (2, 4) # TK this is two rows because two unique indices, could be four rows for all different rows ....
    assert series_dataframe.index.name == 'date'
    assert series_dataframe.get_selector() == 'product'

#def test_duplicate_indices(series_dataframe):
    #assert series_dataframe.index.duplicated().any() # TK as it standas, this is not true, the index is unique but just not for the _d["series"] part
#    assert len(series_dataframe.index.unique()) < len(series_dataframe)

def test_get_selectors(series_dataframe):
    selectors = series_dataframe.get_selectors()
    assert 'product' in selectors
    assert 'sales' in selectors
    assert 'stock' in selectors

def test_get_subindices(series_dataframe):
    series_dataframe.set_index(pd.Timestamp('2023-01-01'))
    subindices = series_dataframe.get_subindices()
    assert len(subindices) == 2
    assert 'A' in subindices
    assert 'B' in subindices

def test_get_value_series(series_dataframe):
    series_dataframe.set_index(pd.Timestamp('2023-01-01'))
    series_dataframe.set_column('sales')
    series_dataframe.set_subindex('A')
    assert series_dataframe.get_value() == 100

    series_dataframe.set_subindex('B')
    assert series_dataframe.get_value() == 150

def test_set_value_series(series_dataframe):
    series_dataframe.set_index(pd.Timestamp('2023-01-01'))
    series_dataframe.set_column('sales')
    series_dataframe.set_subindex('A')
    series_dataframe.set_value(110)
    assert series_dataframe.get_value() == 110

def test_get_subseries(series_dataframe):
    series_dataframe.set_index(pd.Timestamp('2023-01-01'))
    subseries = series_dataframe.get_subseries()
    assert isinstance(subseries, pd.DataFrame)
    assert subseries.shape[0] == 2  # Two rows associated with first Jan
    assert set(subseries.columns) == {'product', 'sales', 'stock'}

def test_merge_with_series(series_dataframe):
    other_data = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02'],
        'temperature': [20, 22]
    })
    other_data['date'] = pd.to_datetime(other_data['date'])
    # Set index of data frame as date
    other_data.set_index('date', inplace=True)
    
    other_df = CustomDataFrame(other_data, colspecs={'input': ['temperature']})
    
    merged = series_dataframe.merge(other_df, left_index=True, right_index=True)
    assert isinstance(merged, CustomDataFrame)
    assert merged.shape == (2, 5)  # Original columns plus temperature TK THis is two rows because two unique indices, could be four rows for all different rows ....
    assert 'temperature' in merged.columns

def test_to_pandas_conversion(series_dataframe):
    pandas_df = series_dataframe.to_pandas()
    assert isinstance(pandas_df, pd.DataFrame)
    assert pandas_df.shape[1] == series_dataframe.shape[1]
    assert len(set(pandas_df.index)) == series_dataframe.shape[0]
    assert pandas_df.index.name == 'date'

def test_series_operations(series_dataframe):
    # Test a simple operation on a series column
    result = series_dataframe['sales'] * 2
    assert isinstance(result, pd.Series)
    assert (result == series_dataframe['sales'].values * 2).all()

def test_groupby_with_series(series_dataframe):
    grouped = series_dataframe.groupby('product')['sales'].sum()
    assert isinstance(grouped, pd.Series)
    assert grouped['A'] == 220
    assert grouped['B'] == 330

# Test error handling
def test_invalid_subindex(series_dataframe):
    series_dataframe.set_index(pd.Timestamp('2023-01-01'))
    series_dataframe.set_column('sales')
    with pytest.raises(KeyError):
        series_dataframe.set_subindex('C')  # 'C' is not a valid subindex

def test_non_series_column_access(series_dataframe):
    series_dataframe.set_selector('day')
    with pytest.raises(KeyError):
        series_dataframe.set_subindex('A')  # 'day' is not a series column

def test_from_pandas_sets_colspecs():
    pd_df = pd.DataFrame(
        {
            'A': [1, 2, 3, 3],
            'B': [4, 5, 6, 6]
        },
        index=[0, 1, 2, 2]
    )
    custom_df = CustomDataFrame.from_pandas(pd_df, colspecs={'input': ['A'], 'series': ['B']})
    assert custom_df._colspecs == {'input': ['A'], 'series': ['B']}
        
#def test_filter_preserves_colspecs(sample_df):
#    filtered = sample_df[sample_df['A'] > 1]
#    # All colspecs should now be "cache"
#    for colspec in filtered._colspecs.values():
#        assert all([col == 'cache' for col in colspec])
        
