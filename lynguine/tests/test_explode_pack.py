"""CIP-0014 explode list fields and pack columns to a corpus row."""

import pandas as pd
import pytest

from lynguine.access.io import (
    explode_list_field,
    pack_dataframe,
    reshape_for_write,
    write_data,
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
