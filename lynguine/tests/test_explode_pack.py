"""CIP-0014 explode list fields and pack columns to a corpus row."""

import numpy as np
import pandas as pd
import pytest
import yaml

from lynguine.access.io import (
    _as_pandas,
    _drop_nested_keys,
    _packable_cell,
    _store_index_name,
    explode_list_field,
    omit_columns_frame,
    omit_nested_keys_frame,
    pack_dataframe,
    reshape_for_write,
    write_data,
    write_yaml,
    read_yaml,
)
from lynguine.access.documents.segment import units_to_frame


def _parent_frame():
    return pd.DataFrame(
        {
            "Name": ["doc-a", "doc-b"],
            "filename": ["a.pdf", "b.pdf"],
            "year": [2024, 2025],
            "units": [
                [
                    {"unit_id": "a-0", "text": "hello", "chunk_index": 0},
                    {"unit_id": "a-1", "text": "world", "chunk_index": 1},
                ],
                [
                    {"unit_id": "b-0", "text": "later", "chunk_index": 0},
                ],
            ],
        }
    ).set_index("Name")


def test_explode_list_field_inherits_parent_columns():
    tall = explode_list_field(
        _parent_frame(),
        field="units",
        inherit=["Name", "filename", "year"],
        index="unit_id",
    )
    assert list(tall.index) == ["a-0", "a-1", "b-0"]
    assert tall.index.name == "unit_id"
    assert list(tall.loc["a-1", ["Name", "filename", "text"]]) == [
        "doc-a",
        "a.pdf",
        "world",
    ]
    assert "units" not in tall.columns


def test_explode_empty_list_no_rows():
    df = pd.DataFrame({"Name": ["x"], "units": [[]]}).set_index("Name")
    tall = explode_list_field(df, field="units", inherit=["Name"], index="unit_id")
    assert tall.empty
    assert tall.index.name == "unit_id"


def test_units_to_frame_empty_keeps_columns():
    df = units_to_frame([])
    assert "unit_id" in df.columns
    assert df.empty


def test_explode_duplicate_index_raises():
    df = pd.DataFrame(
        {
            "units": [
                [
                    {"unit_id": "same", "text": "a"},
                    {"unit_id": "same", "text": "b"},
                ]
            ]
        }
    )
    with pytest.raises(ValueError, match="not unique"):
        explode_list_field(df, field="units", index="unit_id")


def test_pack_three_rows_aligned():
    tall = pd.DataFrame(
        {
            "phrase": ["p0", "p1", "p2"],
            "embedding": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            "doc_id": ["a", "a", "b"],
        }
    )
    packed = pack_dataframe(
        tall,
        columns={"phrases": "phrase", "embeddings": "embedding", "doc_ids": "doc_id"},
        index_value="corpus",
        index_name="Name",
    )
    assert list(packed.index) == ["corpus"]
    assert packed.index.name == "Name"
    row = packed.iloc[0]
    assert row["phrases"] == ["p0", "p1", "p2"]
    assert row["embeddings"][1] == [0.3, 0.4]
    assert len(row["phrases"]) == len(row["embeddings"]) == len(row["doc_ids"])


def test_pack_missing_embedding_errors():
    tall = pd.DataFrame(
        {"phrase": ["p0", "p1"], "embedding": [[0.1], None]}
    )
    with pytest.raises(ValueError, match="missing embedding"):
        pack_dataframe(tall, columns={"phrases": "phrase", "embeddings": "embedding"})


def test_pack_drop_incomplete():
    tall = pd.DataFrame(
        {"phrase": ["p0", "p1"], "embedding": [[0.1], None]}
    )
    packed = pack_dataframe(
        tall,
        columns={"phrases": "phrase", "embeddings": "embedding"},
        drop_incomplete=True,
    )
    assert packed.iloc[0]["phrases"] == ["p0"]


def test_pack_drop_incomplete_missing_embedding_column():
    """Save after extract: phrase rows exist, embedding column does not."""
    tall = pd.DataFrame({"phrase": ["p0"], "doc_id": ["a.pdf"]})
    packed = pack_dataframe(
        tall,
        columns={
            "phrases": "phrase",
            "embeddings": "embedding",
            "doc_ids": "doc_id",
        },
        drop_incomplete=True,
    )
    row = packed.iloc[0]
    assert row["phrases"] == []
    assert row["embeddings"] == []
    assert row["doc_ids"] == []


