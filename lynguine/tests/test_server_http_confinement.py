"""In-process coverage for HTTP path confinement (PR #69 Copilot fixes).

``test_server_mode`` runs the server in a subprocess, so those lines never
appear in the parent coverage report. These tests exercise the handlers
directly.
"""

import pandas as pd
import pytest

from lynguine.server import LynguineHandler
from lynguine.server_interface_handlers import handle_talk_field
from lynguine.util.yaml import FileFormatError


def test_handle_read_data_defaults_confinement(mocker):
    handler = object.__new__(LynguineHandler)
    send = mocker.patch.object(handler, "send_json_response")
    mocker.patch.object(handler, "send_error_response")
    read = mocker.patch(
        "lynguine.server.io.read_data",
        return_value=pd.DataFrame({"name": ["a"]}),
    )

    handler.handle_read_data(
        {"data_source": {"type": "fake", "nrows": 1, "directory": "/tmp/jail"}}
    )

    details = read.call_args[0][0]
    assert details["unbounded_paths"] is False
    assert details["allowed_roots"] == ["/tmp/jail"]
    send.assert_called_once()


def test_handle_read_data_defaults_root_to_dot(mocker):
    handler = object.__new__(LynguineHandler)
    mocker.patch.object(handler, "send_json_response")
    mocker.patch.object(handler, "send_error_response")
    read = mocker.patch(
        "lynguine.server.io.read_data",
        return_value=pd.DataFrame({"name": ["a"]}),
    )

    handler.handle_read_data({"data_source": {"type": "fake", "nrows": 1}})

    details = read.call_args[0][0]
    assert details["allowed_roots"] == ["."]
    assert details["unbounded_paths"] is False


def test_handle_read_data_keeps_explicit_confinement(mocker):
    handler = object.__new__(LynguineHandler)
    mocker.patch.object(handler, "send_json_response")
    mocker.patch.object(handler, "send_error_response")
    read = mocker.patch(
        "lynguine.server.io.read_data",
        return_value=(pd.DataFrame({"name": ["a"]}), object()),
    )

    handler.handle_read_data(
        {
            "data_source": {
                "type": "fake",
                "nrows": 1,
                "unbounded_paths": True,
                "allowed_roots": ["/explicit"],
            }
        }
    )

    details = read.call_args[0][0]
    assert details["unbounded_paths"] is True
    assert details["allowed_roots"] == ["/explicit"]


@pytest.mark.parametrize(
    "config_files,match",
    [
        (123, "must be a list"),
        ([""], "cannot be empty"),
        (["  "], "cannot be empty"),
        ([1], "must be a string"),
        (["/etc/passwd"], "Invalid config file path"),
        (["../secret.yml"], "Invalid config file path"),
        (["subdir/a.yml"], "Invalid config file path"),
        (["."], "Invalid config file path"),
        ([".."], "Invalid config file path"),
    ],
)
def test_handle_talk_field_rejects_bad_config_files(config_files, match):
    result = handle_talk_field(
        {
            "field": "title",
            "markdown_file": "talk.md",
            "config_files": config_files,
        }
    )
    assert result["status"] == "error"
    assert match in result["error"]


def test_handle_talk_field_accepts_basename_string(mocker):
    talk = mocker.patch(
        "lynguine.server_interface_handlers.talk_field",
        return_value="Hello",
    )
    result = handle_talk_field(
        {
            "field": "title",
            "markdown_file": "talk.md",
            "config_files": "_lamd.yml",
        }
    )
    assert result == {"status": "success", "value": "Hello"}
    talk.assert_called_once_with("title", "talk.md", user_file=["_lamd.yml"])


def test_handle_talk_field_fallback_uses_sanitized_list(mocker):
    mocker.patch(
        "lynguine.server_interface_handlers.talk_field",
        side_effect=FileFormatError("bad markdown"),
    )
    iface = {"title": "From config"}
    from_cwd = mocker.patch(
        "lynguine.server_interface_handlers.Interface.from_cwd_file",
        return_value=iface,
    )
    result = handle_talk_field(
        {
            "field": "title",
            "markdown_file": "talk.md",
            "config_files": ["_lamd.yml"],
        }
    )
    assert result["status"] == "success"
    assert result["value"] == "From config"
    from_cwd.assert_called_once_with(user_file=["_lamd.yml"], directory=".")


def test_handle_talk_field_missing_md_uses_sanitized_list(mocker):
    mocker.patch(
        "lynguine.server_interface_handlers.talk_field",
        side_effect=FileNotFoundError("missing"),
    )
    iface = {"title": "Fallback"}
    from_cwd = mocker.patch(
        "lynguine.server_interface_handlers.Interface.from_cwd_file",
        return_value=iface,
    )
    result = handle_talk_field(
        {
            "field": "title",
            "markdown_file": "missing.md",
            "config_files": ["ok.yml"],
        }
    )
    assert result["value"] == "Fallback"
    from_cwd.assert_called_once_with(user_file=["ok.yml"], directory=".")
