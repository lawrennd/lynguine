"""Regression tests for CustomDataFrame.set_value keeping self._d in sync.

Bug fixed: set_value updated the main pandas DataFrame (via self.at) but not
the sub-DataFrame stored in self._d[typ].  save_flows reads exclusively from
self._d, so after the first save+reload cycle the stale self._d values would
be written rather than the freshly set ones.

The fix adds an explicit ``self._d[typ].at[index, col] = value`` assignment
inside set_value whenever the column belongs to a standard (non-series)
output type.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from lynguine.assess.data import CustomDataFrame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cdf(colspec_type: str = "writedata", data: dict | None = None, index: list | None = None) -> CustomDataFrame:
    """Return a minimal CustomDataFrame with one output column.

    ``colspec_type`` must be a type in ``CustomDataFrame.types["output"]``
    that is *not* a series type (so set_value follows the non-series branch).
    """
    if index is None:
        index = ["alice", "bob"]
    if data is None:
        data = {"Score": [0, 0]}
    df = pd.DataFrame(data, index=index)
    return CustomDataFrame(df, colspecs={colspec_type: list(data.keys())})


# ---------------------------------------------------------------------------
# Tests: set_value updates the main DataFrame (self.at)
# ---------------------------------------------------------------------------


class TestSetValueUpdatesMainDataFrame:
    def test_at_cell_updated(self):
        cdf = _make_cdf()
        cdf.set_index("alice")
        cdf.set_column("Score")
        cdf.set_value(7)
        assert cdf.at["alice", "Score"] == 7

    def test_other_rows_unchanged_in_main(self):
        cdf = _make_cdf()
        cdf.set_index("alice")
        cdf.set_column("Score")
        cdf.set_value(7)
        assert cdf.at["bob", "Score"] == 0


# ---------------------------------------------------------------------------
# Tests: set_value propagates to self._d (the critical regression fix)
# ---------------------------------------------------------------------------


class TestSetValueSyncsInternalD:
    def test_d_updated_after_set_value(self):
        """After set_value the sub-DataFrame in _d must reflect the new value."""
        cdf = _make_cdf()
        cdf.set_index("alice")
        cdf.set_column("Score")
        cdf.set_value(7)

        typ = cdf._col_source("Score")
        assert typ is not None, "Column not found in any _d sub-DataFrame"
        assert cdf._d[typ].at["alice", "Score"] == 7

    def test_d_not_stale_after_second_set_value(self):
        """A second set_value call must also update _d (catches the CoW stale-view bug)."""
        cdf = _make_cdf()
        cdf.set_index("alice")
        cdf.set_column("Score")

        cdf.set_value(3)
        cdf.set_value(9)  # second call — this was the failing case

        typ = cdf._col_source("Score")
        assert cdf._d[typ].at["alice", "Score"] == 9

    def test_d_updated_across_multiple_sequential_calls(self):
        """Each successive set_value must leave _d in a consistent state."""
        cdf = _make_cdf()
        cdf.set_index("alice")
        cdf.set_column("Score")

        for val in [1, 5, 10, 3]:
            cdf.set_value(val)
            typ = cdf._col_source("Score")
            assert cdf._d[typ].at["alice", "Score"] == val, (
                f"_d stale after setting Score={val}"
            )

    def test_d_updated_for_each_row_independently(self):
        """Updating alice then bob updates the correct row in _d for each."""
        cdf = _make_cdf()
        cdf.set_column("Score")

        cdf.set_index("alice")
        cdf.set_value(4)

        cdf.set_index("bob")
        cdf.set_value(8)

        typ = cdf._col_source("Score")
        assert cdf._d[typ].at["alice", "Score"] == 4
        assert cdf._d[typ].at["bob", "Score"] == 8

    def test_d_updated_for_second_row_does_not_corrupt_first(self):
        """Writing to bob must not overwrite alice's value in _d."""
        cdf = _make_cdf()
        cdf.set_column("Score")

        cdf.set_index("alice")
        cdf.set_value(42)

        cdf.set_index("bob")
        cdf.set_value(0)

        typ = cdf._col_source("Score")
        assert cdf._d[typ].at["alice", "Score"] == 42


# ---------------------------------------------------------------------------
# Tests: save_flows writes the updated value (not the stale original)
# ---------------------------------------------------------------------------


class TestSaveFlowsWritesUpdatedValue:
    def test_save_writes_value_set_via_set_value(self, monkeypatch):
        """save_flows must pass the new value to write_data, not the stale one."""
        import lynguine.access.io as io

        captured: list[pd.DataFrame] = []

        def fake_write_data(df: pd.DataFrame, details) -> None:
            captured.append(df.copy())

        monkeypatch.setattr(io, "write_data", fake_write_data)

        colspec_type = "writedata"
        cdf = _make_cdf(colspec_type=colspec_type)
        cdf.interface = {colspec_type: {"something": "irrelevant"}}

        cdf.set_index("alice")
        cdf.set_column("Score")
        cdf.set_value(42)
        cdf.save_flows()

        assert captured, "write_data was never called"
        written = captured[0]
        assert "Score" in written.columns
        assert written.loc["alice", "Score"] == 42

    def test_second_save_writes_second_updated_value(self, monkeypatch):
        """A second set_value followed by save_flows must write the second value.

        This is the core regression: before the fix the second save would write
        the original (stale) value from _d rather than the value set in the
        second set_value call.
        """
        import lynguine.access.io as io

        captured: list[pd.DataFrame] = []

        def fake_write_data(df: pd.DataFrame, details) -> None:
            captured.append(df.copy())

        monkeypatch.setattr(io, "write_data", fake_write_data)

        colspec_type = "writedata"
        cdf = _make_cdf(colspec_type=colspec_type)
        cdf.interface = {colspec_type: {"something": "irrelevant"}}

        cdf.set_index("alice")
        cdf.set_column("Score")

        # First save
        cdf.set_value(3)
        cdf.save_flows()

        # Second save — must write the new value, not revert to 3
        cdf.set_value(12)
        cdf.save_flows()

        assert len(captured) == 2
        first_saved = captured[0].loc["alice", "Score"]
        second_saved = captured[1].loc["alice", "Score"]
        assert first_saved == 3, f"First save wrote {first_saved!r}, expected 3"
        assert second_saved == 12, f"Second save wrote {second_saved!r}, expected 12 (regression)"
