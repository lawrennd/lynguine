"""Flow-level CIP-0014/0015 checks: from_flow write, next config load."""

from __future__ import annotations

import gzip

import pandas as pd
import pytest
import yaml

from lynguine.assess.data import CustomDataFrame
from lynguine.config.interface import Interface


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _interface(directory, user_file, data):
    path = directory / user_file
    _write_yaml(path, data)
    return Interface.from_file(
        user_file=user_file,
        directory=str(directory),
        allowed_roots=[str(directory)],
    )


def _documents():
    return [
        {
            "Name": "doc-a",
            "filename": "a.pdf",
            "year": 2024,
            "units": [
                {"unit_id": "a-0", "text": "hello", "chunk_index": 0},
                {"unit_id": "a-1", "text": "world", "chunk_index": 1},
            ],
        },
        {
            "Name": "doc-b",
            "filename": "b.pdf",
            "year": 2025,
            "units": [
                {"unit_id": "b-0", "text": "later", "chunk_index": 0},
            ],
        },
    ]


def _phrases(include_missing=False):
    rows = [
        {
            "phrase_id": "p0",
            "phrase": "one",
            "embedding": [0.1, 0.2],
            "doc_id": "a",
        },
        {
            "phrase_id": "p1",
            "phrase": "two",
            "embedding": None if include_missing else [0.3, 0.4],
            "doc_id": "a",
        },
        {
            "phrase_id": "p2",
            "phrase": "three",
            "embedding": [0.5, 0.6],
            "doc_id": "b",
        },
    ]
    return rows


def test_explode_flow_writes_tall_table_next_config_loads(tmp_path):
    info = tmp_path / "info"
    info.mkdir()
    _write_yaml(info / "documents.yml", _documents())

    chunk_iface = _interface(
        tmp_path,
        "_chunk.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "documents.yml",
                "directory": "info",
                "index": "Name",
            },
            "output": {
                "type": "yaml",
                "filename": "chunks.yml",
                "directory": "info",
                "index": "unit_id",
                "explode": {
                    "field": "units",
                    "inherit": ["Name", "filename", "year"],
                },
            },
        },
    )
    chunk = CustomDataFrame.from_flow(chunk_iface)
    chunk.save_flows()

    chunks_path = info / "chunks.yml"
    assert chunks_path.exists()
    written = yaml.safe_load(chunks_path.read_text(encoding="utf-8"))
    assert len(written) == 3
    assert {row["unit_id"] for row in written} == {"a-0", "a-1", "b-0"}
    world = next(row for row in written if row["unit_id"] == "a-1")
    assert world["Name"] == "doc-a"
    assert world["filename"] == "a.pdf"
    assert world["text"] == "world"
    assert "units" not in world

    next_iface = _interface(
        tmp_path,
        "_phrases.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "chunks.yml",
                "directory": "info",
                "index": "unit_id",
            },
        },
    )
    loaded = CustomDataFrame.from_flow(next_iface)
    assert list(loaded.index) == ["a-0", "a-1", "b-0"]
    assert loaded.index.name == "unit_id"
    assert loaded.at["a-1", "Name"] == "doc-a"
    assert loaded.at["a-1", "text"] == "world"


