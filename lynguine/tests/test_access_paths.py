"""Tests for CIP-000A path confinement."""

import os
import pytest

from lynguine.access.paths import PathEscapeError, resolve_under_roots


def test_path_inside_root(tmp_path):
    target = tmp_path / "data.yml"
    target.write_text("x: 1\n")
    resolved = resolve_under_roots(str(target), [str(tmp_path)])
    assert resolved == os.path.realpath(str(target))


def test_path_equal_to_root(tmp_path):
    resolved = resolve_under_roots(str(tmp_path), [str(tmp_path)])
    assert resolved == os.path.realpath(str(tmp_path))


def test_relative_escape_rejected(tmp_path):
    with pytest.raises(PathEscapeError) as exc:
        resolve_under_roots(str(tmp_path / ".." / "etc" / "passwd"), [str(tmp_path)])
    assert exc.value.path is not None
    assert str(tmp_path) in exc.value.roots


def test_absolute_escape_rejected(tmp_path):
    with pytest.raises(PathEscapeError):
        resolve_under_roots("/etc/passwd", [str(tmp_path)])


def test_empty_path_rejected(tmp_path):
    with pytest.raises(PathEscapeError):
        resolve_under_roots("", [str(tmp_path)])


def test_nul_rejected(tmp_path):
    with pytest.raises(PathEscapeError):
        resolve_under_roots("foo\x00bar", [str(tmp_path)])


def test_empty_roots_rejected(tmp_path):
    with pytest.raises(PathEscapeError):
        resolve_under_roots(str(tmp_path / "a.yml"), [])


def test_expandvars(tmp_path, monkeypatch):
    monkeypatch.setenv("LYNGUINE_TEST_ROOT", str(tmp_path))
    target = tmp_path / "nested" / "file.yml"
    target.parent.mkdir()
    target.write_text("ok\n")
    resolved = resolve_under_roots(
        os.path.join("$LYNGUINE_TEST_ROOT", "nested", "file.yml"),
        ["$LYNGUINE_TEST_ROOT"],
    )
    assert resolved == os.path.realpath(str(target))


def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("nope\n")
    jail = tmp_path / "jail"
    jail.mkdir()
    link = jail / "escape"
    try:
        os.symlink(str(secret), str(link))
    except OSError:
        pytest.skip("symlinks not available")
    with pytest.raises(PathEscapeError):
        resolve_under_roots(str(link), [str(jail)])


def test_confine_configured_path_unbounded(tmp_path):
    from lynguine.access.paths import confine_configured_path

    path = str(tmp_path / ".." / "etc" / "passwd")
    assert confine_configured_path(path, {"unbounded_paths": True}) == path


def test_yaml_cannot_enlarge_jail_via_stamp(tmp_path):
    from lynguine.assess.data import _stamp_path_roots
    from lynguine.config.interface import Interface

    cfg = tmp_path / "iface.yml"
    cfg.write_text("input:\n  type: yaml\n  filename: data.yml\n")
    interface = Interface.from_file(user_file="iface.yml", directory=str(tmp_path))
    item = {
        "type": "yaml",
        "filename": "data.yml",
        "allowed_roots": ["/"],
        "unbounded_paths": True,
    }
    _stamp_path_roots(item, interface)
    assert "unbounded_paths" not in item
    assert item["allowed_roots"] == interface.allowed_roots
    assert "/" not in item["allowed_roots"]


def test_session_manager_rejects_interface_outside_directory(tmp_path):
    from lynguine.session_manager import SessionManager

    jail = tmp_path / "jail"
    jail.mkdir()
    mgr = SessionManager(
        persistence_dir=str(tmp_path / "sessions"),
        allowed_roots=[str(jail)],
    )
    (tmp_path / "secret.yml").write_text("leaked: true\n")
    with pytest.raises(PathEscapeError):
        mgr.create_session(interface_file="../secret.yml", directory=str(jail))


def test_session_manager_rejects_request_directory_outside_cwd(tmp_path):
    """Per-request directory must not become the jail (CodeQL alert 40)."""
    from lynguine.session_manager import SessionManager

    mgr = SessionManager(persistence_dir=str(tmp_path / "sessions"))
    with pytest.raises(PathEscapeError):
        mgr.create_session(interface_file="passwd", directory="/etc")


def test_from_file_list_rejects_escape(tmp_path):
    from lynguine.config.interface import Interface

    jail = tmp_path / "jail"
    jail.mkdir()
    (tmp_path / "secret.yml").write_text("leaked: true\n")
    with pytest.raises(PathEscapeError):
        Interface.from_file(user_file=["../secret.yml"], directory=str(jail))