def test_pack_missing_embedding_column_without_drop_still_errors():
    tall = pd.DataFrame({"phrase": ["p0"]})
    with pytest.raises(ValueError, match="pack source columns not present"):
        pack_dataframe(
            tall,
            columns={"phrases": "phrase", "embeddings": "embedding"},
        )


def test_write_data_explode_round_trip(tmp_path):
    details = {
        "type": "yaml",
        "filename": "chunks.yml",
        "directory": str(tmp_path),
        "index": "unit_id",
        "explode": {
            "field": "units",
            "inherit": ["Name", "filename"],
        },
    }
    write_data(_parent_frame().reset_index(), details)
    loaded = read_yaml(
        {"filename": "chunks.yml", "directory": str(tmp_path)}
    )
    assert len(loaded) == 3
    assert set(loaded["unit_id"]) == {"a-0", "a-1", "b-0"}


def test_reshape_for_write_pack_on_store():
    tall = pd.DataFrame(
        {"phrase": ["p0"], "embedding": [[1.0, 2.0]]}
    )
    out = reshape_for_write(
        tall,
        {
            "type": "yaml",
            "index": "Name",
            "pack": {
                "columns": {"phrases": "phrase", "embeddings": "embedding"},
                "index_value": "corpus",
            },
        },
    )
    assert list(out.index) == ["corpus"]
    assert out.iloc[0]["phrases"] == ["p0"]


def test_store_index_name_str_dict_and_missing():
    assert _store_index_name({"index": "unit_id"}) == "unit_id"
    assert _store_index_name({"index": {"name": "Name"}}) == "Name"
    assert _store_index_name({"index": 3}) is None
    assert _store_index_name("not-a-dict") is None


def test_as_pandas_uses_to_pandas():
    class _Wrap:
        def to_pandas(self):
            return pd.DataFrame({"a": [1]})

    assert list(_as_pandas(_Wrap()).columns) == ["a"]
    plain = pd.DataFrame({"b": [2]})
    assert _as_pandas(plain) is plain


def test_explode_field_missing_and_inherit_missing(caplog):
    df = pd.DataFrame({"Name": ["x"], "units": [[{"unit_id": "x-0"}]]})
    with pytest.raises(ValueError, match="not a column"):
        explode_list_field(df, field="missing")
    with caplog.at_level("WARNING"):
        tall = explode_list_field(
            df, field="units", inherit=["filename", "Name"], index="unit_id"
        )
    assert "inherit columns not present, skipping" in caplog.text
    assert "filename" in caplog.text
    assert list(tall.index) == ["x-0"]
    assert tall.loc["x-0", "Name"] == "x"
    assert "filename" not in tall.columns


def test_explode_none_nan_and_ndarray_items():
    df = pd.DataFrame(
        {
            "Name": ["none", "nan", "arr"],
            "units": [
                None,
                np.nan,
                np.array([{"unit_id": "arr-0", "text": "ok"}], dtype=object),
            ],
        }
    )
    tall = explode_list_field(df, field="units", inherit=["Name"], index="unit_id")
    assert list(tall.index) == ["arr-0"]
    assert tall.loc["arr-0", "text"] == "ok"


def test_explode_rejects_non_list_and_non_mapping_items():
    with pytest.raises(ValueError, match="must be a list of mappings"):
        explode_list_field(pd.DataFrame({"units": ["not-a-list"]}), field="units")
    with pytest.raises(ValueError, match="items must be mappings"):
        explode_list_field(pd.DataFrame({"units": [["plain"]]}), field="units")


def test_explode_series_item_to_dict():
    df = pd.DataFrame(
        {"units": [[pd.Series({"unit_id": "s-0", "text": "from-series"})]]}
    )
    tall = explode_list_field(df, field="units", index="unit_id")
    assert tall.loc["s-0", "text"] == "from-series"


def test_explode_index_missing_on_rows():
    df = pd.DataFrame({"units": [[{"text": "no-id"}]]})
    with pytest.raises(ValueError, match="is not a key"):
        explode_list_field(df, field="units", index="unit_id")


def test_packable_cell_ndarray_and_scalar_na():
    assert _packable_cell(np.array([1.0, 2.0])) == [1.0, 2.0]
    assert pd.isna(_packable_cell(np.float64("nan")))
    assert _packable_cell("keep") == "keep"


