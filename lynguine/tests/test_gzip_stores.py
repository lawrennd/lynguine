"""CIP-0015 gzip YAML/JSON stores and store_stat."""

import gzip
from datetime import datetime

import pandas as pd
import pytest
import yaml

from lynguine.access.io import (
    gzip_codec_from_name,
    open_text_store,
    read_json,
    read_yaml,
    read_yaml_file,
    resolve_text_codec,
    store_stat,
    write_data,
    write_json_file,
    write_yaml_file,
)
from lynguine.util.misc import extract_file_type


def _phrase_table():
    return pd.DataFrame(
        {
            "phrase_id": ["p0", "p1", "p2"],
            "phrase": ["one", "two", "three"],
            "embedding": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
        }
    )


def test_extract_file_type_strips_gz():
    assert extract_file_type("phrases.yml.gz") == "yaml"
    assert extract_file_type("cache.json.gz") == "json"


def test_yaml_gz_round_trip_smaller_than_plain(tmp_path):
    details_gz = {
        "type": "yaml",
        "filename": "phrases.yml.gz",
        "directory": str(tmp_path),
    }
    write_data(_phrase_table(), details_gz)
    gz_path = tmp_path / "phrases.yml.gz"
    plain_path = tmp_path / "phrases.yml"
    write_yaml_file(_phrase_table().to_dict("records"), str(plain_path))

    assert gz_path.exists()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        loaded_raw = yaml.safe_load(fh)
    assert len(loaded_raw) == 3
    loaded = read_yaml(details_gz)
    assert len(loaded) == 3
    assert list(loaded["phrase"]) == ["one", "two", "three"]
    assert gz_path.stat().st_size < plain_path.stat().st_size


def test_yml_with_gzip_bytes_is_error(tmp_path):
    path = tmp_path / "phrases.yml"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        yaml.safe_dump([{"a": 1}], fh)
    with pytest.raises(ValueError, match="does not end in .gz"):
        read_yaml_file(str(path))


def test_compress_gzip_without_gz_suffix_errors(tmp_path):
    with pytest.raises(ValueError, match="requires a .gz filename"):
        write_yaml_file(
            [{"a": 1}],
            str(tmp_path / "phrases.yml"),
            compress="gzip",
        )


def test_store_stat_missing_plain_and_gzip(tmp_path):
    missing = store_stat(
        {"filename": "absent.yml.gz", "directory": str(tmp_path), "type": "yaml"}
    )
    assert missing["exists"] is False
    assert missing["size_bytes"] == 0
    assert missing["codec"] == "gzip"
    assert missing["logical_type"] == "yaml"
    assert missing["mtime"] is None

    plain = tmp_path / "plain.yml"
    write_yaml_file([{"a": 1}], str(plain))
    st_plain = store_stat(
        {"filename": "plain.yml", "directory": str(tmp_path), "type": "yaml"}
    )
    assert st_plain["exists"] is True
    assert st_plain["codec"] is None
    assert st_plain["size_bytes"] > 0
    datetime.fromisoformat(st_plain["mtime"])

    write_data(
        _phrase_table(),
        {"type": "yaml", "filename": "cache.yml.gz", "directory": str(tmp_path)},
    )
    st_gz = store_stat(
        {"filename": "cache.yml.gz", "directory": str(tmp_path), "type": "yaml"}
    )
    assert st_gz["codec"] == "gzip"
    assert st_gz["exists"] is True
    datetime.fromisoformat(st_gz["mtime"])


def test_gzip_codec_from_name_accepts_gzip_suffix():
    assert gzip_codec_from_name("cache.json.gzip") == "gzip"
    assert gzip_codec_from_name("phrases.yml") is None


def test_unknown_compress_codec_errors():
    with pytest.raises(ValueError, match="Unknown compress codec"):
        resolve_text_codec("phrases.yml.gz", compress="brotli")


def test_missing_yml_is_not_treated_as_gzip(tmp_path):
    missing = tmp_path / "absent.yml"
    with pytest.raises(FileNotFoundError):
        read_yaml_file(str(missing))


def test_open_text_store_accepts_text_mode(tmp_path):
    path = tmp_path / "phrases.yml.gz"
    write_yaml_file([{"a": 1}], str(path), compress="gzip")
    with open_text_store(str(path), "rt") as stream:
        loaded = yaml.safe_load(stream)
    assert loaded == [{"a": 1}]


def test_yaml_gz_honours_compress_details_and_level(tmp_path):
    details = {
        "type": "yaml",
        "filename": "phrases.yml.gz",
        "directory": str(tmp_path),
        "compress": "gzip",
        "compress_level": 1,
    }
    write_data(_phrase_table(), details)
    loaded = read_yaml(details)
    assert list(loaded["phrase"]) == ["one", "two", "three"]


def test_json_gz_round_trip(tmp_path):
    import json

    details = {
        "type": "json",
        "filename": "cache.json.gz",
        "directory": str(tmp_path),
        "compress": "gzip",
    }
    write_data(_phrase_table(), details)
    loaded = read_json(details)
    assert list(loaded["phrase"]) == ["one", "two", "three"]
    with gzip.open(tmp_path / "cache.json.gz", "rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    assert len(raw) == 3


def test_store_stat_infers_logical_type_and_unknown(tmp_path):
    gz = tmp_path / "cache.yml.gz"
    write_yaml_file([{"a": 1}], str(gz))
    inferred = store_stat({"filename": "cache.yml.gz", "directory": str(tmp_path)})
    assert inferred["logical_type"] == "yaml"
    assert inferred["codec"] == "gzip"

    unknown = store_stat(
        {"filename": "notes.bin", "directory": str(tmp_path), "role": "cache"}
    )
    assert unknown["exists"] is False
    assert unknown["logical_type"] is None
    assert unknown["role"] == "cache"


def test_write_json_file_gzip(tmp_path):
    path = tmp_path / "rows.json.gz"
    write_json_file([{"a": 1}], str(path), compress="gzip", compress_level=9)
    loaded = read_json(
        {"filename": "rows.json.gz", "directory": str(tmp_path), "type": "json"}
    )
    assert loaded.iloc[0]["a"] == 1
