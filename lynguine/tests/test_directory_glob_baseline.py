"""Directory-glob behaviour tests (CIP-000F baseline + recursive discovery).

Do not mock ``glob.glob`` here — use real ``tmp_path`` trees.
"""

from __future__ import annotations

import os

import pytest
import yaml

from lynguine.access.io import read_yaml_directory
from lynguine.access.paths import PathEscapeError


def _write_yml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _yaml_details(source_directory: str, glob_pattern: str = "*.yml", **source_extra):
    return {
        "source": [
            {
                "directory": source_directory,
                "glob": glob_pattern,
                **source_extra,
            }
        ],
    }


def test_flat_glob_absolute_directory(tmp_path):
    """Flat ``*.yml`` under an absolute directory loads one row per file."""
    _write_yml(tmp_path / "a.yml", {"title": "A"})
    _write_yml(tmp_path / "b.yml", {"title": "B"})
    _write_yml(tmp_path / "nested" / "c.yml", {"title": "C"})

    df = read_yaml_directory(_yaml_details(str(tmp_path), "*.yml"))

    names = sorted(df["sourceFilename"].tolist())
    assert names == ["a.yml", "b.yml"]
    assert set(df["title"].tolist()) == {"A", "B"}


def test_flat_glob_relative_directory(tmp_path, monkeypatch):
    """Relative ``directory`` without ``allowed_roots`` resolves matches (no double-join)."""
    root = tmp_path / "workspace"
    data_dir = root / "catalog"
    _write_yml(data_dir / "item.yml", {"title": "Item"})
    monkeypatch.chdir(root)

    df = read_yaml_directory(_yaml_details("catalog", "*.yml"))

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Item"
    assert df.iloc[0]["sourceFilename"] == "item.yml"


def test_flat_glob_relative_directory_with_allowed_roots(tmp_path, monkeypatch):
    """Relative directory under ``allowed_roots`` (from_flow-shaped) loads."""
    root = tmp_path / "workspace"
    data_dir = root / "catalog"
    _write_yml(data_dir / "item.yml", {"title": "Rooted"})
    monkeypatch.chdir(root)

    details = _yaml_details("catalog", "*.yml")
    details["allowed_roots"] = [str(root.resolve())]

    df = read_yaml_directory(details)

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Rooted"


def test_nested_not_matched_by_flat_glob(tmp_path):
    """Without recursive support, nested files stay undiscovered by ``*.yml``."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})

    df = read_yaml_directory(_yaml_details(str(tmp_path), "*.yml"))

    assert sorted(df["sourceFilename"].tolist()) == ["top.yml"]
    assert df.iloc[0]["title"] == "Top"


def test_starstar_without_recursive_is_not_full_tree(tmp_path):
    """``**`` without ``recursive=True`` is not full-tree discovery (Python semantics).

    Today ``read_directory`` calls ``glob.glob(pattern)`` with no recursive flag.
    Pin that a ``**/*.yml`` pattern does not return the union of flat + nested files
    the way ``recursive=True`` would.
    """
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})
    _write_yml(tmp_path / "sub" / "deeper" / "leaf.yml", {"title": "Leaf"})

    df = read_yaml_directory(_yaml_details(str(tmp_path), "**/*.yml"))

    # Non-recursive ``**`` behaves like a single path segment — not a full walk.
    # Exact match set may be empty or one-level nested depending on Python/platform;
    # it must not equal the full recursive set {top, deep, leaf}.
    found = set(df["sourceFilename"].tolist()) if len(df) else set()
    full_tree = {"top.yml", "deep.yml", "leaf.yml"}
    assert found != full_tree
    assert "top.yml" not in found or found != full_tree


def test_regexp_filters_basename_after_expand(tmp_path):
    """``regexp`` keeps only basenames that match after glob expand."""
    _write_yml(tmp_path / "keep.yml", {"title": "Keep"})
    _write_yml(tmp_path / "drop.yml", {"title": "Drop"})
    _write_yml(tmp_path / "keep.txt.yml", {"title": "AlsoDrop"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "*.yml", regexp=r"^keep\.yml$")
    )

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Keep"
    assert df.iloc[0]["sourceFilename"] == "keep.yml"


