import pytest
import os

from datetime import datetime
from ndlpy.util.misc import (
    reorder_dictionary,
    extract_full_filename,  extract_root_directory, extract_file_type, extract_abs_filename, camel_capitalize,
    remove_nan, is_valid_var, to_valid_var, to_camel_case, sub_path_environment, get_path_env,
    get_url_file
)

# Sample data for testing
sample_details = {
    "directory": "/path/to/dir",
    "filename": "file.txt"
}



def test_reorder_dictionary_basic():
    dictionary = {'B': 2, 'A': 1, 'C': 3}
    order = ['A', 'B']
    reordered_dict = reorder_dictionary(dictionary, order)
    expected_keys = ['A', 'B', 'C']
    assert list(reordered_dict.keys()) == expected_keys

def test_reorder_dictionary_with_extra_keys_in_order():
    dictionary = {'B': 2, 'A': 1}
    order = ['A', 'C', 'B']  # 'C' is not in the dictionary
    reordered_dict = reorder_dictionary(dictionary, order)
    expected_keys = ['A', 'B']
    assert list(reordered_dict.keys()) == expected_keys

def test_reorder_dictionary_with_no_order():
    dictionary = {'B': 2, 'A': 1}
    order = []
    reordered_dict = reorder_dictionary(dictionary, order)
    expected_keys = ['A', 'B']  # Sorted remaining keys
    assert list(reordered_dict.keys()) == expected_keys

def test_reorder_dictionary_without_sorting_remaining():
    dictionary = {'C': 3, 'B': 2, 'A': 1}
    order = ['B']
    reordered_dict = reorder_dictionary(dictionary, order, sort_remaining=False)
    expected_keys = ['B', 'C', 'A']  # 'C' and 'A' retain their original order
    assert list(reordered_dict.keys()) == expected_keys

def test_reorder_dictionary_all_keys_ordered():
    dictionary = {'C': 3, 'B': 2, 'A': 1}
    order = ['B', 'A', 'C']
    reordered_dict = reorder_dictionary(dictionary, order)
    expected_keys = ['B', 'A', 'C']
    assert list(reordered_dict.keys()) == expected_keys


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
    assert root == "${HOME}"
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

# Testing is_valid_var
def test_valid_var_names():
    assert is_valid_var("valid_var_name")
    assert is_valid_var("_alsoValid123")
    assert is_valid_var("__name__")
    assert is_valid_var("validVarName")
    assert is_valid_var("validVarName123")
    
def test_invalid_var_names():
    assert not is_valid_var("1invalid")
    assert not is_valid_var("for")  # 'for' is a keyword
    assert not is_valid_var("invalid-var")
    assert not is_valid_var("invalid var")
    assert not is_valid_var("")

def test_non_string_input():
    assert not is_valid_var(123)
    assert not is_valid_var(12.34)
    assert not is_valid_var(["list", "is", "not", "a", "string"])
    assert not is_valid_var({"dict": "is not a string"})
    assert not is_valid_var(None)
    assert not is_valid_var(True)

def test_unicode_var_names():
    assert is_valid_var("变量")  # Chinese characters
    assert is_valid_var("переменная")  # Cyrillic characters

    
# Testing to_valid_var
@pytest.mark.parametrize("variable, expected", [
    ("Invalid Variable", "invalid_variable"),
    ("123numeric", "_123numeric"),
    ("with-hyphen", "with_hyphen")
])
def test_to_valid_var(variable, expected):
    assert to_valid_var(variable) == expected

def test_scalars_to_valid_var():
    assert to_valid_var(123) == "n123"
    assert to_valid_var(-123) == "neg123"
    assert to_valid_var(12.34) == "n12p34"
    assert to_valid_var(-12.34) == "neg12p34"

def test_string_to_valid_var():
    assert to_valid_var("validName") == "validname"
    assert to_valid_var("Invalid-Name") == "invalid_name"
    assert to_valid_var("123invalid") == "_123invalid"
    assert to_valid_var("name with space") == "name_with_space"
    assert to_valid_var("for") == "for_"  # Python keyword

def test_non_string_non_scalar_input():
    with pytest.raises(TypeError):
        to_valid_var(["not", "a", "string"])
    with pytest.raises(TypeError):
        to_valid_var({"not": "a string"})

def test_empty_and_special_char_strings():
    assert to_valid_var("") == "_"
    assert to_valid_var("@#$%^&*()") == "_________"

def test_unicode_strings():
    assert to_valid_var("变量") == "变量"  # Unicode characters
    assert to_valid_var("переменная") == "переменная"  # Cyrillic characters

# Testing to_camel_case
def test_camel_capitalize():
    assert camel_capitalize("test") == "Test"
    assert camel_capitalize("TEST") == "TEST"  # Uppercase stays uppercase
    assert camel_capitalize("tESt") == "Test"
    assert camel_capitalize("") == ""  # Empty string handling

def test_to_camel_case_with_strings():
    assert to_camel_case("hello world") == "helloWorld"
    assert to_camel_case("hello-world") == "helloWorld"
    assert to_camel_case("hello_world") == "helloWorld"
    assert to_camel_case("Hello world") == "helloWorld"
    assert to_camel_case("hello/World") == "helloOrWorld"
    assert to_camel_case("hello@world") == "helloAtWorld"
    assert to_camel_case("HELLO WORLD") == "helloWORLD"  # Preserving uppercase words

def test_to_camel_case_with_scalars():
    assert to_camel_case(123) == "n123"
    assert to_camel_case(-123.45) == "neg123p45"

def test_to_camel_case_with_edge_cases():
    with pytest.raises(ValueError):
        to_camel_case("")
    with pytest.raises(TypeError):
        to_camel_case(["not", "a", "string"])

@pytest.mark.parametrize("text, expected", [
    ("hello world", "helloWorld"),
    ("HELLO WORLD", "helloWORLD"),
    ("Camel case", "camelCase"),
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
