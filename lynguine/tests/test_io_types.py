"""Tests for CIP-0019 tabular IO plugins. No network, no vendor SDKs."""

import sys
import textwrap

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from lynguine.access.io import read_data, write_data
from lynguine.access.io_types import (
    MissingIOCredentialError,
    PluginImportError,
    ReadOnlyIOTypeError,
    ReservedIOTypeError,
    UnknownIOTypeError,
    get_io_type,
    list_io_types,
    load_plugins,
    register_io_type,
    unknown_io_type_message,
)
from lynguine.assess.data import CustomDataFrame
from lynguine.config.interface import Interface


@pytest.fixture
def empty_io_registry():
    from lynguine.access import io_types

    saved = dict(io_types._REGISTRY)
    io_types._REGISTRY.clear()
    yield io_types
    io_types._REGISTRY.clear()
    io_types._REGISTRY.update(saved)


def _read_mem(details):
    rows = details.get("rows") or [{"id": 1, "title": "alpha"}]
    return pd.DataFrame(rows)


def test_register_list_and_get(empty_io_registry):
    register_io_type("memtable", read=_read_mem)
    assert list_io_types() == ["memtable"]
    spec = get_io_type("memtable")
    assert spec.name == "memtable"
    assert spec.write is None


def test_register_replaces_same_name(empty_io_registry):
    register_io_type("memtable", read=_read_mem)

    def other(details):
        return pd.DataFrame([{"id": 9}])

    register_io_type("memtable", read=other)
    df, _ = read_data({"type": "memtable"})
    assert list(df["id"]) == [9]


def test_reserved_builtin_names_rejected(empty_io_registry):
    for name in ("csv", "excel", "fake", "gsheet", "yaml"):
        with pytest.raises(ReservedIOTypeError, match=name):
            register_io_type(name, read=_read_mem)
    assert list_io_types() == []


def test_get_unknown_type_lists_registered(empty_io_registry):
    register_io_type("memtable", read=_read_mem)
    with pytest.raises(UnknownIOTypeError, match="memtable"):
        get_io_type("missing")


def test_read_data_dispatches_registered_type(empty_io_registry):
    register_io_type("memtable", read=_read_mem)
    df, details = read_data(
        {"type": "memtable", "rows": [{"id": 2, "title": "beta"}]}
    )
    assert_frame_equal(df, pd.DataFrame([{"id": 2, "title": "beta"}]))
    assert details["type"] == "memtable"


def test_read_data_unknown_type_names_type_and_registry(empty_io_registry):
    register_io_type("memtable", read=_read_mem)
    with pytest.raises(ValueError) as exc:
        read_data({"type": "trello"})
    msg = str(exc.value)
    assert 'Unknown type "trello" in read_data' in msg
    assert "memtable" in msg


def test_builtin_fake_unchanged_when_plugins_registered(empty_io_registry, mocker):
    from lynguine.util.fake import Generate

    register_io_type("memtable", read=_read_mem)
    mocker.patch.object(Generate, "name", return_value="Ada Lovelace")
    df, _ = read_data(
        {"type": "fake", "nrows": 2, "cols": ["name"]}
    )
    assert list(df["name"]) == ["Ada Lovelace", "Ada Lovelace"]


def test_write_registered_without_write_flag_is_readonly(empty_io_registry):
    written = []

    def _write(df, details):
        written.append(df.copy())

    register_io_type("memtable", read=_read_mem, write=_write)
    with pytest.raises(ReadOnlyIOTypeError, match="memtable"):
        write_data(pd.DataFrame([{"id": 1}]), {"type": "memtable"})
    assert written == []


def test_write_registered_without_callable_is_readonly(empty_io_registry):
    register_io_type("memtable", read=_read_mem)
    with pytest.raises(ReadOnlyIOTypeError, match="read-only"):
        write_data(
            pd.DataFrame([{"id": 1}]),
            {"type": "memtable", "write": True},
        )


def test_write_registered_when_enabled(empty_io_registry):
    written = []

    def _write(df, details):
        written.append((list(df["id"]), details.get("sink")))

    register_io_type("memtable", read=_read_mem, write=_write)
    write_data(
        pd.DataFrame([{"id": 3}]),
        {"type": "memtable", "write": True, "sink": "board"},
    )
    assert written == [([3], "board")]


def test_write_unknown_type_does_not_fall_through_to_file(empty_io_registry):
    with pytest.raises(ValueError, match='Unknown type "trello" in write_data'):
        write_data(pd.DataFrame([{"id": 1}]), {"type": "trello", "write": True})


