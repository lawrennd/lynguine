"""Directory-glob behaviour tests (CIP-000F baseline + recursive discovery).

Do not mock ``glob.glob`` here — use real ``tmp_path`` trees.
"""

from __future__ import annotations

import os

import pytest
import yaml

import pandas as pd

from lynguine.access.io import (
    _matches_exclude,
    read_directory,
    read_yaml_directory,
    update_store_fields,
)
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


def test_include_start_directory_false_omits_start_dir_matches(tmp_path):
    """``include_start_directory: false`` keeps nested files only."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})
    _write_yml(tmp_path / "sub" / "deeper" / "leaf.yml", {"title": "Leaf"})

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path),
            "**/*.yml",
            recursive=True,
            include_start_directory=False,
        )
    )

    assert sorted(df["sourceFilename"].tolist()) == ["deep.yml", "leaf.yml"]
    assert set(df["title"].tolist()) == {"Deep", "Leaf"}


def test_include_start_directory_default_keeps_start_dir(tmp_path):
    """Default ``include_start_directory`` keeps start-directory matches."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "deep.yml", {"title": "Deep"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "**/*.yml", recursive=True)
    )

    assert "top.yml" in df["sourceFilename"].tolist()


def test_include_start_directory_false_non_recursive(tmp_path):
    """Descendants-only also applies to flat globs (start-dir file omitted)."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "sub" / "nested.yml", {"title": "Nested"})

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path),
            "*.yml",
            include_start_directory=False,
        )
    )

    assert len(df) == 0


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


# --- CIP-000F field projection ----------------------------------------------------


def test_fields_projects_top_level_keys(tmp_path):
    """``fields`` keeps listed keys and drops the rest before normalize."""
    _write_yml(
        tmp_path / "rich.yml",
        {
            "title": "Catalog",
            "description": "Desc",
            "extra": 99,
            "nested": {"x": 1},
        },
    )

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "*.yml", fields=["title", "description"])
    )

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Catalog"
    assert df.iloc[0]["description"] == "Desc"
    assert "extra" not in df.columns
    assert "nested" not in df.columns
    assert "nested.x" not in df.columns


def test_fields_missing_keys_are_null(tmp_path):
    """Missing listed keys appear as null/NaN after normalize."""
    _write_yml(tmp_path / "partial.yml", {"title": "OnlyTitle"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "*.yml", fields=["title", "missing"])
    )

    assert df.iloc[0]["title"] == "OnlyTitle"
    assert pd.isna(df.iloc[0]["missing"])


def test_fields_absent_keeps_full_document(tmp_path):
    """Absent ``fields`` preserves full-document normalize behaviour."""
    _write_yml(
        tmp_path / "full.yml",
        {"title": "T", "extra": 1, "nested": {"x": 2}},
    )

    df = read_yaml_directory(_yaml_details(str(tmp_path), "*.yml"))

    assert df.iloc[0]["title"] == "T"
    assert df.iloc[0]["extra"] == 1
    assert "nested.x" in df.columns


def test_fields_from_details_when_source_omits(tmp_path):
    """Top-level ``details['fields']`` applies when source omits the key."""
    _write_yml(tmp_path / "a.yml", {"title": "T", "noise": True})

    details = _yaml_details(str(tmp_path), "*.yml")
    details["fields"] = ["title"]

    df = read_yaml_directory(details)

    assert list(df["title"]) == ["T"]
    assert "noise" not in df.columns


def test_source_fields_overrides_details(tmp_path):
    """Per-source ``fields`` wins over ``details``."""
    _write_yml(tmp_path / "a.yml", {"title": "T", "description": "D"})

    details = _yaml_details(str(tmp_path), "*.yml", fields=["title"])
    details["fields"] = ["description"]

    df = read_yaml_directory(details)

    assert "title" in df.columns
    assert "description" not in df.columns


def test_fields_preserves_store_fields(tmp_path):
    """Path ``store_fields`` are still appended after projection."""
    _write_yml(tmp_path / "meta.yml", {"title": "Meta", "noise": 1})

    details = _yaml_details(str(tmp_path), "*.yml", fields=["title"])
    details["store_fields"] = {
        "directory": "sourceDirectory",
        "filename": "sourceFilename",
        "root": "sourceRoot",
    }

    df = read_yaml_directory(details)

    assert df.iloc[0]["title"] == "Meta"
    assert df.iloc[0]["sourceFilename"] == "meta.yml"
    assert "noise" not in df.columns
    assert "sourceDirectory" in df.columns
    assert "sourceRoot" in df.columns


def test_fields_store_fields_name_collision_still_errors(tmp_path):
    """Projected content that already uses a store field name still errors."""
    _write_yml(tmp_path / "clash.yml", {"title": "T", "sourceFilename": "bad"})

    details = _yaml_details(
        str(tmp_path), "*.yml", fields=["title", "sourceFilename"]
    )

    with pytest.raises(ValueError, match="sourceFilename"):
        read_yaml_directory(details)


def test_fields_non_mapping_warns_without_crash(tmp_path, caplog):
    """Non-mapping payloads warn and yield null projected fields (no crash)."""
    plain = tmp_path / "note.txt"
    plain.write_text("not yaml mapping", encoding="utf-8")

    details = update_store_fields(
        _yaml_details(str(tmp_path), "*.txt", fields=["title", "description"])
    )

    with caplog.at_level("WARNING"):
        df = read_directory(
            details,
            filereader=lambda filename: open(filename, encoding="utf-8").read(),
        )

    assert len(df) == 1
    assert pd.isna(df.iloc[0]["title"])
    assert pd.isna(df.iloc[0]["description"])
    assert df.iloc[0]["sourceFilename"] == "note.txt"
    assert "not a mapping" in caplog.text


def test_fields_with_recursive_catalog(tmp_path):
    """Recursive discovery plus field projection for nested catalog files."""
    _write_yml(
        tmp_path / "apps" / "one" / "config.yml",
        {"title": "One", "description": "D1", "input": {"type": "csv"}},
    )
    _write_yml(
        tmp_path / "apps" / "two" / "config.yml",
        {"title": "Two", "description": "D2", "review": {"a": 1}},
    )

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path),
            "**/config.yml",
            recursive=True,
            fields=["title", "description"],
        )
    )

    assert sorted(df["title"].tolist()) == ["One", "Two"]
    assert "input" not in df.columns
    assert "input.type" not in df.columns
    assert "review" not in df.columns
    assert "review.a" not in df.columns