def test_store_fields_on_flat_match(tmp_path):
    """``store_fields`` populate root / directory / filename for a flat match."""
    _write_yml(tmp_path / "meta.yml", {"title": "Meta"})

    details = _yaml_details(str(tmp_path), "*.yml")
    details["store_fields"] = {
        "directory": "sourceDirectory",
        "filename": "sourceFilename",
        "root": "sourceRoot",
    }

    df = read_yaml_directory(details)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["sourceFilename"] == "meta.yml"
    assert row["title"] == "Meta"
    assert "sourceDirectory" in df.columns
    assert "sourceRoot" in df.columns
    assert row["sourceDirectory"] is not None and row["sourceDirectory"] != ""
    assert row["sourceRoot"] is not None and row["sourceRoot"] != ""


# --- CIP-000F recursive discovery -------------------------------------------------


def test_recursive_starstar_matches_full_tree(tmp_path):
    """``recursive: true`` with ``**/*.yml`` discovers nested files."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})
    _write_yml(tmp_path / "sub" / "deeper" / "leaf.yml", {"title": "Leaf"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "**/*.yml", recursive=True)
    )

    assert sorted(df["sourceFilename"].tolist()) == ["deep.yml", "leaf.yml", "top.yml"]
    assert set(df["title"].tolist()) == {"Top", "Deep", "Leaf"}


def test_recursive_false_preserves_non_full_tree(tmp_path):
    """Explicit ``recursive: false`` keeps non-full-tree ``**`` semantics."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})
    _write_yml(tmp_path / "sub" / "deeper" / "leaf.yml", {"title": "Leaf"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "**/*.yml", recursive=False)
    )

    found = set(df["sourceFilename"].tolist()) if len(df) else set()
    assert found != {"top.yml", "deep.yml", "leaf.yml"}


def test_recursive_from_details_when_source_omits_flag(tmp_path):
    """Top-level ``details['recursive']`` applies when source omits the key."""
    _write_yml(tmp_path / "a" / "b" / "c.yml", {"title": "C"})

    details = _yaml_details(str(tmp_path), "**/c.yml")
    details["recursive"] = True

    df = read_yaml_directory(details)

    assert len(df) == 1
    assert df.iloc[0]["title"] == "C"


def test_source_recursive_overrides_details_false(tmp_path):
    """Per-source ``recursive: true`` wins over ``details`` false."""
    _write_yml(tmp_path / "a" / "b" / "c.yml", {"title": "C"})

    details = _yaml_details(str(tmp_path), "**/c.yml", recursive=True)
    details["recursive"] = False

    df = read_yaml_directory(details)

    assert len(df) == 1
    assert df.iloc[0]["title"] == "C"


def test_recursive_regexp_filters_after_expand(tmp_path):
    """``regexp`` still filters basenames after recursive expand."""
    _write_yml(tmp_path / "keep.yml", {"title": "KeepTop"})
    _write_yml(tmp_path / "sub" / "keep.yml", {"title": "KeepNested"})
    _write_yml(tmp_path / "sub" / "drop.yml", {"title": "Drop"})

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path), "**/*.yml", recursive=True, regexp=r"^keep\.yml$"
        )
    )

    assert sorted(df["title"].tolist()) == ["KeepNested", "KeepTop"]


def test_recursive_relative_directory(tmp_path, monkeypatch):
    """Recursive discovery works with a relative source directory."""
    root = tmp_path / "workspace"
    _write_yml(root / "catalog" / "nested" / "item.yml", {"title": "Nested"})
    monkeypatch.chdir(root)

    df = read_yaml_directory(
        _yaml_details("catalog", "**/*.yml", recursive=True)
    )

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Nested"
    assert df.iloc[0]["sourceFilename"] == "item.yml"


def test_recursive_path_outside_allowed_roots_raises(tmp_path):
    """Matched paths outside ``allowed_roots`` still raise (CIP-000A)."""
    jail = tmp_path / "jail"
    outside = tmp_path / "outside"
    _write_yml(jail / "ok.yml", {"title": "Ok"})
    _write_yml(outside / "secret.yml", {"title": "Secret"})
    # Symlink inside jail points at a file outside the jail.
    os.symlink(outside / "secret.yml", jail / "link.yml")

    details = _yaml_details(str(jail), "**/*.yml", recursive=True)
    details["allowed_roots"] = [str(jail.resolve())]

    with pytest.raises(PathEscapeError):
        read_yaml_directory(details)

