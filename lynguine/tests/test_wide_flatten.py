"""Tests for CIP-0010 wide_flatten reshape."""

from __future__ import annotations

import pandas as pd
import pytest

from lynguine.access.io import read_data, wide_flatten_dataframe


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
    assert list(wide.columns) == [
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

    assert list(wide.columns) == [
        "title_grant/a",
        "title_grant/b",
        "complete_grant/a",
        "complete_grant/b",
    ]
    assert wide.iloc[0]["title_grant/b"] == "B"


def test_wide_flatten_columns_subset_drops_others():
    wide = wide_flatten_dataframe(_sample_frame(), columns=["title"])

    assert list(wide.columns) == ["grant/a_title", "grant/b_title"]
    assert "extra" not in "".join(wide.columns)


def test_wide_flatten_duplicate_index_raises():
    df = pd.DataFrame({"title": ["A", "B"]}, index=["same", "same"])

    with pytest.raises(ValueError, match="unique index"):
        wide_flatten_dataframe(df)


def test_wide_flatten_empty_frame_one_empty_row():
    df = pd.DataFrame(columns=["title", "complete"])
    wide = wide_flatten_dataframe(df)

    assert len(wide) == 1
    assert list(wide.columns) == []


def test_wide_flatten_str_coercion_of_names():
    df = pd.DataFrame({"count": [1, 2]}, index=[10, 20])
    wide = wide_flatten_dataframe(df, separator="-")

    assert list(wide.columns) == ["10-count", "20-count"]
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
    assert df.iloc[0]["grant/a_title"] == "A"
    assert df.iloc[0]["grant/b_complete"] is False or df.iloc[0]["grant/b_complete"] == False


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
    assert "a_title" in df.columns and "b_title" in df.columns
    assert "a_tag" in df.columns and "b_tag" in df.columns
    # today() default format is YYYY-MM-DD
    assert isinstance(df.iloc[0]["a_tag"], str)
    assert len(df.iloc[0]["a_tag"]) == 10


def test_read_wide_flatten_missing_specifications():
    with pytest.raises(ValueError, match="specifications"):
        read_data({"type": "wide_flatten"})


def test_read_wide_flatten_wrong_type_helper():
    from lynguine.access.io import read_wide_flatten

    with pytest.raises(ValueError, match="wide_flatten"):
        read_wide_flatten({"type": "series", "specifications": {"type": "local", "data": []}})
