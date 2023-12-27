import pytest
import pandas as pd
import os
from datetime import datetime
from ndlpy.util import (
    extract_full_filename,  extract_root_directory, extract_file_type, extract_abs_filename, camel_capitalize,
    remove_nan, to_valid_var, to_camel_case, sub_path_environment, get_path_env,
    get_url_file, convert_datetime, convert_int, convert_string, convert_year_iso,
    addmonth, addyear, augmentmonth, augmentyear, augmentcurrency, fillna, ascending,
    descending, recent, current, former, onbool, columnis, columncontains

)

# Sample data for testing
sample_details = {
    "directory": "/path/to/dir",
    "filename": "file.txt"
}

# Testing extract_full_filename
def test_extract_full_filename():
    expected = "/path/to/dir/file.txt"
    assert extract_full_filename(sample_details) == expected

# Testing extract_root_directory
@pytest.fixture
def setup_environment(monkeypatch):
    # Setting up mock environment variables for testing
    monkeypatch.setenv("TEST", "/mock/home")
    monkeypatch.setenv("HOME", "/mock/home")
    monkeypatch.setenv("USERPROFILE", "/mock/userprofile")
    monkeypatch.setenv("TEMP", "/mock/temp")
    monkeypatch.setenv("TMPDIR", "/mock/tmpdir")
    monkeypatch.setenv("TMP", "/mock/tmp")

def test_extract_root_directory(setup_environment):
    # Testing with a directory containing an environment variable
    directory = "$TEST/Documents"
    root, sub = extract_root_directory(directory)
    assert root == "$HOME"
    assert sub == "Documents"

    # Testing with a directory containing the current working directory
    cwd = os.getcwd()
    directory = os.path.join(cwd, "subdir")
    root, sub = extract_root_directory(directory)
    assert root == sub_path_environment(cwd)
    assert sub == "subdir"

    # Testing with None as input
    root, sub = extract_root_directory(None)
    assert root is None
    assert sub is None
    
# Testing extract_file_type
@pytest.mark.parametrize("filename, expected", [
    ("file.md", "markdown"),
    ("data.csv", "csv"),
    ("report.xlsx", "excel"),
    ("config.yaml", "yaml"),
    ("reference.bib", "bibtex"),
    ("document.docx", "docx"),
    ("unknown.file", ValueError)
])
def test_extract_file_type(filename, expected):
    if expected is ValueError:
        with pytest.raises(expected):
            extract_file_type(filename)
    else:
        assert extract_file_type(filename) == expected

# Testing extract_abs_filename
def test_extract_abs_filename():
    abs_path = os.path.abspath("/path/to/dir/file.txt")
    assert extract_abs_filename(sample_details) == abs_path

# Testing camel_capitalize
@pytest.mark.parametrize("input, expected", [
    ("text", "Text"),
    ("TEXT", "TEXT"),
    ("tExt", "Text")
])
def test_camel_capitalize(input, expected):
    assert camel_capitalize(input) == expected

# Testing remove_nan
def test_remove_nan():
    input_dict = {"a": None, "b": float('nan'), "c": 1, "d": {"da": None, "db": 2}}
    expected_dict = {"c": 1, "d": {"db": 2}}
    assert remove_nan(input_dict) == expected_dict

# Testing to_valid_var
@pytest.mark.parametrize("variable, expected", [
    ("Invalid Variable", "invalid_variable"),
    ("123numeric", "_123numeric"),
    ("with-hyphen", "with_hyphen")
])
def test_to_valid_var(variable, expected):
    assert to_valid_var(variable) == expected

# Testing to_camel_case
@pytest.mark.parametrize("text, expected", [
    ("hello world", "helloWorld"),
    ("HELLO WORLD", "HELLOWORLD"),
    ("Camel case", "CamelCase"),
    ("with/slash", "withOrSlash"),
    ("with@symbol", "withAtSymbol"),
    ("with-hyphen", "withHyphen"),
    ("123number", "123number"),
    ("", ValueError)
])
def test_to_camel_case(text, expected):
    if expected is ValueError:
        with pytest.raises(expected):
            to_camel_case(text)
    else:     
        assert to_camel_case(text) == expected

# Testing sub_path_environment
def test_sub_path_environment():
    # This test may vary depending on the environment it's run in
    path = "/home/user/path"
    env_var = "HOME"
    expected = path.replace(os.environ.get(env_var, ''), f"${env_var}")
    assert sub_path_environment(path) == expected

# Testing get_path_env
def test_get_path_env():
    # Similar to sub_path_environment, this is environment dependent
    current_path = os.getcwd()
    expected = sub_path_environment(current_path)
    assert get_path_env() == expected

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
