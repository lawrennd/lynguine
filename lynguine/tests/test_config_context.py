import io
import logging
import os
from unittest.mock import MagicMock

import pytest

import lynguine
from lynguine.config.context import Context, _Config
from lynguine.security.credentials import (
    CredentialNotFoundError,
    CredentialValidationError,
)

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

dirname = os.path.dirname(lynguine.config.context.__file__)
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


def _logging(**overrides):
    data = {"level": 20, "filename": "test.log"}
    data.update(overrides)
    return {"logging": data}


def test_config_base_cannot_be_constructed():
    with pytest.raises(NotImplementedError):
        _Config()


def test_context_from_data_dict_protocol():
    cfg = Context(data={"alpha": 1, **_logging()})
    assert cfg["alpha"] == 1
    assert "alpha" in cfg
    assert "missing" not in cfg
    assert len(cfg) == 2
    assert set(cfg.keys()) == {"alpha", "logging"}
    assert ("alpha", 1) in list(cfg.items())
    assert 1 in list(cfg.values())
    assert list(cfg) == list(cfg.keys())
    assert cfg.get("alpha") == 1
    assert cfg.get("missing", "fallback") == "fallback"

    cfg["beta"] = 2
    assert cfg["beta"] == 2
    cfg.update({"gamma": 3})
    assert cfg["gamma"] == 3
    del cfg["beta"]
    assert "beta" not in cfg

    text = str(cfg)
    assert "alpha" in text
    assert "Context(" in repr(cfg)


def test_context_empty_data_raises():
    with pytest.raises(ValueError, match="No configuration file found"):
        Context(data={})


def test_context_expands_nested_list_and_env(monkeypatch):
    monkeypatch.setenv("LYNGUINE_TEST_HOME", "/tmp/lynguine-home")
    cfg = Context(
        data={
            "paths": ["$LYNGUINE_TEST_HOME/a", "$LYNGUINE_TEST_HOME/b"],
            "nested": {"x": "$LYNGUINE_TEST_HOME/c"},
            "count": 3,
            **_logging(),
        }
    )
    assert cfg["paths"] == ["/tmp/lynguine-home/a", "/tmp/lynguine-home/b"]
    assert cfg["nested"]["x"] == "/tmp/lynguine-home/c"
    assert cfg["count"] == 3


def test_context_merges_machine_over_defaults(monkeypatch):
    default_path = os.path.join(dirname, "defaults.yml")
    local_path = os.path.join(dirname, "machine.yml")
    contents = {
        default_path: "logging:\n  level: 20\n  filename: d.log\nshared: default\n",
        local_path: "shared: local\nextra: 1\n",
    }

    monkeypatch.setattr(os.path, "exists", lambda path: path in contents)

    def mock_open(path, mode="r", *args, **kwargs):
        return io.StringIO(contents[path])

    monkeypatch.setattr("builtins.open", mock_open)
    cfg = Context()
    assert cfg["shared"] == "local"
    assert cfg["extra"] == 1
    assert cfg["logging"]["filename"] == "d.log"


def test_expand_credential_non_string():
    cfg = Context(data={"n": 7, **_logging()})
    assert cfg._expand_credential_references(7) == 7


def test_expand_credential_unavailable(monkeypatch):
    monkeypatch.setattr(
        "lynguine.config.context.SECURE_CREDENTIALS_AVAILABLE", False
    )
    cfg = Context(data={"token": "${credential:secret}", **_logging()})
    assert cfg["token"] == "${credential:secret}"


def test_expand_credential_scalar_value(monkeypatch):
    manager = MagicMock()
    manager.get_credential.return_value = {"value": "abc"}
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    cfg = Context(data={"token": "${credential:k}", **_logging()})
    assert cfg["token"] == "abc"
    manager.get_credential.assert_called()


def test_expand_credential_dict_value(monkeypatch):
    manager = MagicMock()
    manager.get_credential.return_value = {"value": {"client_id": "x"}}
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    # Call the expander directly: Context.__init__ then runs expandvars, which
    # cannot accept the dict this path returns.
    cfg = Context(data=_logging())
    assert cfg._expand_credential_references("${credential:google}") == {
        "client_id": "x"
    }


def test_expand_credential_missing_value_leaves_reference(monkeypatch, caplog):
    manager = MagicMock()
    manager.get_credential.return_value = {"meta": True}
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    with caplog.at_level(logging.WARNING, logger="lynguine.config.context"):
        cfg = Context(data={"token": "${credential:empty}", **_logging()})
    assert cfg["token"] == "${credential:empty}"
    assert "Failed to resolve credential reference" in caplog.text


def test_expand_credential_not_found_leaves_reference(monkeypatch, caplog):
    manager = MagicMock()
    manager.get_credential.side_effect = CredentialNotFoundError("missing")
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    with caplog.at_level(logging.WARNING, logger="lynguine.config.context"):
        cfg = Context(data={"token": "${credential:gone}", **_logging()})
    assert cfg["token"] == "${credential:gone}"


def test_expand_credential_validation_error_leaves_reference(monkeypatch):
    manager = MagicMock()
    manager.get_credential.side_effect = CredentialValidationError("bad")
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    cfg = Context(data={"token": "${credential:bad}", **_logging()})
    assert cfg["token"] == "${credential:bad}"


def test_expand_credential_dict_placeholder_refetch_fails(monkeypatch):
    manager = MagicMock()
    manager.get_credential.side_effect = [
        {"value": {"k": "v"}},
        RuntimeError("gone"),
    ]
    monkeypatch.setattr(
        "lynguine.config.context.get_credential_manager", lambda: manager
    )
    cfg = Context(data={"oauth": "${credential:google}", **_logging()})
    assert cfg["oauth"] == "__CREDENTIAL_DICT_google__"


def test_logging_defaults_missing_level():
    cfg = Context(data={"logging": {"filename": "only.log"}})
    assert cfg["logging"]["level"] == 20
    assert cfg["logging"]["filename"] == "only.log"


def test_logging_defaults_missing_filename():
    cfg = Context(name="unit", data={"logging": {"level": 10}})
    assert cfg["logging"]["level"] == 10
    assert cfg["logging"]["filename"] == "unit.log"


def test_logging_defaults_absent():
    cfg = Context(name="unit", data={"foo": 1})
    assert cfg["logging"] == {"level": 20, "filename": "unit.log"}
