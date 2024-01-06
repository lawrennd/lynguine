import os
import pytest
from io import StringIO
from ndlpy.config.interface import Interface, _HConfig  # Adjust the import as per your project structure

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

parent2_yaml = """
key1: value1
key2: value2
"""
child2_yaml = """
key2: new_value2
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
    interface = Interface.from_file(user_file="user_settings.yml", directory=".")
    assert interface["logging"]["level"] == "DEBUG"
    assert interface["logging"]["filename"] == "user_log.log"

def test_inherited_interface(monkeypatch):
    file_content_map = {
        "./user_settings.yml": user_yaml_content_inherit,
        "./parent_settings.yml": parent_yaml_content
    }
    mock_yaml_open(monkeypatch, file_content_map)
    interface = Interface.from_file(user_file="user_settings.yml", directory=".")
    # Assuming inheritance is correctly implemented in your Interface class
    assert interface["logging"]["level"] == "DEBUG"  # Overridden in user settings
    assert interface["some_parent_setting"] == "value_from_parent"  # Inherited

def test_env_variable_expansion(monkeypatch):
    env_yaml_content = """
    path: $HOME/test
    """
    monkeypatch.setenv("HOME", "/home/user")
    mock_yaml_open(monkeypatch, {"./env_settings.yml": env_yaml_content})
    interface = Interface.from_file(user_file="env_settings.yml", directory=".")
    assert interface["path"] == "/home/user/test"


class MockConfig(_HConfig):
    def __init__(self, data=None, parent=None):
        self._data = data or {}
        self._parent = parent

@pytest.fixture
def mock_config():
    return MockConfig(data={'key1': 'value1'})

@pytest.fixture
def mock_interface(mocker):
    return Interface(data={'key3': 'value3'})

@pytest.fixture
def mock_interface2(monkeypatch):
    yaml_content = """
    key: value
    """
    mock_yaml_open(monkeypatch, {"./test.yml": yaml_content})
    return Interface.from_file(user_file="test.yml", directory=".")
    
def test_hconfig_initialization(mock_config):
    with pytest.raises(NotImplementedError):
        _HConfig()

def test_hconfig_getitem(mock_config):
    assert mock_config['key1'] == 'value1'
    with pytest.raises(KeyError):
        _ = mock_config['nonexistent_key']

def test_hconfig_setitem(mock_config):
    mock_config['key2'] = 'value2'
    assert mock_config._data['key2'] == 'value2'

def test_hconfig_delitem(mock_config):
    del mock_config['key1']
    assert 'key1' not in mock_config._data
    with pytest.raises(KeyError):
        del mock_config['nonexistent_key']

def test_hconfig_iter(mock_config):
    mock_config._data = {'key1': 'value1', 'key2': 'value2'}
    keys = list(mock_config)
    assert set(keys) == {'key1', 'key2'}

def test_hconfig_len(mock_config):
    mock_config._data = {'key1': 'value1', 'key2': 'value2'}
    assert len(mock_config) == 2

def test_hconfig_contains(mock_config):
    assert 'key1' in mock_config
    assert 'nonexistent_key' not in mock_config

def test_interface_initialization(mock_interface):
    assert mock_interface._data == {'key3': 'value3'}

def test_interface_inheritance(monkeypatch):
    mock_yaml_open(monkeypatch,
                   {
                       "./parent.yml": parent2_yaml,
                       "./child.yml": child2_yaml
                   }
                   )
    parent_config = Interface.from_file(user_file="parent.yml")
    child_config = Interface.from_file(user_file="child.yml")
    child_config._parent = parent_config
    assert child_config['key1'] == 'value1'
    assert child_config['key2'] == 'new_value2'

def test_interface_get_with_default(mock_interface, mock_interface2):
    assert mock_interface.get('key3', default='default') == 'value3'
    assert mock_interface.get('nonexistent_key', default='default') == 'default'

    assert mock_interface2.get('key', default='default') == 'value'
    assert mock_interface2.get('nonexistent_key', default='default') == 'default'

def test_interface_keys(mock_interface):
    assert set(mock_interface.keys()) == {'key3'}

def test_interface_values(mock_interface):
    assert list(mock_interface.values()) == ['value3']

def test_interface_items(mock_interface):
    assert set(mock_interface.items()) == {('key3', 'value3')}

def test_interface_update(mock_interface):
    mock_interface.update({'new_key': 'new_value'})
    assert mock_interface['new_key'] == 'new_value'
    
