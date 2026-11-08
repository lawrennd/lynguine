"""CIP-0014 explode on read after input load."""

from __future__ import annotations

from pathlib import Path

import yaml

from lynguine.assess.data import CustomDataFrame
from lynguine.config.interface import Interface


def test_input_explode_on_read(tmp_path: Path):
    (tmp_path / "messages.yml").write_text(
        yaml.safe_dump(
            [
                {
                    "mail_key": "phd::1",
                    "message_id": "<a@b>",
                    "subject": "PhD",
                    "candidate": True,
                    "unit_paragraphs": [
                        {
                            "unit_id": "<a@b>::0",
                            "unit_index": 0,
                            "text": "First paragraph.",
                            "extract_text": "First paragraph.",
                        },
                        {
                            "unit_id": "<a@b>::1",
                            "unit_index": 1,
                            "text": "Second paragraph long enough here.",
                            "extract_text": "Second paragraph long enough here.",
                        },
                    ],
                }
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    iface = Interface(
        {
            "input": {
                "type": "yaml",
                "directory": ".",
                "filename": "messages.yml",
                "index": "mail_key",
                "explode": {
                    "field": "unit_paragraphs",
                    "inherit": ["message_id", "mail_key", "subject"],
                    "index": "unit_id",
                },
            }
        },
        directory=str(tmp_path),
        user_file="flow.yml",
    )
    cdf = CustomDataFrame.from_flow(iface)
    assert len(cdf) == 2
    assert list(cdf.index) == ["<a@b>::0", "<a@b>::1"]
    assert "text" in cdf.columns
    assert "subject" in cdf.columns


def test_input_compute_then_explode_keeps_singleton_list(tmp_path: Path):
    """Regression: .loc assign must not unwrap a one-item unit list to a dict."""
    (tmp_path / "messages.yml").write_text(
        yaml.safe_dump(
            [
                {
                    "mail_key": "phd::1",
                    "message_id": "<a@b>",
                    "subject": "PhD",
                    "from": "Dept <dept@example.ac.uk>",
                    "date": "2026-01-01",
                    "candidate": True,
                    "body": (
                        "We invite applications for a fully funded PhD "
                        "studentship in causal machine learning."
                    ),
                },
                {
                    "mail_key": "noise::2",
                    "message_id": "<c@d>",
                    "subject": "Hello",
                    "from": "x@y.com",
                    "date": "2026-01-02",
                    "candidate": False,
                    "body": "Not a candidate message body that is long enough.",
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    iface = Interface(
        {
            "input": {
                "type": "yaml",
                "directory": ".",
                "filename": "messages.yml",
                "index": "mail_key",
                "compute": [
                    {
                        "field": "unit_paragraphs",
                        "function": "split_paragraph_units",
                        "args": {
                            "min_chars": 40,
                            "max_units": 12,
                            "only_candidates": True,
                        },
                        "row_args": {
                            "text": "body",
                            "message_id": "message_id",
                            "mail_key": "mail_key",
                            "candidate": "candidate",
                            "subject": "subject",
                            "sender": "from",
                            "date": "date",
                        },
                    }
                ],
                "explode": {
                    "field": "unit_paragraphs",
                    "inherit": ["message_id", "mail_key", "subject", "from", "date"],
                    "index": "unit_id",
                },
            }
        },
        directory=str(tmp_path),
        user_file="flow.yml",
    )
    cdf = CustomDataFrame.from_flow(iface)
    assert len(cdf) == 1
    # unit_id prefers mail_key when present (see split_paragraph_units).
    assert list(cdf.index) == ["phd::1::0"]
    assert "extract_text" in cdf.columns
    assert cdf.loc["phd::1::0", "subject"] == "PhD"
