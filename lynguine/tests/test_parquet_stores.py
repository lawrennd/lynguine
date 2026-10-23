"""CIP-0015 phase 2: parquet Access stores and store_stat."""

from datetime import datetime
import json

import numpy as np
import pandas as pd
import pytest

from lynguine.access.io import (
    PyArrowMissingError,
    _PYARROW_INSTALL,
    _arrow_list_type,
    _cell_as_nested_list,
    _cell_from_arrow,
    _import_pyarrow,
    _is_missing_cell,
    _json_cell_default,
    _list_column_arrow_types,
    _object_column_to_arrow,
    _parquet_compression,
    _python_lists_from_parquet,
    parquet_codec_from_file,
    read_auto,
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


def test_parquet_plotly_dict_column_json_round_trip(tmp_path):
    pytest.importorskip("pyarrow")
    table = pd.DataFrame(
        {
            "Name": ["corpus"],
            "vq_spec": [
                {
                    "data": [{"x": [0.0], "y": [1.0]}],
                    "layout": {"title": {"text": "walk"}},
                    "frames": [{"name": "0", "data": [{"x": [0.0]}]}],
                }
            ],
        }
    )
    details = _parquet_details(tmp_path)
    write_data(table, details)
    loaded = read_parquet(details)
    raw = loaded.iloc[0]["vq_spec"]
    assert isinstance(raw, str)
    spec = json.loads(raw)
    assert spec["layout"]["title"]["text"] == "walk"
    assert spec["frames"][0]["name"] == "0"


def test_json_cell_default_numpy_and_reject_unknown():
    assert _json_cell_default(np.array([0.25, 0.75])) == [0.25, 0.75]
    assert _json_cell_default(np.float64(1.5)) == 1.5
    assert _json_cell_default(np.int64(3)) == 3
    with pytest.raises(TypeError, match="not JSON serializable"):
        _json_cell_default(object())


def test_is_missing_cell_none_na_and_nan(monkeypatch):
    assert _is_missing_cell(None) is True
    assert _is_missing_cell(pd.NA) is True
    assert _is_missing_cell(float("nan")) is True
    assert _is_missing_cell(np.nan) is True
    assert _is_missing_cell({"layout": {}}) is False
    assert _is_missing_cell("already-json") is False

    import lynguine.access.io as io_mod

    def _isnan_raises(_value):
        raise TypeError("not a real float")

    monkeypatch.setattr(io_mod.np, "isnan", _isnan_raises)
    assert io_mod._is_missing_cell(1.0) is False


def test_object_column_to_arrow_missing_str_and_numpy_dict(tmp_path):
    pa = pytest.importorskip("pyarrow")
    table = pd.DataFrame(
        {
            "Name": ["a", "b", "c", "d"],
            "vq_spec": [
                None,
                {
                    "data": [{"x": np.array([0.0])}],
                    "layout": {"n": np.int64(1), "f": np.float64(2.5)},
                },
                '{"already": true}',
                float("nan"),
            ],
        }
    )
    write_data(table, _parquet_details(tmp_path))
    loaded = read_parquet(_parquet_details(tmp_path))
    assert loaded.iloc[0]["vq_spec"] is None
    spec = json.loads(loaded.iloc[1]["vq_spec"])
    assert spec["data"][0]["x"] == [0.0]
    assert spec["layout"] == {"n": 1, "f": 2.5}
    assert json.loads(loaded.iloc[2]["vq_spec"]) == {"already": True}
    assert loaded.iloc[3]["vq_spec"] is None

    encoded = _object_column_to_arrow(pd.Series([None, pd.NA]), pa)
    assert encoded.to_pylist() == [None, None]
    plain = _object_column_to_arrow(pd.Series(["keep"]), pa)
    assert plain.to_pylist() == ["keep"]


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


def test_import_pyarrow_wraps_import_error(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "pyarrow", None)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", None)
    with pytest.raises(PyArrowMissingError, match=r"lynguine\[parquet\]"):
        _import_pyarrow()


def test_read_parquet_missing_extra_message(tmp_path, monkeypatch):
    import lynguine.access.io as io_mod

    def _boom():
        raise PyArrowMissingError(_PYARROW_INSTALL)

    monkeypatch.setattr(io_mod, "_import_pyarrow", _boom)
    with pytest.raises(PyArrowMissingError, match="poetry install --extras parquet"):
        read_parquet(_parquet_details(tmp_path))


def test_parquet_compression_none_and_non_mapping():
    assert _parquet_compression(None) == "snappy"
    assert _parquet_compression({}) == "snappy"
    assert _parquet_compression({"compress": "NONE"}) == "none"
    assert _parquet_compression({"compress": "uncompressed"}) == "none"
    assert _parquet_compression({"compress": "gzip"}) == "gzip"


def test_cell_helpers_normalise_numpy_and_nulls():
    assert _cell_as_nested_list(None) is None
    assert _cell_as_nested_list(np.array([1.0, 2.0])) == [1.0, 2.0]
    assert _cell_as_nested_list(np.float64("nan")) is None
    assert _cell_as_nested_list(float("nan")) is None
    assert _cell_as_nested_list(np.int64(3)) == 3
    assert _cell_as_nested_list(np.float32(1.5)) == pytest.approx(1.5)
    assert _cell_from_arrow(None) is None
    assert _cell_from_arrow((np.float32(0.1), np.int64(2))) == pytest.approx([0.1, 2])
    assert _cell_from_arrow(np.array([0.5, 1.5])) == pytest.approx([0.5, 1.5])
    nested = _cell_from_arrow(np.array([[0.1], [0.2]], dtype=object))
    assert nested[0] == pytest.approx([0.1])
    assert nested[1] == pytest.approx([0.2])
    assert _cell_from_arrow("keep") == "keep"
    converted = _python_lists_from_parquet(
        pd.DataFrame({"empty": [None, None], "vals": [[0.1], [0.2]]})
    )
    assert converted.iloc[0]["vals"] == pytest.approx([0.1])
    assert converted.iloc[0]["empty"] is None


def test_arrow_list_type_inference_edges():
    pa = pytest.importorskip("pyarrow")
    assert _arrow_list_type("not-a-list", pa) is None
    assert _arrow_list_type([], pa) is None
    inferred = _arrow_list_type(np.array([0.1, 0.2]), pa)
    assert pa.types.is_list(inferred)
    assert pa.types.is_float32(inferred.value_type)
    nested = _arrow_list_type([np.array([0.1, 0.2])], pa)
    assert pa.types.is_list(nested)
    assert pa.types.is_list(nested.value_type)
    assert _arrow_list_type([["a", "b"]], pa) is None
    assert _arrow_list_type([{"k": 1}], pa) is None
    assert pa.types.is_string(_arrow_list_type(["one", "two"], pa).value_type)


def test_list_columns_declared_dict_and_list():
    pa = pytest.importorskip("pyarrow")
    df = pd.DataFrame(
        {
            "embedding": [[0.1, 0.2]],
            "other": [1],
            "empty": [None],
        }
    )
    as_list = _list_column_arrow_types(
        df, {"list_columns": ["embedding", "absent"]}, pa
    )
    assert "embedding" in as_list
    assert "absent" not in as_list
    as_dict = _list_column_arrow_types(
        df, {"list_columns": {"embedding": "float32"}}, pa
    )
    assert "embedding" in as_dict
    skipped = _list_column_arrow_types(
        pd.DataFrame({"embedding": [None, None]}), {}, pa
    )
    assert skipped == {}


def test_named_index_and_to_pandas_wrapper_round_trip(tmp_path):
    pytest.importorskip("pyarrow")

    class _Wrap:
        def to_pandas(self):
            return _phrase_table().set_index("phrase_id")

    details = _parquet_details(tmp_path)
    write_parquet(_Wrap(), details)
    loaded = read_parquet(details)
    assert "phrase_id" in loaded.columns
    assert list(loaded["phrase_id"]) == ["p0", "p1", "p2"]
    assert loaded.iloc[1]["embedding"] == pytest.approx([0.3, 0.4])


def test_read_auto_parquet_and_uncompressed_codec(tmp_path):
    pytest.importorskip("pyarrow")
    details = _parquet_details(tmp_path, compress="uncompressed")
    write_data(_phrase_table(), details)
    loaded = read_auto(
        {"filename": "phrases.parquet", "directory": str(tmp_path)}
    )
    assert list(loaded["phrase"]) == ["one", "two", "three"]
    codec = parquet_codec_from_file(str(tmp_path / "phrases.parquet"))
    assert codec in {"uncompressed", "none", "uncompressed_none"}


def test_declared_list_columns_write_even_when_empty(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    details = _parquet_details(tmp_path, list_columns=["embedding"])
    table = pd.DataFrame({"phrase_id": ["p0"], "embedding": [None]})
    write_parquet(table, details)
    emb_type = pq.read_schema(str(tmp_path / "phrases.parquet")).field("embedding").type
    assert pa.types.is_list(emb_type)
    assert pa.types.is_float32(emb_type.value_type)
    loaded = read_parquet(details)
    assert loaded.iloc[0]["embedding"] is None


def test_numpy_embedding_cells_round_trip(tmp_path):
    pytest.importorskip("pyarrow")
    details = _parquet_details(tmp_path)
    table = pd.DataFrame(
        {
            "phrase_id": ["p0"],
            "embedding": [np.array([0.25, 0.75], dtype=np.float32)],
        }
    )
    write_parquet(table, details)
    loaded = read_parquet(details)
    assert loaded.iloc[0]["embedding"] == pytest.approx([0.25, 0.75])


def test_store_stat_parquet_without_pyarrow_keeps_declared_codec(
    tmp_path, monkeypatch
):
    pytest.importorskip("pyarrow")
    import lynguine.access.io as io_mod

    write_data(_phrase_table(), _parquet_details(tmp_path, compress="gzip"))

    def _boom(*_args, **_kwargs):
        raise PyArrowMissingError(_PYARROW_INSTALL)

    monkeypatch.setattr(io_mod, "parquet_codec_from_file", _boom)
    st = store_stat(_parquet_details(tmp_path, compress="gzip"))
    assert st["exists"] is True
    assert st["codec"] == "gzip"
    assert st["logical_type"] == "parquet"


def test_parquet_codec_from_file_mixed_and_empty(monkeypatch):
    import lynguine.access.io as io_mod

    class _Col:
        def __init__(self, compression):
            self.compression = compression

    class _Group:
        def __init__(self, compressions):
            self._cs = compressions
            self.num_columns = len(compressions)

        def column(self, j):
            return _Col(self._cs[j])

    class _Meta:
        def __init__(self, groups):
            self._groups = groups
            self.num_row_groups = len(groups)

        def row_group(self, i):
            return self._groups[i]

    class _Pq:
        def __init__(self, meta):
            self._meta = meta

        def read_metadata(self, _filename):
            return self._meta

    monkeypatch.setattr(
        io_mod,
        "_import_pyarrow",
        lambda: (None, _Pq(_Meta([_Group(["SNAPPY", "ZSTD"])]))),
    )
    assert parquet_codec_from_file("phrases.parquet") == "snappy,zstd"

    monkeypatch.setattr(
        io_mod, "_import_pyarrow", lambda: (None, _Pq(_Meta([])))
    )
    assert parquet_codec_from_file("phrases.parquet") is None
