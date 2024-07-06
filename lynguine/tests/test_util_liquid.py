import pytest
import os
import lynguine
from lynguine.util.liquid import load_template_env, url_escape, markdownify, relative_url, absolute_url, to_i

def test_load_template_env_default(mocker):
    """
    Test the load_template_env function with default parameters.
    """
    custom_dir = "/custom/path/to/templates"
    mock_env = mocker.patch('liquid.Environment')

    mock_os_path_join = mocker.patch('os.path.join', return_value="cat")
    env = load_template_env()
    mock_os_path_join.assert_called_once_with(os.path.dirname(lynguine.__file__), "templates")
    mock_env.assert_called_once()
    assert env == mock_env.return_value

def test_load_template_env_custom_extension(mocker):
    """
    Test the load_template_env function with a custom extension.
    """
    custom_ext = ".html"
    mock_env = mocker.patch('liquid.Environment')
    env = load_template_env(ext=custom_ext)
    mock_env.assert_called_once()
    assert env == mock_env.return_value

def test_load_template_env_custom_directory(mocker):
    """
    Test the load_template_env function with a custom template directory.
    """
    custom_dir = "/custom/path/to/templates"
    mock_env = mocker.patch('liquid.Environment')

    env = load_template_env(template_dir=custom_dir)

    mock_env.assert_called_once()
    assert env == mock_env.return_value

def test_url_escape():
    assert url_escape("https://www.example.com/test?param=value") == "https%3A//www.example.com/test%3Fparam%3Dvalue"
    assert url_escape(" ") == "%20"
    with pytest.raises(ValueError):
        url_escape("\ud800")  # Unencodable character

def test_markdownify(mocker):
    # Mock the markdown2html function
    mocker.patch('lynguine.util.misc.markdown2html', return_value="<h1>Test</h1>")
    assert markdownify("# Test") == "<h1>Test</h1>"
    # Test for error handling
    mocker.patch('lynguine.util.misc.markdown2html', side_effect=Exception('mock error'))
    with pytest.raises(ValueError) as exc_info:
        markdownify("# Test")
    assert str(exc_info.value) == "Error converting markdown to HTML: mock error"
def test_relative_url():
    assert relative_url("test/notebook.ipynb") == "/notebooks/test/notebook.ipynb"
    assert relative_url("/test/notebook.ipynb") == "/notebooks/test/notebook.ipynb"

def test_absolute_url():
    assert absolute_url("test/notebook.ipynb") == "http://localhost:8888/notebooks/test/notebook.ipynb"
    assert absolute_url("/test/notebook.ipynb") == "http://localhost:8888/notebooks/test/notebook.ipynb"

def test_to_i():
    assert to_i("123") == 123
    assert to_i("123.45") == 123
    assert to_i("") == 0
    with pytest.raises(ValueError):
        to_i("abc")
    