def test_from_cwd_file_loads_under_cwd(tmp_path, monkeypatch):
    from lynguine.config.interface import Interface

    monkeypatch.chdir(tmp_path)
    (tmp_path / "ok.yml").write_text("a: 1\n")
    interface = Interface.from_cwd_file(user_file="ok.yml", directory=".")
    assert interface["a"] == 1
    assert os.path.realpath(str(tmp_path)) in {
        os.path.realpath(root) for root in interface.allowed_roots
    }


def test_from_cwd_file_rejects_absolute_escape(tmp_path, monkeypatch):
    from lynguine.config.interface import Interface

    monkeypatch.chdir(tmp_path)
    with pytest.raises(PathEscapeError):
        Interface.from_cwd_file(user_file="passwd", directory="/etc")


def test_from_cwd_file_rejects_parent_escape(tmp_path, monkeypatch):
    from lynguine.config.interface import Interface

    jail = tmp_path / "jail"
    jail.mkdir()
    (tmp_path / "secret.yml").write_text("leaked: true\n")
    monkeypatch.chdir(jail)
    with pytest.raises(PathEscapeError):
        Interface.from_cwd_file(user_file="../secret.yml", directory=".")


def test_from_cwd_file_inherit_cannot_leave_cwd(tmp_path, monkeypatch):
    from lynguine.config.interface import Interface

    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "parent.yml").write_text("parent_only: true\n")
    (jail / "child.yml").write_text(
        "inherit:\n  directory: ../outside\n  filename: parent.yml\nchild: 1\n"
    )
    monkeypatch.chdir(jail)
    with pytest.raises(PathEscapeError):
        Interface.from_cwd_file(user_file="child.yml", directory=".")


def test_from_file_inherit_allows_sibling_directory(tmp_path):
    """Sibling inherit is normal; jail expands to include the parent dir."""
    from lynguine.config.interface import Interface

    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    (parent_dir / "_lynguine.yml").write_text("parent_only: true\nshared: from_parent\n")
    (child_dir / "_lynguine.yml").write_text(
        "inherit:\n  directory: ../parent\nchild_only: true\nshared: from_child\n"
    )
    interface = Interface.from_file(user_file="_lynguine.yml", directory=str(child_dir))
    assert interface["child_only"] is True
    assert interface["shared"] == "from_child"
    assert interface["parent_only"] is True
    child_root = os.path.realpath(str(child_dir))
    parent_root = os.path.realpath(str(parent_dir))
    roots = [os.path.realpath(r) for r in interface.allowed_roots]
    assert child_root in roots
    assert parent_root in roots


def test_from_file_inherit_binds_parent_data_directory(tmp_path):
    """Inherited filename specs with directory: . resolve under inherit.directory."""
    from lynguine.config.interface import Interface

    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    (parent_dir / "people.yml").write_text("- crsid: abc\n  name: Ada\n")
    (parent_dir / "_lynguine.yml").write_text(
        "input:\n  type: yaml\n  filename: people.yml\n  directory: .\n  index: crsid\n"
    )
    (child_dir / "_lynguine.yml").write_text(
        "inherit:\n  directory: ../parent\n  filename: _lynguine.yml\n"
    )
    interface = Interface.from_file(
        user_file="_lynguine.yml", directory=str(child_dir)
    )
    assert os.path.realpath(interface["input"]["directory"]) == os.path.realpath(
        str(parent_dir)
    )


def test_from_file_inherit_binds_glob_source_directory(tmp_path):
    """Inherited glob sources with directory: . resolve under inherit.directory."""
    from lynguine.config.interface import Interface

    parent_dir = tmp_path / "catalog"
    child_dir = tmp_path / "today"
    work = parent_dir / "work"
    parent_dir.mkdir()
    child_dir.mkdir()
    work.mkdir()
    (work / "item.yml").write_text("title: Nested work\n")
    (parent_dir / "_lynguine.yml").write_text(
        "input:\n"
        "  type: yaml_directory\n"
        "  index: sourceFilename\n"
        "  source:\n"
        "    - directory: .\n"
        "      glob: '**/*.yml'\n"
        "      recursive: true\n"
        "      include_start_directory: false\n"
        "  fields:\n"
        "    - title\n"
    )
    (child_dir / "_lynguine.yml").write_text(
        "inherit:\n  directory: ../catalog\n  filename: _lynguine.yml\n"
    )
    interface = Interface.from_file(
        user_file="_lynguine.yml", directory=str(child_dir)
    )
    src = interface["input"]["source"][0]
    assert os.path.realpath(src["directory"]) == os.path.realpath(str(parent_dir))


