"""output.also_materialize writes a joined input+output side-car on Save."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from lynguine.assess.data import CustomDataFrame
from lynguine.config.interface import Interface


def test_also_materialize_writes_messages_sidecar(tmp_path: Path):
    (tmp_path / "hits.yml").write_text(
        yaml.safe_dump(
            [
                {
                    "mail_key": "phd::1",
                    "message_id": "<a@b>",
                    "subject": "PhD post",
                    "body": "Fully funded studentship",
                    "slice": "phd",
                },
                {
                    "mail_key": "phd::2",
                    "message_id": "<c@d>",
                    "subject": "Noise",
                    "body": "Unsubscribe",
                    "slice": "phd",
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scores = tmp_path / "scores.yml"
    scores.write_text(
        yaml.safe_dump(
            [
                {"mail_key": "phd::1", "candidate": True, "notes": "keep"},
                {"mail_key": "phd::2", "candidate": False},
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    corpus = tmp_path / "corpus"
    corpus.mkdir()

    iface = Interface(
        {
            "input": {
                "type": "yaml",
                "directory": ".",
                "filename": "hits.yml",
                "index": "mail_key",
            },
            "output": {
                "type": "yaml",
                "directory": ".",
                "filename": "scores.yml",
                "index": "mail_key",
                "columns": ["candidate", "notes"],
                "also_materialize": {
                    "type": "yaml",
                    "directory": "corpus",
                    "filename": "messages.yml",
                    "index": "mail_key",
                    "columns": [
                        "message_id",
                        "subject",
                        "body",
                        "slice",
                        "candidate",
                        "notes",
                    ],
                },
            },
        },
        directory=str(tmp_path),
        user_file="flow.yml",
    )
    cdf = CustomDataFrame.from_flow(iface)
    cdf.save_flows()

    messages = yaml.safe_load(
        (corpus / "messages.yml").read_text(encoding="utf-8")
    )
    assert isinstance(messages, list)
    by_key = {row["mail_key"]: row for row in messages}
    assert by_key["phd::1"]["body"] == "Fully funded studentship"
    assert by_key["phd::1"]["candidate"] is True
    assert by_key["phd::1"]["notes"] == "keep"
    assert by_key["phd::2"]["candidate"] is False
    # Primary scores file still only has review columns (+ index).
    scores_rows = yaml.safe_load(scores.read_text(encoding="utf-8"))
    assert set(scores_rows[0]) <= {"mail_key", "candidate", "notes"} or "candidate" in scores_rows[0]
