"""Tests for CIP-0010 wide_flatten / view / unflatten."""

from __future__ import annotations

import pandas as pd
import pytest

from lynguine.access.io import (
    compose_wide_column_name,
    parse_wide_column_name,
    read_data,
    wide_flatten_dataframe,
    wide_unflatten_dataframe,
    wide_view_get,
    wide_view_set,
)
from lynguine.assess.data import CustomDataFrame


def _sample_frame():
    return pd.DataFrame(
        {
            "title": ["A", "B"],
            "complete": [True, False],
            "extra": ["x", "y"],
        },
        index=["grant/a", "grant/b"],
    )


def test_wide_flatten_happy_path_index_then_field():
    wide = wide_flatten_dataframe(_sample_frame(), columns=["title", "complete"])

    assert len(wide) == 1
    assert wide.iloc[0]["flattenKeys"] == ["grant/a", "grant/b"]
    assert list(c for c in wide.columns if c != "flattenKeys") == [
        "grant/a_title",
        "grant/a_complete",
        "grant/b_title",
        "grant/b_complete",
    ]
    assert wide.iloc[0]["grant/a_title"] == "A"
    assert wide.iloc[0]["grant/b_complete"] is False or wide.iloc[0]["grant/b_complete"] == False


def test_wide_flatten_order_field_then_index():
    wide = wide_flatten_dataframe(
        _sample_frame(),
        order="field_then_index",
        columns=["title", "complete"],
    )

    assert wide.iloc[0]["flattenKeys"] == ["grant/a", "grant/b"]
    assert list(c for c in wide.columns if c != "flattenKeys") == [
        "title_grant/a",
        "title_grant/b",
        "complete_grant/a",
        "complete_grant/b",
    ]
    assert wide.iloc[0]["title_grant/b"] == "B"


def test_wide_flatten_columns_subset_drops_others():
    wide = wide_flatten_dataframe(_sample_frame(), columns=["title"])

    value_cols = [c for c in wide.columns if c != "flattenKeys"]
    assert value_cols == ["grant/a_title", "grant/b_title"]
    assert "extra" not in "".join(value_cols)


def test_wide_flatten_custom_keys_field():
    wide = wide_flatten_dataframe(_sample_frame(), columns=["title"], keys_field="ids")
    assert "ids" in wide.columns
    assert "flattenKeys" not in wide.columns
    assert wide.iloc[0]["ids"] == ["grant/a", "grant/b"]


def test_wide_flatten_omit_keys_field():
    wide = wide_flatten_dataframe(
        _sample_frame(), columns=["title"], keys_field=None
    )
    assert "flattenKeys" not in wide.columns
    assert list(wide.columns) == ["grant/a_title", "grant/b_title"]


def test_wide_flatten_duplicate_index_raises():
    df = pd.DataFrame({"title": ["A", "B"]}, index=["same", "same"])

    with pytest.raises(ValueError, match="unique index"):
        wide_flatten_dataframe(df)


def test_wide_flatten_empty_frame_one_empty_row():
    df = pd.DataFrame(columns=["title", "complete"])
    wide = wide_flatten_dataframe(df)

    assert len(wide) == 1
    assert wide.iloc[0]["flattenKeys"] == []
    assert list(c for c in wide.columns if c != "flattenKeys") == []


def test_wide_flatten_str_coercion_of_names():
    df = pd.DataFrame({"count": [1, 2]}, index=[10, 20])
    wide = wide_flatten_dataframe(df, separator="-")

    assert wide.iloc[0]["flattenKeys"] == [10, 20]
    assert wide.iloc[0]["10-count"] == 1


def test_wide_flatten_separator_in_index_raises():
    df = pd.DataFrame({"title": ["A"]}, index=["grant_a"])

    with pytest.raises(ValueError, match="separator"):
        wide_flatten_dataframe(df, separator="_")


def test_wide_flatten_invalid_order_raises():
    with pytest.raises(ValueError, match="order"):
        wide_flatten_dataframe(_sample_frame(), order="sideways")


def test_wide_flatten_missing_columns_raises():
    with pytest.raises(ValueError, match="columns not present"):
        wide_flatten_dataframe(_sample_frame(), columns=["missing"])


def test_parse_and_compose_wide_names():
    keys = ["grant/a", "grant/b"]
    assert compose_wide_column_name("grant/a", "title") == "grant/a_title"
    assert parse_wide_column_name(
        "grant/b_complete", keys=keys, fields=["title", "complete"]
    ) == ("grant/b", "complete")
    assert parse_wide_column_name(
        "title_grant/a",
        keys=keys,
        fields=["title"],
        order="field_then_index",
    ) == ("grant/a", "title")