def test_pack_empty_frame_writes_empty_arrays():
    packed = pack_dataframe(
        pd.DataFrame(columns=["phrase", "embedding"]),
        columns={"phrases": "phrase", "embeddings": "embedding"},
        index_value="corpus",
        index_name="Name",
    )
    assert list(packed.index) == ["corpus"]
    assert packed.iloc[0]["phrases"] == []
    assert packed.iloc[0]["embeddings"] == []
    assert packed.iloc[0]["Name"] == "corpus"


def test_pack_empty_defaults_index_name_and_skips_duplicate_dest():
    unnamed = pack_dataframe(
        pd.DataFrame(columns=["phrase"]),
        columns={"phrases": "phrase"},
        index_name=None,
        index_value="corpus",
    )
    assert unnamed.index.name == "Name"
    assert unnamed.iloc[0]["Name"] == "corpus"
    assert unnamed.iloc[0]["phrases"] == []

    packed = pack_dataframe(
        pd.DataFrame(columns=["Name"]),
        columns={"Name": "Name"},
        index_name="Name",
        index_value="corpus",
    )
    assert list(packed.columns).count("Name") == 1
    assert packed.iloc[0]["Name"] == []


def test_pack_columns_must_be_mapping_and_present():
    tall = pd.DataFrame({"phrase": ["p0"]})
    with pytest.raises(ValueError, match="must be a mapping"):
        pack_dataframe(tall, columns=[])
    with pytest.raises(ValueError, match="source columns not present"):
        pack_dataframe(tall, columns={"phrases": "missing"})


def test_pack_skips_incomplete_check_when_field_absent():
    packed = pack_dataframe(
        pd.DataFrame({"phrase": ["p0", "p1"]}),
        columns={"phrases": "phrase"},
    )
    assert packed.iloc[0]["phrases"] == ["p0", "p1"]


def test_pack_does_not_duplicate_existing_index_column():
    packed = pack_dataframe(
        pd.DataFrame({"Name": ["a"], "phrase": ["p0"]}),
        columns={"Name": "Name", "phrases": "phrase"},
        index_name="Name",
        index_value="corpus",
    )
    assert list(packed.columns).count("Name") == 1
    assert packed.iloc[0]["Name"] == ["a"]


def test_reshape_rejects_bad_explode_and_pack_specs():
    df = pd.DataFrame({"units": [[{"unit_id": "a"}]]})
    with pytest.raises(ValueError, match='mapping with "field"'):
        reshape_for_write(df, {"explode": "units"})
    with pytest.raises(ValueError, match="must include"):
        reshape_for_write(
            pd.DataFrame({"phrase": ["p0"]}),
            {"pack": {"index_value": "corpus"}},
        )


def test_write_yaml_keep_nulls_preserves_nan_as_null(tmp_path):
    df = pd.DataFrame({"model": ["x"], "pca_dim": [np.nan], "note": [None]})
    details = {
        "type": "yaml",
        "filename": "constants.yml",
        "directory": str(tmp_path),
        "keep_nulls": True,
    }
    write_yaml(df, details)
    loaded = yaml.safe_load((tmp_path / "constants.yml").read_text(encoding="utf-8"))
    assert loaded[0]["model"] == "x"
    assert loaded[0]["pca_dim"] is None
    assert loaded[0]["note"] is None


def test_write_yaml_default_drops_nan_keys(tmp_path):
    df = pd.DataFrame({"model": ["x"], "pca_dim": [np.nan]})
    details = {
        "type": "yaml",
        "filename": "constants.yml",
        "directory": str(tmp_path),
    }
    write_yaml(df, details)
    loaded = yaml.safe_load((tmp_path / "constants.yml").read_text(encoding="utf-8"))
    assert loaded[0]["model"] == "x"
    assert "pca_dim" not in loaded[0]


def test_reshape_uses_explode_spec_index_when_store_index_absent():
    df = pd.DataFrame(
        {"units": [[{"unit_id": "u-0", "text": "x"}]]}
    )
    out = reshape_for_write(
        df,
        {"explode": {"field": "units", "index": "unit_id"}},
    )
    assert list(out.index) == ["u-0"]