def test_plugins_import_registers_type(empty_io_registry, tmp_path, monkeypatch):
    mod = tmp_path / "lynguine_test_mem.py"
    mod.write_text(
        textwrap.dedent(
            """
            import pandas as pd
            from lynguine.access.io_types import register_io_type

            def _read(details):
                return pd.DataFrame([{"id": 7, "title": "from-plugin"}])

            register_io_type("memtable", read=_read)
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    load_plugins(["lynguine_test_mem"], needed_type="memtable")
    df, _ = read_data({"type": "memtable"})
    assert list(df["title"]) == ["from-plugin"]
    sys.modules.pop("lynguine_test_mem", None)


def test_plugins_import_failure_names_module(empty_io_registry):
    with pytest.raises(PluginImportError, match="lynguine_no_such_plugin"):
        load_plugins(["lynguine_no_such_plugin"], needed_type="trello")


def test_read_data_plugins_key_imports_before_dispatch(
    empty_io_registry, tmp_path, monkeypatch
):
    mod = tmp_path / "lynguine_test_mem2.py"
    mod.write_text(
        textwrap.dedent(
            """
            import pandas as pd
            from lynguine.access.io_types import register_io_type

            def _read(details):
                return pd.DataFrame([{"id": 4}])

            register_io_type("memtable", read=_read)
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    df, _ = read_data(
        {"type": "memtable", "plugins": ["lynguine_test_mem2"]}
    )
    assert list(df["id"]) == [4]
    sys.modules.pop("lynguine_test_mem2", None)


def test_from_flow_loads_interface_plugins(
    empty_io_registry, tmp_path, monkeypatch
):
    mod = tmp_path / "lynguine_test_flow.py"
    mod.write_text(
        textwrap.dedent(
            """
            import pandas as pd
            from lynguine.access.io_types import register_io_type

            def _read(details):
                return pd.DataFrame([{"id": 11, "title": "flow"}])

            register_io_type("memtable", read=_read)
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    interface = Interface.from_yaml(
        """
plugins:
  - lynguine_test_flow
input:
  type: memtable
  index: id
"""
    )
    cdf = CustomDataFrame.from_flow(interface)
    assert list(cdf.index) == [11]
    assert cdf.at[11, "title"] == "flow"
    sys.modules.pop("lynguine_test_flow", None)


def test_entry_point_lazy_load(empty_io_registry, monkeypatch):
    class FakeEP:
        name = "fromep"
        value = "lynguine_mem:register"
        dist = type("D", (), {"name": "lynguine-mem"})()

        def load(self):
            def register():
                register_io_type(
                    "fromep",
                    read=lambda details: pd.DataFrame([{"k": 1}]),
                )

            return register

    monkeypatch.setattr(
        "lynguine.access.io_types._iter_entry_points",
        lambda: [FakeEP()],
    )
    df, _ = read_data({"type": "fromep"})
    assert list(df["k"]) == [1]
    assert "fromep" in list_io_types()


def test_unknown_message_with_empty_registry(empty_io_registry):
    msg = unknown_io_type_message("read_data", "trello")
    assert "trello" in msg
    assert "No plugin types are registered" in msg


def test_declared_credential_type_is_fetched_by_lynguine(
    empty_io_registry, mocker
):
    seen = {}

    def _read(details):
        seen["value"] = details.get("credential_value")
        seen["key"] = details.get("credential")
        return pd.DataFrame([{"id": 1}])

    register_io_type("trello", read=_read, credential_type="trello_api")
    mock_mgr = mocker.Mock()
    mock_mgr.get_credential.return_value = {
        "value": {"api_key": "k", "token": "t"}
    }
    mocker.patch(
        "lynguine.security.credentials.get_credential_manager",
        return_value=mock_mgr,
    )
    mock_ac = mocker.Mock()
    mocker.patch(
        "lynguine.security.access_control.get_access_controller",
        return_value=mock_ac,
    )

    df, details = read_data(
        {"type": "trello", "credential": "my_trello"}
    )
    assert list(df["id"]) == [1]
    mock_mgr.get_credential.assert_called_once_with(
        "my_trello", credential_type="trello_api"
    )
    assert seen["value"] == {"api_key": "k", "token": "t"}
    assert seen["key"] == "my_trello"
    assert "credential_value" not in details


def test_credential_type_without_key_raises(empty_io_registry):
    register_io_type("trello", read=_read_mem, credential_type="trello_api")
    with pytest.raises(MissingIOCredentialError, match="credential:"):
        read_data({"type": "trello"})


def test_no_credential_type_does_not_fetch(empty_io_registry, mocker):
    fetch = mocker.patch(
        "lynguine.security.credentials.get_credential_manager"
    )
    register_io_type("memtable", read=_read_mem)
    df, _ = read_data({"type": "memtable"})
    assert list(df["id"]) == [1]
    fetch.assert_not_called()