# --- CIP-0018 exclude --------------------------------------------------------


def test_matches_exclude_prefix_starstar():
    assert _matches_exclude("today/_referia.yml", ["today/**"])
    assert _matches_exclude("today/nested/x.yml", ["today/**"])
    assert _matches_exclude("today", ["today/**"])
    assert not _matches_exclude("work/today.yml", ["today/**"])
    assert not _matches_exclude("applications/a.yml", ["today/**"])


def test_exclude_omits_listed_trees_keeps_others(tmp_path):
    """``exclude: [today/**]`` drops that tree and keeps unlisted nested files."""
    _write_yml(tmp_path / "work" / "item.yml", {"title": "Work"})
    _write_yml(tmp_path / "today" / "view.yml", {"title": "Today"})
    _write_yml(tmp_path / "today" / "nested" / "deep.yml", {"title": "Deep"})
    _write_yml(tmp_path / "year" / "view.yml", {"title": "Year"})

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path),
            "**/*.yml",
            recursive=True,
            include_start_directory=False,
            exclude=["today/**"],
        )
    )

    titles = sorted(df["title"].tolist())
    assert titles == ["Work", "Year"]


def test_exclude_default_keeps_full_match_set(tmp_path):
    """Absent exclude leaves CIP-000F discovery unchanged."""
    _write_yml(tmp_path / "top.yml", {"title": "Top"})
    _write_yml(tmp_path / "today" / "view.yml", {"title": "Today"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "**/*.yml", recursive=True)
    )

    assert sorted(df["title"].tolist()) == ["Today", "Top"]


def test_exclude_with_include_start_directory_false(tmp_path):
    """Start-dir omit stays on ``include_start_directory``; exclude is extra."""
    _write_yml(tmp_path / "root.yml", {"title": "Root"})
    _write_yml(tmp_path / "work" / "item.yml", {"title": "Work"})
    _write_yml(tmp_path / "today" / "view.yml", {"title": "Today"})

    df = read_yaml_directory(
        _yaml_details(
            str(tmp_path),
            "**/*.yml",
            recursive=True,
            include_start_directory=False,
            exclude=["today/**"],
        )
    )

    assert sorted(df["title"].tolist()) == ["Work"]


def test_exclude_string_is_accepted(tmp_path):
    _write_yml(tmp_path / "keep.yml", {"title": "Keep"})
    _write_yml(tmp_path / "skip.tmp.yml", {"title": "Skip"})

    df = read_yaml_directory(
        _yaml_details(str(tmp_path), "*.yml", exclude="*.tmp.yml")
    )

    assert df["title"].tolist() == ["Keep"]

