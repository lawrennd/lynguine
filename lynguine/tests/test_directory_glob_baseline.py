"""Baseline tests for current directory-glob behaviour (CIP-000F prerequisite).

These pin today's flat, non-recursive discovery before recursive / fields land.
Do not mock ``glob.glob`` here — use real ``tmp_path`` trees.
"""

from __future__ import annotations

import pytest
import yaml

from lynguine.access.io import read_yaml_directory


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


@pytest.mark.xfail(
    reason=(
        "read_directory rejoins directory onto glob matches; relative directory "
        "becomes catalog/catalog/item.yml (backlog 2026-10-11_read-directory-relative-glob-double-join)"
    ),
    strict=True,
)
def test_flat_glob_relative_directory(tmp_path, monkeypatch):
    """Relative ``directory`` without ``allowed_roots`` should still resolve matches.

    Today this double-joins; the xfail documents current breakage until the bug fix.
    """
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

