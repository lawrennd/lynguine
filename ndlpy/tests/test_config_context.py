import os
import io
import pytest
import yaml
import ndlpy

from ndlpy.config.context import Context

# Sample data that might be in your YAML files
machine_yaml_content = """
logging:
  level: INFO
  filename: machine_log.log
"""

defaults_yaml_content = """
logging:
  level: ERROR
  filename: default_log.log
"""

def mock_yaml_open(monkeypatch, file_content, file_path):
    # Mock open function to return specific file content
    class MockOpen:
        def __init__(self, path, mode='r', *args, **kwargs):
            assert path in file_path

        def __enter__(self):
            return io.StringIO(file_content)

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("builtins.open", MockOpen)

dirname = os.path.dirname(ndlpy.config.context.__file__)
filepaths = [
    os.path.join(dirname, "machine.yml"),
    os.path.join(dirname, "defaults.yml"),
]
    
def test_machine_yaml(monkeypatch):
    mock_yaml_open(monkeypatch, machine_yaml_content, filepaths)
    config = Context()
    assert config["logging"]["level"] == "INFO"
    assert config["logging"]["filename"] == "machine_log.log"

def test_defaults_yaml(monkeypatch):
    mock_yaml_open(monkeypatch, defaults_yaml_content, filepaths)
    config = Context()
    assert config["logging"]["level"] == "ERROR"
    assert config["logging"]["filename"] == "default_log.log"


