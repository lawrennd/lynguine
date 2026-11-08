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
