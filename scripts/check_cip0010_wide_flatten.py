#!/usr/bin/env python3
"""Manual acceptance check for CIP-0010 (wide flatten / store views).

Run from the repository root after installing lynguine in the active env:

    python scripts/check_cip0010_wide_flatten.py

Or in Jupyter from the repo root:

    %run scripts/check_cip0010_wide_flatten.py

Exits 0 and prints OK lines if Pattern A (virtual view) and Pattern B
(materialized flatten + unflatten) behave as CIP-0010 requires.
"""

from __future__ import annotations

import sys

import pandas as pd

from lynguine.access.io import (
    read_data,
    wide_flatten_dataframe,
    wide_unflatten_dataframe,
    wide_view_get,
    wide_view_set,
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def check_pattern_a_virtual_view() -> None:
    """Tall store + wide names; shape unchanged; Save would see tall columns."""
    df = pd.DataFrame(
        {"title": ["A", "B"], "complete": [False, False]},
        index=["grant/a", "grant/b"],
    )
    keys = list(df.index)
    fields = ["title", "complete"]
    before = df.shape

    wide_view_set(df, "grant/a_complete", True, keys=keys, fields=fields)
    got = wide_view_get(df, "grant/a_complete", keys=keys, fields=fields)

    if df.shape != before:
        _fail(f"Pattern A changed shape {before} -> {df.shape}")
    if got != True:  # noqa: E712 — may be numpy.bool_
        _fail(f"Pattern A get expected True, got {got!r}")
    if df.at["grant/a", "complete"] != True:  # noqa: E712
        _fail("Pattern A set did not update tall cell")
    if list(df.columns) != ["title", "complete"]:
        _fail(f"Pattern A columns changed: {list(df.columns)}")

    print("OK  Pattern A: wide_view_get/set on tall store (shape unchanged)")


def check_pattern_b_materialized() -> None:
    """type: wide_flatten snapshot + flattenKeys + unflatten round-trip."""
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
    wide, _ = read_data(details)

    if len(wide) != 1:
        _fail(f"Pattern B expected 1 wide row, got {len(wide)}")
    keys = wide.iloc[0]["flattenKeys"]
    if list(keys) != ["grant/a", "grant/b"]:
        _fail(f"Pattern B flattenKeys mismatch: {keys!r}")
    if wide.iloc[0]["grant/a_title"] != "A":
        _fail("Pattern B missing grant/a_title")

    tall = wide_unflatten_dataframe(wide, fields=["title", "complete"])
    if list(tall.index) != ["grant/a", "grant/b"]:
        _fail(f"unflatten index mismatch: {list(tall.index)}")
    if tall.at["grant/b", "title"] != "B":
        _fail("unflatten value mismatch")

    # Helper path without read_data
    src = pd.DataFrame(
        {"title": ["A", "B"], "complete": [True, False]},
        index=["grant/a", "grant/b"],
    )
    wide2 = wide_flatten_dataframe(src, columns=["title", "complete"])
    back = wide_unflatten_dataframe(wide2, fields=["title", "complete"])
    if back.at["grant/a", "title"] != "A":
        _fail("helper round-trip failed")

    print("OK  Pattern B: wide_flatten + flattenKeys + wide_unflatten")


def main() -> None:
    print("CIP-0010 acceptance check (run from repo root)\n")
    check_pattern_a_virtual_view()
    check_pattern_b_materialized()
    print("\nAll checks passed. Safe to accept/close CIP-0010 if this matches intent.")


if __name__ == "__main__":
    main()