def test_omit_nested_keys_copies_and_strips_embedding():
    phrases = [[{"phrase": "one", "embedding": [0.1, 0.2], "kind": "benefit"}]]
    df = pd.DataFrame({"extraction_phrases": phrases})
    out = omit_nested_keys_frame(
        df,
        {"omit_nested_keys": {"extraction_phrases": ["embedding"]}},
    )
    assert "embedding" not in out.iloc[0]["extraction_phrases"][0]
    assert out.iloc[0]["extraction_phrases"][0]["phrase"] == "one"
    assert df.iloc[0]["extraction_phrases"][0]["embedding"] == [0.1, 0.2]


def test_omit_columns_drops_embedding_without_touching_source():
    df = pd.DataFrame({"phrase": ["one"], "embedding": [[0.1]]})
    out = omit_columns_frame(df, {"omit_columns": ["embedding"]})
    assert "embedding" not in out.columns
    assert "embedding" in df.columns


def test_write_data_omits_yaml_vectors_and_keeps_source(tmp_path):
    """Extract/embed YAML must not persist 3072-d lists; pack still sees them."""
    phrases = [[{"phrase": "one", "embedding": [0.1, 0.2], "kind": "benefit"}]]
    cache = pd.DataFrame(
        {"extraction_payload": [{"raw": "x"}], "extraction_phrases": phrases}
    )
    write_data(
        cache,
        {
            "type": "yaml",
            "filename": "cache.yml",
            "directory": str(tmp_path),
            "omit_nested_keys": {"extraction_phrases": ["embedding"]},
        },
    )
    tall = pd.DataFrame({"phrase": ["one"], "embedding": [[0.1, 0.2]]})
    write_data(
        tall,
        {
            "type": "yaml",
            "filename": "phrases.yml",
            "directory": str(tmp_path),
            "omit_columns": ["embedding"],
        },
    )
    cached = yaml.safe_load((tmp_path / "cache.yml").read_text(encoding="utf-8"))
    assert "embedding" not in cached[0]["extraction_phrases"][0]
    assert cache.iloc[0]["extraction_phrases"][0]["embedding"] == [0.1, 0.2]
    written = yaml.safe_load((tmp_path / "phrases.yml").read_text(encoding="utf-8"))
    assert "embedding" not in written[0]
    assert written[0]["phrase"] == "one"
    assert tall.iloc[0]["embedding"] == [0.1, 0.2]


def test_omit_nested_keys_guards_string_key_and_ndarray_cells():
    assert omit_nested_keys_frame(pd.DataFrame({"x": [1]}), None) is not None
    df = pd.DataFrame({"phrase": ["one"]})
    assert omit_nested_keys_frame(df, "not-a-mapping") is df
    assert omit_nested_keys_frame(
        df, {"omit_nested_keys": ["embedding"]}
    ) is df
    skipped = omit_nested_keys_frame(
        df, {"omit_nested_keys": {"extraction_phrases": ["embedding"]}}
    )
    assert list(skipped.columns) == ["phrase"]

    arr = np.array(
        [{"phrase": "one", "embedding": [0.1], "kind": "benefit"}],
        dtype=object,
    )
    nested = pd.DataFrame({"extraction_phrases": [arr]})
    out = omit_nested_keys_frame(
        nested,
        {"omit_nested_keys": {"extraction_phrases": "embedding"}},
    )
    cell = out.iloc[0]["extraction_phrases"][0]
    assert "embedding" not in cell
    assert cell["phrase"] == "one"
    assert arr[0]["embedding"] == [0.1]
    assert _drop_nested_keys("plain", {"embedding"}) == "plain"


def test_omit_columns_noop_when_names_absent():
    df = pd.DataFrame({"phrase": ["one"], "embedding": [[0.1]]})
    assert omit_columns_frame(df, None) is df
    assert omit_columns_frame(df, {}) is df
    assert omit_columns_frame(df, {"omit_columns": []}) is df
    kept = omit_columns_frame(df, {"omit_columns": ["missing"]})
    assert kept is df
    assert "embedding" in df.columns


def test_pack_drop_incomplete_all_rows_writes_empty_arrays():
    packed = pack_dataframe(
        pd.DataFrame({"phrase": ["p0"], "embedding": [None]}),
        columns={"phrases": "phrase", "embeddings": "embedding"},
        drop_incomplete=True,
    )
    assert packed.iloc[0]["phrases"] == []
    assert packed.iloc[0]["embeddings"] == []