def test_top_level_pack_one_corpus_row_and_missing_embeddings(tmp_path):
    info = tmp_path / "info"
    info.mkdir()
    _write_yaml(info / "phrases.yml", _phrases())

    pack_spec = {
        "type": "yaml",
        "filename": "records.yml",
        "directory": "info",
        "index": "Name",
        "pack": {
            "columns": {
                "phrases": "phrase",
                "embeddings": "embedding",
                "doc_ids": "doc_id",
            },
            "index_value": "corpus",
        },
    }
    packed_iface = _interface(
        tmp_path,
        "_pack.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "phrases.yml",
                "directory": "info",
                "index": "phrase_id",
            },
            "pack": pack_spec,
        },
    )
    CustomDataFrame.from_flow(packed_iface).save_flows()

    records_path = info / "records.yml"
    written = yaml.safe_load(records_path.read_text(encoding="utf-8"))
    assert len(written) == 1
    row = written[0]
    assert row["Name"] == "corpus"
    assert row["phrases"] == ["one", "two", "three"]
    assert row["embeddings"][1] == [0.3, 0.4]
    assert len(row["phrases"]) == len(row["embeddings"]) == len(row["doc_ids"])

    next_iface = _interface(
        tmp_path,
        "_grain.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "records.yml",
                "directory": "info",
                "index": "Name",
            },
        },
    )
    grain = CustomDataFrame.from_flow(next_iface)
    assert list(grain.index) == ["corpus"]
    assert list(grain.at["corpus", "phrases"]) == ["one", "two", "three"]

    missing_dir = tmp_path / "missing"
    missing_info = missing_dir / "info"
    missing_info.mkdir(parents=True)
    _write_yaml(missing_info / "phrases.yml", _phrases(include_missing=True))

    abort_iface = _interface(
        missing_dir,
        "_pack.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "phrases.yml",
                "directory": "info",
                "index": "phrase_id",
            },
            "pack": dict(pack_spec),
        },
    )
    with pytest.raises(ValueError, match="missing embedding"):
        CustomDataFrame.from_flow(abort_iface).save_flows()
    assert not (missing_info / "records.yml").exists()

    drop_spec = dict(pack_spec)
    drop_spec["pack"] = dict(pack_spec["pack"], drop_incomplete=True)
    drop_iface = _interface(
        missing_dir,
        "_pack_drop.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "phrases.yml",
                "directory": "info",
                "index": "phrase_id",
            },
            "pack": drop_spec,
        },
    )
    CustomDataFrame.from_flow(drop_iface).save_flows()
    dropped = yaml.safe_load((missing_info / "records.yml").read_text(encoding="utf-8"))
    assert dropped[0]["phrases"] == ["one", "three"]
    assert len(dropped[0]["embeddings"]) == 2


def test_yml_gz_round_trip_and_gzip_yml_fails(tmp_path):
    info = tmp_path / "info"
    info.mkdir()
    _write_yaml(info / "phrases.yml", _phrases())

    gz_iface = _interface(
        tmp_path,
        "_gz.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "phrases.yml",
                "directory": "info",
                "index": "phrase_id",
            },
            "output": {
                "type": "yaml",
                "filename": "phrases.yml.gz",
                "directory": "info",
                "index": "phrase_id",
                "columns": ["phrase", "embedding", "doc_id"],
            },
        },
    )
    cdf = CustomDataFrame.from_flow(gz_iface)
    # Copy tall columns onto output so gzip write is the phrase table.
    for col in ["phrase", "embedding", "doc_id"]:
        cdf._d["output"][col] = cdf._d["input"][col]
    cdf.save_flows()

    gz_path = info / "phrases.yml.gz"
    assert gz_path.exists()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    assert len(raw) == 3

    load_gz = _interface(
        tmp_path,
        "_load_gz.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "phrases.yml.gz",
                "directory": "info",
                "index": "phrase_id",
            },
        },
    )
    loaded = CustomDataFrame.from_flow(load_gz)
    assert list(loaded["phrase"]) == ["one", "two", "three"]

    fake_yml = info / "compressed.yml"
    with gzip.open(fake_yml, "wt", encoding="utf-8") as fh:
        yaml.safe_dump(_phrases(), fh)
    bad_iface = _interface(
        tmp_path,
        "_bad_gz.yml",
        {
            "input": {
                "type": "yaml",
                "filename": "compressed.yml",
                "directory": "info",
                "index": "phrase_id",
            },
        },
    )
    with pytest.raises(ValueError, match="does not end in .gz"):
        CustomDataFrame.from_flow(bad_iface)
