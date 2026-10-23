"""CIP-0017: exercise production inherit/merge and loader branches.

These tests call Interface methods directly. They do not mock
``_process_parent`` or ``_extract_mapping_columns``.
"""

import pytest

from lynguine.access.paths import PathEscapeError
from lynguine.config.interface import Interface, _HConfig


class MockConfig(_HConfig):
    def __init__(self, data=None, parent=None):
        self._data = data or {}
        self._parent = parent


def _write(directory, name, text):
    path = directory / name
    path.write_text(text)
    return path


def _load(directory, name="child.yml", **kwargs):
    return Interface.from_file(user_file=name, directory=str(directory), **kwargs)


def test_hconfig_parent_getitem_setitem_delitem():
    parent = MockConfig({"shared": "from_parent", "only_parent": 1})
    child = MockConfig({"shared": "from_child", "only_child": 2}, parent=parent)

    assert child["only_parent"] == 1
    assert child["shared"] == "from_child"

    child["only_parent"] = 9
    assert parent["only_parent"] == 9

    child["shared"] = "updated"
    assert child["shared"] == "updated"
    assert "shared" not in parent

    del child["only_parent"]
    assert "only_parent" not in parent


def test_hconfig_parent_values_str_repr_iter():
    parent = MockConfig({"p": 1})
    child = MockConfig({"c": 2}, parent=parent)

    assert set(child.values()) == {1, 2}
    assert set(child) == {"c", "p"}
    text = str(child)
    assert "'c': 2" in text
    assert "'p': 1" in text
    assert "MockConfig(" in repr(child)


def test_extract_mapping_columns_copies_and_strips():
    data = {
        "type": "csv",
        "mapping": {"a": "b"},
        "columns": ["c", "d"],
    }
    mapping, columns = Interface._extract_mapping_columns(data)
    assert mapping == {"a": "b"}
    assert columns == ["c", "d"]
    assert "mapping" not in data
    assert "columns" not in data
    assert data["type"] == "csv"

    empty_mapping, empty_columns = Interface._extract_mapping_columns({"type": "csv"})
    assert empty_mapping == {}
    assert empty_columns == []


def test_interface_requires_directory_and_user_file():
    with pytest.raises(ValueError, match="directory must be provided"):
        Interface(data=None, directory=None, user_file=None)
    with pytest.raises(ValueError, match="user_file must be provided"):
        Interface(data={}, directory=".", user_file=None)


def test_inherit_requires_directory():
    with pytest.raises(ValueError, match="no directory to inherit from"):
        Interface(
            data={"inherit": {"filename": "parent.yml"}},
            directory=".",
            user_file="child.yml",
        )


def test_inherit_unbounded_loads_parent_outside_jail(tmp_path):
    outside = tmp_path / "outside"
    jail = tmp_path / "jail"
    outside.mkdir()
    jail.mkdir()
    _write(outside, "parent.yml", "from_parent: 1\n")
    _write(
        jail,
        "child.yml",
        "inherit:\n  directory: ../outside\n  filename: parent.yml\nchild: 2\n",
    )
    iface = _load(jail, unbounded_paths=True)
    assert iface["child"] == 2
    assert iface["from_parent"] == 1
    assert iface.unbounded_paths is True


