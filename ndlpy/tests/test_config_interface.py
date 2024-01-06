import os
import pytest
from io import StringIO
from unittest.mock import patch
from ndlpy.config.interface import Interface  # Adjust the import as per your project structure

# Mocked content of YAML files


user_yaml_content = """
logging:
  level: DEBUG
  filename: user_log.log
"""

user_yaml_content_inherit = """
inherit:
  directory: .
  filename: parent_settings.yml
logging:
  level: DEBUG
  filename: user_log.log
"""

parent_yaml_content = """
logging:
  level: INFO
  filename: default_log.log
some_parent_setting: value_from_parent
"""

def mock_yaml_open(monkeypatch, file_content_map):
    def mock_open(filename, mode='r', *args, **kwargs):
        if filename in file_content_map:
            return StringIO(file_content_map[filename])
        raise FileNotFoundError(f"No mock data for file \"{filename}\"")

    monkeypatch.setattr("builtins.open", mock_open)

    # Mocking os.path.exists to simulate file presence
    def mock_exists(path):
        return path in file_content_map

    monkeypatch.setattr("os.path.exists", mock_exists)
    
def test_basic_interface(monkeypatch):
    mock_yaml_open(monkeypatch, {"./user_settings.yml": user_yaml_content})
    interface = Interface(user_file="user_settings.yml", directory=".")
    assert interface["logging"]["level"] == "DEBUG"
    assert interface["logging"]["filename"] == "user_log.log"

def test_inherited_interface(monkeypatch):
    file_content_map = {
        "./user_settings.yml": user_yaml_content_inherit,
        "./parent_settings.yml": parent_yaml_content
    }
    mock_yaml_open(monkeypatch, file_content_map)
    interface = Interface(user_file="user_settings.yml", directory=".")
    # Assuming inheritance is correctly implemented in your Interface class
    assert interface["logging"]["level"] == "DEBUG"  # Overridden in user settings
    assert interface["some_parent_setting"] == "value_from_parent"  # Inherited

def test_env_variable_expansion(monkeypatch):
    env_yaml_content = """
    path: $HOME/test
    """
    monkeypatch.setenv("HOME", "/home/user")
    mock_yaml_open(monkeypatch, {"./env_settings.yml": env_yaml_content})
    interface = Interface(user_file="env_settings.yml", directory=".")
    assert interface["path"] == "/home/user/test"

# Additional tests can be written to cover other scenarios and edge cases
