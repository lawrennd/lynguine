import pytest
import os
import ndlpy
from ndlpy.util.liquid import load_template_env

def test_load_template_env_default(mocker):
    """
    Test the load_template_env function with default parameters.
    """
    custom_dir = "/custom/path/to/templates"
    mock_env = mocker.patch('liquid.Environment')

    mock_os_path_join = mocker.patch('os.path.join', return_value="cat")
    env = load_template_env()
    mock_os_path_join.assert_called_once_with(os.path.dirname(ndlpy.__file__), "templates")
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