def test_wide_view_get_set_on_dataframe_preserves_shape():
    df = _sample_frame().copy()
    shape_before = df.shape
    keys = list(df.index)

    assert wide_view_get(df, "grant/a_complete", keys=keys, fields=["complete"]) == True
    wide_view_set(df, "grant/b_complete", True, keys=keys, fields=["complete"])
    assert df.at["grant/b", "complete"] == True
    assert df.shape == shape_before


def test_wide_view_get_set_on_customdataframe():
    tall = pd.DataFrame(
        {"title": ["A", "B"], "complete": [False, False]},
        index=["grant/a", "grant/b"],
    )
    cdf = CustomDataFrame(tall, colspecs={"output": ["title", "complete"]})
    keys = list(cdf.index)
    shape_before = cdf.to_pandas().shape

    wide_view_set(
        cdf, "grant/a_complete", True, keys=keys, fields=["title", "complete"]
    )
    assert (
        wide_view_get(
            cdf, "grant/a_complete", keys=keys, fields=["title", "complete"]
        )
        is True
        or wide_view_get(
            cdf, "grant/a_complete", keys=keys, fields=["title", "complete"]
        )
        == True
    )
    assert cdf.to_pandas().shape == shape_before


def test_wide_unflatten_round_trip():
    tall = _sample_frame()[["title", "complete"]]
    wide = wide_flatten_dataframe(tall, columns=["title", "complete"])
    recovered = wide_unflatten_dataframe(
        wide, fields=["title", "complete"]
    )
    # Object dtype / bool may differ slightly; compare values
    assert list(recovered.index) == ["grant/a", "grant/b"]
    assert recovered.at["grant/a", "title"] == "A"
    assert recovered.at["grant/b", "complete"] is False or recovered.at[
        "grant/b", "complete"
    ] == False


def test_wide_unflatten_skips_keys_field():
    wide = wide_flatten_dataframe(_sample_frame(), columns=["title"])
    recovered = wide_unflatten_dataframe(wide, fields=["title"])
    assert list(recovered.columns) == ["title"]
    assert "flattenKeys" not in recovered.columns


def test_wide_view_bad_name_raises():
    with pytest.raises(ValueError, match="Cannot parse"):
        parse_wide_column_name("nope", keys=["grant/a"], fields=["title"])


def test_read_wide_flatten_via_read_data():
    details = {
        "type": "wide_flatten",
        "separator": "_",
        "order": "index_then_field",
        "columns": ["title", "complete"],
        "index": "id",
        "specifications": {
            "type": "local",
            "data": [
                {"id": "grant/a", "title": "A", "complete": True},
                {"id": "grant/b", "title": "B", "complete": False},
            ],
        },
    }

    df, _ = read_data(details)

    assert len(df) == 1
    assert df.iloc[0]["flattenKeys"] == ["grant/a", "grant/b"]
    assert df.iloc[0]["grant/a_title"] == "A"
    assert df.iloc[0]["grant/b_complete"] is False or df.iloc[0]["grant/b_complete"] == False
    # finalize_data must not inject tall ``columns`` names onto the wide row
    assert "title" not in df.columns
    assert "complete" not in df.columns


def test_read_wide_flatten_keys_field_false():
    details = {
        "type": "wide_flatten",
        "keys_field": False,
        "columns": ["title"],
        "index": "id",
        "specifications": {
            "type": "local",
            "data": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B"},
            ],
        },
    }
    df, _ = read_data(details)
    assert "flattenKeys" not in df.columns


def test_read_wide_flatten_nested_compute_then_widen():
    """Nested compute runs on multi-row frame before flatten (thin finalize)."""
    details = {
        "type": "wide_flatten",
        "columns": ["title", "tag"],
        "index": "id",
        "specifications": {
            "type": "local",
            "data": [
                {"id": "a", "title": "Alpha"},
                {"id": "b", "title": "Beta"},
            ],
            "compute": [
                {
                    "field": "tag",
                    "function": "today",
                }
            ],
        },
    }

    df, _ = read_data(details)

    assert len(df) == 1
    assert df.iloc[0]["flattenKeys"] == ["a", "b"]
    assert "a_title" in df.columns and "b_title" in df.columns
    assert "a_tag" in df.columns and "b_tag" in df.columns
    assert isinstance(df.iloc[0]["a_tag"], str)
    assert len(df.iloc[0]["a_tag"]) == 10


def test_read_wide_flatten_missing_specifications():
    with pytest.raises(ValueError, match="specifications"):
        read_data({"type": "wide_flatten"})


def test_read_wide_flatten_wrong_type_helper():
    from lynguine.access.io import read_wide_flatten

    with pytest.raises(ValueError, match="wide_flatten"):
        read_wide_flatten(
            {"type": "series", "specifications": {"type": "local", "data": []}}
        )