def test_inherit_writable_keeps_parent_writable(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(parent_dir, "parent.yml", "from_parent: 1\n")
    _write(
        child_dir,
        "child.yml",
        (
            "writable: true\n"
            "inherit:\n"
            "  directory: ../parent\n"
            "  filename: parent.yml\n"
            "  writable: true\n"
            "child: 2\n"
        ),
    )
    iface = _load(child_dir)
    assert iface._parent._writable is True
    assert iface["from_parent"] == 1


def test_getitem_missing_key_without_parent():
    iface = Interface(data={"a": 1}, directory=".", user_file="t.yml")
    with pytest.raises(ValueError, match="Key missing"):
        iface["missing"]


def test_input_hstack_merge_combinations(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()

    parent_plain = (
        "input:\n"
        "  type: csv\n"
        "  index: id\n"
        "  mapping:\n"
        "    a: b\n"
        "  path: parent.csv\n"
    )
    parent_hstack = (
        "input:\n"
        "  type: hstack\n"
        "  index: id\n"
        "  mapping:\n"
        "    a: b\n"
        "  specifications:\n"
        "  - type: csv\n"
        "    path: a.csv\n"
    )
    child_plain = (
        "inherit:\n"
        "  directory: ../parent\n"
        "  filename: parent.yml\n"
        "input:\n"
        "  type: yaml\n"
        "  index: id\n"
        "  mapping:\n"
        "    c: d\n"
        "  path: child.yaml\n"
    )
    child_hstack = (
        "inherit:\n"
        "  directory: ../parent\n"
        "  filename: parent.yml\n"
        "input:\n"
        "  type: hstack\n"
        "  index: id\n"
        "  mapping:\n"
        "    c: d\n"
        "  specifications:\n"
        "  - type: yaml\n"
        "    path: child.yaml\n"
    )

    _write(parent_dir, "parent.yml", parent_plain)
    _write(child_dir, "child.yml", child_plain)
    neither_hstack = _load(child_dir)["input"]
    assert neither_hstack["type"] == "hstack"
    assert len(neither_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", parent_plain)
    _write(child_dir, "child.yml", child_hstack)
    both_child_hstack = _load(child_dir)["input"]
    assert both_child_hstack["type"] == "hstack"
    assert len(both_child_hstack["specifications"]) == 2
    assert both_child_hstack["mapping"]["a"] == "b"
    assert both_child_hstack["mapping"]["c"] == "d"

    _write(parent_dir, "parent.yml", parent_hstack)
    _write(child_dir, "child.yml", child_plain)
    parent_is_hstack = _load(child_dir)["input"]
    assert parent_is_hstack["type"] == "hstack"
    assert len(parent_is_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", parent_hstack)
    _write(child_dir, "child.yml", child_hstack)
    both_hstack = _load(child_dir)["input"]
    assert both_hstack["type"] == "hstack"
    assert len(both_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", "other: 1\n")
    _write(child_dir, "child.yml", child_plain)
    only_child = _load(child_dir)["input"]
    assert only_child["path"] == "child.yaml"

    _write(parent_dir, "parent.yml", parent_plain)
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    only_parent = _load(child_dir)["input"]
    assert only_parent["path"] == "parent.csv"


def test_constants_hstack_merge_combinations(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()

    parent_plain = "constants:\n  type: yaml\n  path: parent.yaml\n"
    parent_hstack = (
        "constants:\n"
        "  type: hstack\n"
        "  specifications:\n"
        "  - type: yaml\n"
        "    path: a.yaml\n"
    )
    child_plain = (
        "inherit:\n"
        "  directory: ../parent\n"
        "  filename: parent.yml\n"
        "constants:\n"
        "  type: yaml\n"
        "  path: child.yaml\n"
    )
    child_hstack = (
        "inherit:\n"
        "  directory: ../parent\n"
        "  filename: parent.yml\n"
        "constants:\n"
        "  type: hstack\n"
        "  specifications:\n"
        "  - type: yaml\n"
        "    path: child.yaml\n"
    )

    _write(parent_dir, "parent.yml", parent_plain)
    _write(child_dir, "child.yml", child_plain)
    neither_hstack = _load(child_dir)["constants"]
    assert neither_hstack["type"] == "hstack"
    assert len(neither_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", parent_plain)
    _write(child_dir, "child.yml", child_hstack)
    child_is_hstack = _load(child_dir)["constants"]
    assert child_is_hstack["type"] == "hstack"
    assert len(child_is_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", parent_hstack)
    _write(child_dir, "child.yml", child_plain)
    parent_is_hstack = _load(child_dir)["constants"]
    assert len(parent_is_hstack["specifications"]) == 2

    _write(parent_dir, "parent.yml", parent_hstack)
    _write(child_dir, "child.yml", child_hstack)
    both = _load(child_dir)["constants"]
    assert len(both["specifications"]) == 2

    _write(parent_dir, "parent.yml", "other: 1\n")
    _write(child_dir, "child.yml", child_plain)
    assert _load(child_dir)["constants"]["path"] == "child.yaml"

    _write(parent_dir, "parent.yml", parent_plain)
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    assert _load(child_dir)["constants"]["path"] == "parent.yaml"


def test_inherit_append_scalar_raises(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(parent_dir, "parent.yml", "scalar: 1\n")
    _write(
        child_dir,
        "child.yml",
        (
            "inherit:\n"
            "  directory: ../parent\n"
            "  filename: parent.yml\n"
            "  append:\n"
            "  - scalar\n"
            "scalar: 2\n"
        ),
    )
    iface = _load(child_dir)
    with pytest.raises(ValueError, match="append"):
        _ = iface["scalar"]


def test_inherit_ignore_and_missing_key(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(parent_dir, "parent.yml", "secret: x\nkept: y\n")
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    # _process_parent deletes ignore keys; set ignore after load to hit getitem.
    iface._data["inherit"]["ignore"] = ["secret"]
    with pytest.raises(KeyError, match="inherit:ignore"):
        _ = iface["secret"]
    with pytest.raises(KeyError, match="not found"):
        _ = iface["nope"]
    assert iface["kept"] == "y"


def test_process_parent_output_becomes_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "output:\n"
            "  type: csv\n"
            "  index: id\n"
            "  mapping:\n"
            "    a: b\n"
            "  columns:\n"
            "  - a\n"
            "  path: out.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    assert "output" not in iface._parent._data
    assert iface._parent._data["input"]["path"] == "out.csv"
    assert iface._parent._data["input"]["mapping"]["a"] == "b"
    assert "a" in iface._parent._data["input"]["columns"]


def test_process_parent_output_appends_to_existing_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "input:\n"
            "  type: csv\n"
            "  index: id\n"
            "  mapping:\n"
            "    x: y\n"
            "  path: in.csv\n"
            "output:\n"
            "  type: csv\n"
            "  mapping:\n"
            "    a: b\n"
            "  columns:\n"
            "  - a\n"
            "  path: out.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    parent_input = iface._parent._data["input"]
    assert parent_input["type"] == "hstack"
    assert len(parent_input["specifications"]) == 2
    assert parent_input["mapping"]["a"] == "b"


def test_process_parent_output_appends_to_hstack_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "input:\n"
            "  type: hstack\n"
            "  index: id\n"
            "  mapping: {}\n"
            "  columns:\n"
            "  - x\n"
            "  specifications:\n"
            "  - type: csv\n"
            "    path: in.csv\n"
            "output:\n"
            "  type: csv\n"
            "  columns:\n"
            "  - a\n"
            "  path: out.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    specs = iface._parent._data["input"]["specifications"]
    assert len(specs) == 2
    assert specs[-1]["path"] == "out.csv"


def test_process_parent_series_becomes_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "series:\n"
            "  type: csv\n"
            "  index: id\n"
            "  mapping:\n"
            "    a: b\n"
            "  columns:\n"
            "  - a\n"
            "  path: series.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    assert "series" not in iface._parent._data
    assert iface._parent._data["input"]["type"] == "series"
    assert iface._parent._data["input"]["mapping"]["a"] == "b"


def test_process_parent_series_appends_to_existing_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "input:\n"
            "  type: csv\n"
            "  index: id\n"
            "  path: in.csv\n"
            "series:\n"
            "  type: csv\n"
            "  index: id\n"
            "  path: series.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    parent_input = iface._parent._data["input"]
    assert parent_input["type"] == "hstack"
    assert parent_input["specifications"][-1]["type"] == "series"


def test_process_parent_series_appends_to_hstack_input(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "input:\n"
            "  type: hstack\n"
            "  index: id\n"
            "  mapping:\n"
            "    x: y\n"
            "  columns:\n"
            "  - x\n"
            "  specifications:\n"
            "  - type: csv\n"
            "    path: in.csv\n"
            "series:\n"
            "  type: csv\n"
            "  index: id\n"
            "  mapping:\n"
            "    a: b\n"
            "  columns:\n"
            "  - a\n"
            "  path: series.csv\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    specs = iface._parent._data["input"]["specifications"]
    assert specs[-1]["type"] == "series"


def test_process_parent_parameters_become_constants(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "parameters:\n"
            "  type: yaml\n"
            "  mapping:\n"
            "    a: b\n"
            "  columns:\n"
            "  - a\n"
            "  path: params.yaml\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        "inherit:\n  directory: ../parent\n  filename: parent.yml\nchild: 1\n",
    )
    iface = _load(child_dir)
    assert "parameters" not in iface._parent._data
    constants = iface._parent._data["constants"]
    assert constants["path"] == "params.yaml"
    assert constants["mapping"]["a"] == "b"
    assert "a" in constants["columns"]


def test_process_parent_parameters_stack_onto_parent_constants(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "constants:\n"
            "  type: yaml\n"
            "  path: existing.yaml\n"
            "parameters:\n"
            "  type: yaml\n"
            "  path: params.yaml\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        (
            "inherit:\n"
            "  directory: ../parent\n"
            "  filename: parent.yml\n"
            "constants:\n"
            "  type: yaml\n"
            "  path: child.yaml\n"
        ),
    )
    iface = _load(child_dir)
    constants = iface._parent._data["constants"]
    assert constants["type"] == "hstack"
    assert len(constants["specifications"]) == 2


def test_process_parent_parameters_append_to_hstack_constants(tmp_path):
    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    _write(
        parent_dir,
        "parent.yml",
        (
            "constants:\n"
            "  type: hstack\n"
            "  columns:\n"
            "  - x\n"
            "  specifications:\n"
            "  - type: yaml\n"
            "    path: existing.yaml\n"
            "parameters:\n"
            "  type: yaml\n"
            "  columns:\n"
            "  - a\n"
            "  path: params.yaml\n"
        ),
    )
    _write(
        child_dir,
        "child.yml",
        (
            "inherit:\n"
            "  directory: ../parent\n"
            "  filename: parent.yml\n"
            "constants:\n"
            "  type: yaml\n"
            "  path: child.yaml\n"
        ),
    )
    iface = _load(child_dir)
    specs = iface._parent._data["constants"]["specifications"]
    assert specs[-1]["path"] == "params.yaml"


def test_extract_review_write_fields_edges():
    iface = Interface(data={}, directory=".", user_file="t.yml")
    assert iface._extract_review_write_fields({"foo": 1}) == []
    iface._data = None
    with pytest.raises(ValueError, match="No data provided"):
        iface._extract_review_write_fields()


def test_extract_fields_accepts_single_mapping():
    iface = Interface(data={}, directory=".", user_file="t.yml")
    assert iface._extract_fields({"field": "only"}) == ["only"]


def test_from_file_yaml_error_and_empty(tmp_path):
    _write(tmp_path, "bad.yml", ":\n  - [\n")
    with pytest.raises(ValueError, match="Error reading yaml"):
        _load(tmp_path, "bad.yml")

    _write(tmp_path, "empty.yml", "{}\n")
    with pytest.raises(ValueError, match="No data found"):
        _load(tmp_path, "empty.yml")


def test_from_file_field_extraction(tmp_path):
    _write(tmp_path, "wrapped.yml", "outer:\n  inner: 1\n")
    iface = Interface.from_file(
        user_file="wrapped.yml", directory=str(tmp_path), field="outer"
    )
    assert iface["inner"] == 1
    with pytest.raises(ValueError, match='Field "missing"'):
        Interface.from_file(
            user_file="wrapped.yml", directory=str(tmp_path), field="missing"
        )


def test_from_file_default_name_and_list(tmp_path):
    _write(tmp_path, "_lynguine.yml", "via_default: 1\n")
    iface = Interface.from_file(directory=str(tmp_path))
    assert iface["via_default"] == 1

    _write(tmp_path, "second.yml", "via_list: 2\n")
    listed = Interface.from_file(
        user_file=["missing.yml", "second.yml"], directory=str(tmp_path)
    )
    assert listed["via_list"] == 2


def test_from_file_unbounded_missing_creates_empty(tmp_path):
    iface = Interface.from_file(
        user_file="missing.yml",
        directory=str(tmp_path),
        unbounded_paths=True,
        raise_error_if_not_found=False,
    )
    assert isinstance(iface, Interface)


def test_from_file_unbounded_yaml_error_and_field(tmp_path):
    _write(tmp_path, "bad.yml", ":\n  - [\n")
    with pytest.raises(ValueError, match="Error reading yaml"):
        Interface.from_file(
            user_file="bad.yml",
            directory=str(tmp_path),
            unbounded_paths=True,
        )

    _write(tmp_path, "wrapped.yml", "outer:\n  inner: 1\n")
    iface = Interface.from_file(
        user_file="wrapped.yml",
        directory=str(tmp_path),
        field="outer",
        unbounded_paths=True,
    )
    assert iface["inner"] == 1
    with pytest.raises(ValueError, match='Field "missing"'):
        Interface.from_file(
            user_file="wrapped.yml",
            directory=str(tmp_path),
            field="missing",
            unbounded_paths=True,
        )
    _write(tmp_path, "empty.yml", "{}\n")
    with pytest.raises(ValueError, match="No data found"):
        Interface.from_file(
            user_file="empty.yml",
            directory=str(tmp_path),
            unbounded_paths=True,
        )
    with pytest.raises(ValueError, match="No configuration file found"):
        Interface.from_file(
            user_file="nope.yml",
            directory=str(tmp_path),
            unbounded_paths=True,
        )


def test_from_cwd_file_default_list_yaml_field_and_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, "_lynguine.yml", "via_default: 1\n")
    assert Interface.from_cwd_file(directory=".")["via_default"] == 1

    _write(tmp_path, "second.yml", "via_list: 2\n")
    listed = Interface.from_cwd_file(
        user_file=["missing.yml", "second.yml"], directory="."
    )
    assert listed["via_list"] == 2

    _write(tmp_path, "bad.yml", ":\n  - [\n")
    with pytest.raises(ValueError, match="Error reading yaml"):
        Interface.from_cwd_file(user_file="bad.yml", directory=".")

    _write(tmp_path, "wrapped.yml", "outer:\n  inner: 1\n")
    iface = Interface.from_cwd_file(
        user_file="wrapped.yml", directory=".", field="outer"
    )
    assert iface["inner"] == 1
    with pytest.raises(ValueError, match='Field "missing"'):
        Interface.from_cwd_file(
            user_file="wrapped.yml", directory=".", field="missing"
        )

    _write(tmp_path, "empty.yml", "{}\n")
    with pytest.raises(ValueError, match="No data found"):
        Interface.from_cwd_file(user_file="empty.yml", directory=".")

    with pytest.raises(ValueError, match="No configuration file found"):
        Interface.from_cwd_file(user_file="nope.yml", directory=".")

    iface_empty = Interface.from_cwd_file(
        user_file="nope.yml", directory=".", raise_error_if_not_found=False
    )
    assert isinstance(iface_empty, Interface)


def test_from_cwd_file_rejects_prefix_bypass_directory(tmp_path, monkeypatch):
    cwd = tmp_path / "cwd"
    evil = tmp_path / "cwd-evil"
    cwd.mkdir()
    evil.mkdir()
    _write(evil, "x.yml", "leaked: true\n")
    monkeypatch.chdir(cwd)
    with pytest.raises(PathEscapeError):
        Interface.from_cwd_file(user_file="x.yml", directory="../cwd-evil")