def test_from_flow_reads_inherited_glob_from_parent_dir(tmp_path):
    """from_flow must discover glob matches from inherit.directory, not the child."""
    from lynguine.config.interface import Interface
    from lynguine.assess.data import CustomDataFrame

    parent_dir = tmp_path / "catalog"
    child_dir = tmp_path / "today"
    work = parent_dir / "work"
    parent_dir.mkdir()
    child_dir.mkdir()
    work.mkdir()
    (work / "item.yml").write_text("title: Nested work\n")
    (parent_dir / "_lynguine.yml").write_text(
        "input:\n"
        "  type: yaml_directory\n"
        "  index: sourceFilename\n"
        "  source:\n"
        "    - directory: .\n"
        "      glob: '**/*.yml'\n"
        "      recursive: true\n"
        "      include_start_directory: false\n"
        "  fields:\n"
        "    - title\n"
    )
    (child_dir / "_lynguine.yml").write_text(
        "inherit:\n  directory: ../catalog\n  filename: _lynguine.yml\n"
    )
    interface = Interface.from_file(
        user_file="_lynguine.yml", directory=str(child_dir)
    )
    cdf = CustomDataFrame.from_flow(interface)
    frame = cdf._d["input"]
    assert "item.yml" in list(frame.index)
    assert frame.loc["item.yml", "title"] == "Nested work"


def test_bind_skips_directory_without_filename_or_glob():
    """Specs that are not path-allocating keep a relative directory."""
    from lynguine.config.interface import Interface

    spec = {"directory": ".", "type": "notes"}
    Interface._bind_spec_directory(spec, "/parent")
    assert spec["directory"] == "."


def test_bind_skips_store_fields_filename_mapping():
    """store_fields.filename is a column name, not a path spec (CIP-0018)."""
    from lynguine.config.interface import Interface

    spec = {
        "type": "yaml_directory",
        "store_fields": {
            "directory": "sourceDirectory",
            "filename": "sourceFile",
            "root": "sourceRoot",
        },
        "source": [{"directory": ".", "glob": "**/*.yml"}],
    }
    Interface._bind_spec_directory(spec, "/parent")
    assert spec["store_fields"]["directory"] == "sourceDirectory"
    assert spec["store_fields"]["filename"] == "sourceFile"
    assert spec["source"][0]["directory"] == "/parent"


def test_bind_leaves_absolute_glob_directory():
    from lynguine.config.interface import Interface

    spec = {"directory": "/abs/catalog", "glob": "**/*.yml"}
    Interface._bind_spec_directory(spec, "/parent")
    assert spec["directory"] == "/abs/catalog"


def test_from_flow_reads_inherited_data_under_parent_dir(tmp_path):
    """from_flow must read inherited data files from inherit.directory."""
    from lynguine.config.interface import Interface
    from lynguine.assess.data import CustomDataFrame

    parent_dir = tmp_path / "parent"
    child_dir = tmp_path / "child"
    parent_dir.mkdir()
    child_dir.mkdir()
    (parent_dir / "people.yml").write_text("- crsid: abc\n  name: Ada\n")
    (parent_dir / "_lynguine.yml").write_text(
        "input:\n  type: yaml\n  filename: people.yml\n  directory: .\n  index: crsid\n"
    )
    (child_dir / "_lynguine.yml").write_text(
        "inherit:\n  directory: ../parent\n  filename: _lynguine.yml\n"
    )
    interface = Interface.from_file(
        user_file="_lynguine.yml", directory=str(child_dir)
    )
    cdf = CustomDataFrame.from_flow(interface)
    frame = cdf._d["input"]
    assert frame.loc["abc", "name"] == "Ada"


def test_create_session_refuses_unbounded_manager(tmp_path):
    from lynguine.session_manager import SessionManager

    mgr = SessionManager(
        persistence_dir=str(tmp_path / "sessions"),
        unbounded_paths=True,
    )
    with pytest.raises(ValueError, match="unbounded_paths"):
        mgr.create_session(interface_file="iface.yml", directory=str(tmp_path))


def test_create_session_unbounded_loads_outside_cwd(tmp_path, monkeypatch):
    from lynguine.session_manager import SessionManager

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "iface.yml").write_text(
        "input:\n  type: fake\n  nrows: 2\n  cols:\n    - name\n  index: name\n"
    )
    mgr = SessionManager(
        persistence_dir=str(tmp_path / "sessions"),
        unbounded_paths=True,
    )
    session = mgr.create_session_unbounded(
        interface_file="iface.yml",
        directory=str(outside),
    )
    assert session.cdf.get_shape()[0] == 2


def test_http_handlers_do_not_call_from_file_or_unbounded_session():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in (
        "server.py",
        "server_interface_handlers.py",
        "server_session_handlers.py",
    ):
        text = (root / name).read_text()
        assert "Interface.from_file" not in text
        assert "create_session_unbounded" not in text
