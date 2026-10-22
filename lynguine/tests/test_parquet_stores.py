"""CIP-0015 phase 2: parquet Access stores and store_stat."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from lynguine.access.io import (
    PyArrowMissingError,
    _PYARROW_INSTALL,
    parquet_codec_from_file,
    read_data,
    read_parquet,
    store_stat,
    write_data,
    write_parquet,
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


def _parquet_details(tmp_path, **extra):
    details = {
        "type": "parquet",
        "filename": "phrases.parquet",
        "directory": str(tmp_path),
    }
    details.update(extra)
    return details


def test_extract_file_type_parquet():
    assert extract_file_type("phrases.parquet") == "parquet"


def test_parquet_missing_extra_message(tmp_path, monkeypatch):
    import lynguine.access.io as io_mod

    def _boom():
        raise PyArrowMissingError(_PYARROW_INSTALL)

    monkeypatch.setattr(io_mod, "_import_pyarrow", _boom)
    with pytest.raises(PyArrowMissingError, match=r"lynguine\[parquet\]"):
        write_parquet(_phrase_table(), _parquet_details(tmp_path))


def test_unknown_parquet_compress_errors(tmp_path):
    pytest.importorskip("pyarrow")
    with pytest.raises(ValueError, match="Unknown parquet compress codec"):
        write_parquet(
            _phrase_table(),
            _parquet_details(tmp_path, compress="brotli-max"),
        )


def test_parquet_float32_list_round_trip(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")

    details = _parquet_details(tmp_path)
    write_data(_phrase_table(), details)
    path = tmp_path / "phrases.parquet"
    assert path.exists()

    emb_type = pq.read_schema(str(path)).field("embedding").type
    assert pa.types.is_list(emb_type)
    assert pa.types.is_float32(emb_type.value_type)

    loaded = read_parquet(details)
    assert list(loaded["phrase"]) == ["one", "two", "three"]
    assert loaded.iloc[0]["embedding"] == pytest.approx([0.1, 0.2])
    assert loaded.iloc[2]["embedding"] == pytest.approx([0.5, 0.6])

    via_read_data, _finalized = read_data(details)
    assert list(via_read_data["phrase"]) == ["one", "two", "three"]


def test_parquet_smaller_than_gzip_yaml_for_embeddings(tmp_path):
    pytest.importorskip("pyarrow")
    from lynguine.access.io import write_yaml_file

    rng = np.random.default_rng(0)
    table = pd.DataFrame(
        {
            "phrase_id": [f"p{i}" for i in range(64)],
            "phrase": [f"phrase {i}" for i in range(64)],
            "embedding": [rng.random(384, dtype=np.float32).tolist() for _ in range(64)],
        }
    )
    parquet_path = tmp_path / "phrases.parquet"
    write_data(table, _parquet_details(tmp_path))
    gz_path = tmp_path / "phrases.yml.gz"
    write_yaml_file(table.to_dict("records"), str(gz_path), compress="gzip")
    assert parquet_path.stat().st_size < gz_path.stat().st_size


def test_packed_corpus_nested_float32_lists(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")

    packed = pd.DataFrame(
        {
            "Name": ["corpus"],
            "phrases": [["one", "two"]],
            "embeddings": [[[0.1, 0.2], [0.3, 0.4]]],
        }
    )
    details = {
        "type": "parquet",
        "filename": "records.parquet",
        "directory": str(tmp_path),
    }
    write_data(packed, details)
    emb_type = pq.read_schema(str(tmp_path / "records.parquet")).field(
        "embeddings"
    ).type
    assert pa.types.is_list(emb_type)
    assert pa.types.is_list(emb_type.value_type)
    assert pa.types.is_float32(emb_type.value_type.value_type)

    loaded = read_parquet(details)
    assert loaded.iloc[0]["phrases"] == ["one", "two"]
    assert loaded.iloc[0]["embeddings"][0] == pytest.approx([0.1, 0.2])
    assert loaded.iloc[0]["embeddings"][1] == pytest.approx([0.3, 0.4])


def test_store_stat_parquet_missing_and_written(tmp_path):
    pytest.importorskip("pyarrow")

    missing = store_stat(
        {
            "filename": "absent.parquet",
            "directory": str(tmp_path),
            "type": "parquet",
        }
    )
    assert missing["exists"] is False
    assert missing["size_bytes"] == 0
    assert missing["codec"] == "snappy"
    assert missing["logical_type"] == "parquet"
    assert missing["mtime"] is None

    write_data(_phrase_table(), _parquet_details(tmp_path, compress="zstd"))
    st = store_stat(_parquet_details(tmp_path, compress="zstd"))
    assert st["exists"] is True
    assert st["logical_type"] == "parquet"
    assert st["codec"] == "zstd"
    assert st["size_bytes"] > 0
    datetime.fromisoformat(st["mtime"])
    assert parquet_codec_from_file(str(tmp_path / "phrases.parquet")) == "zstd"


def test_store_stat_infers_parquet_from_filename(tmp_path):
    pytest.importorskip("pyarrow")
    write_data(_phrase_table(), _parquet_details(tmp_path))
    inferred = store_stat(
        {"filename": "phrases.parquet", "directory": str(tmp_path)}
    )
    assert inferred["logical_type"] == "parquet"
    assert inferred["codec"] == "snappy"
