import pytest
import pandas as pd
from datetime import datetime

from ndlpy.util.dataframe import (
    reorder_dataframe,
    convert_datetime, convert_int, convert_string, convert_year_iso,
    addmonth, addyear, augmentmonth, augmentyear, augmentcurrency, fillna, ascending,
    descending, recent, current, former, onbool, columnis, columncontains

)


import pytest
import pandas as pd

def test_reorder_dataframe_basic():
    df = pd.DataFrame({
        'B': [1, 2, 3],
        'A': [4, 5, 6],
        'C': [7, 8, 9]
    })
    order = ['A', 'B']
    reordered_df = reorder_dataframe(df, order)
    expected_columns = ['A', 'B', 'C']
    assert list(reordered_df.columns) == expected_columns

def test_reorder_dataframe_with_extra_columns_in_order():
    df = pd.DataFrame({
        'B': [1, 2, 3],
        'A': [4, 5, 6]
    })
    order = ['A', 'C', 'B']  # 'C' is not in the DataFrame
    reordered_df = reorder_dataframe(df, order)
    expected_columns = ['A', 'B']
    assert list(reordered_df.columns) == expected_columns

def test_reorder_dataframe_with_no_order():
    df = pd.DataFrame({
        'B': [1, 2, 3],
        'A': [4, 5, 6]
    })
    order = []
    reordered_df = reorder_dataframe(df, order)
    expected_columns = ['A', 'B']
    assert list(reordered_df.columns) == expected_columns

def test_reorder_dataframe_with_all_columns_ordered():
    df = pd.DataFrame({
        'C': [1, 2, 3],
        'B': [4, 5, 6],
        'A': [7, 8, 9]
    })
    order = ['B', 'A', 'C']
    reordered_df = reorder_dataframe(df, order)
    expected_columns = ['B', 'A', 'C']
    assert list(reordered_df.columns) == expected_columns


# Testing convert_datetime
def test_convert_datetime():
    df = pd.DataFrame({"date": ["2020-01-01", "2020-01-02"]})
    df = convert_datetime(df, "date")
    assert pd.api.types.is_datetime64_any_dtype(df["date"])

# Testing convert_int
def test_convert_int():
    df = pd.DataFrame({"number": ["1", "2", None]})
    df = convert_int(df, "number")
    assert pd.api.types.is_integer_dtype(df["number"])
    assert df["number"].isna().sum() == 1

# Testing convert_string
def test_convert_string():
    df = pd.DataFrame({"text": [123, None]})
    df = convert_string(df, "text")
    assert all(isinstance(x, str) or pd.isna(x) for x in df["text"])

# Testing convert_year_iso
def test_convert_year_iso():
    df = pd.DataFrame({"year": [2000, "2001", datetime(2002, 1, 1)]})
    df = convert_year_iso(df)
    assert all(isinstance(x, datetime) for x in df["year"])

# Testing addmonth and addyear
def test_add_month_year():
    df = pd.DataFrame({"date": [datetime(2020, 1, 1), datetime(2020, 2, 1)]})
    df['month'] = addmonth(df, "date")
    df['year'] = addyear(df, "date")
    assert df['month'].tolist() == ['January', 'February']
    assert df['year'].tolist() == [2020, 2020]

# Testing augmentmonth and augmentyear
def test_augment_month_year():
    df = pd.DataFrame({"date": [datetime(2020, 1, 1), None], "month": [None, "February"], "year": [None, 2021]})
    df['month'] = augmentmonth(df, "month", "date")
    df['year'] = augmentyear(df, "year", "date")
    assert df['month'].tolist() == ['January', 'February']
    assert df['year'].tolist() == [2020, 2021]

# Testing augmentcurrency
def test_augmentcurrency():
    df = pd.DataFrame({"amount": [1234.56, 7890.123]})
    df['formatted'] = augmentcurrency(df, "amount", 2)
    assert df['formatted'].tolist() == ['1,234.56', '7,890.12']

# Testing fillna
def test_fillna():
    df = pd.DataFrame({"col": [None, 1, 2]})
    df['col'] = fillna(df, "col", 0)
    assert df['col'].tolist() == [0, 1, 2]

# Testing ascending and descending
def test_sorting():
    df = pd.DataFrame({"number": [3, 1, 2]})
    df_asc = ascending(df, "number")
    df_desc = descending(df, "number")
    assert df_asc['number'].tolist() == [1, 2, 3]
    assert df_desc['number'].tolist() == [3, 2, 1]

# Testing recent
def test_recent():
    df = pd.DataFrame({"year": [2000, 2020]})
    current_year = datetime.now().year
    df_recent = recent(df, since_year=2019)
    assert df_recent.tolist() == [False, True]

# Testing current
def test_current():
    now = datetime.now()
    df = pd.DataFrame({"start": [now, now, None], "end": [now, now + pd.DateOffset(years=1), None], "current" : [None, None, True]})
    df_current = current(df, current="current", today=now)
    assert df_current.tolist() == [True, True, True]

# Testing former
def test_former():
    now = datetime.now()
    df = pd.DataFrame({"end": [now - pd.DateOffset(years=1), now]})
    df_former = former(df)
    assert df_former.tolist() == [True, False]

# Testing onbool
def test_onbool():
    df = pd.DataFrame({"flag": [True, False, True]})
    df_true = onbool(df, "flag")
    df_false = onbool(df, "flag", invert=True)
    assert df_true.tolist() == [True, False, True]
    assert df_false.tolist() == [False, True, False]

# Testing columnis
def test_columnis():
    df = pd.DataFrame({"col": ['a', 'b', 'c']})
    df_a = columnis(df, "col", 'a')
    assert df_a.tolist() == [True, False, False]

# Testing columncontains
def test_columncontains():
    df = pd.DataFrame({"col": [['a', 'b'], ['b', 'c'], ['c'], 'a', 'd', None]})
    df_contains_a = columncontains(df, "col", 'a')
    df_contains_b = columncontains(df, "col", 'b')
    assert df_contains_a.tolist() == [True, False, False, True, False, False]
    assert df_contains_b.tolist() == [True, True, False, False, False, False]
