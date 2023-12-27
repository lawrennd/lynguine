import pytest
import os
from datetime import datetime
from ndlpy.util import (
    extract_full_filename,  extract_root_directory, extract_file_type, extract_abs_filename, camel_capitalize,
    remove_nan, to_valid_var, to_camel_case, sub_path_environment, get_path_env,
    get_url_file
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
