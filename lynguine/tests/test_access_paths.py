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

    mgr = SessionManager(persistence_dir=str(tmp_path / "sessions"))
    jail = tmp_path / "jail"
    jail.mkdir()
    (tmp_path / "secret.yml").write_text("leaked: true\n")
    with pytest.raises(PathEscapeError):
        mgr.create_session(interface_file="../secret.yml", directory=str(jail))
