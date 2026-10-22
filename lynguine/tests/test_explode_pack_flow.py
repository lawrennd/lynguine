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


def test_write_pack_store_skips_when_pack_absent_or_non_mapping_interface():
    cdf = CustomDataFrame(
        pd.DataFrame({"phrase": ["one"]}),
        colspecs={"input": ["phrase"]},
    )
    cdf.interface = {"input": {"type": "yaml"}}
    assert cdf._write_pack_store() is False
    cdf._interface = object()
    assert cdf._write_pack_store() is False


def test_pack_source_partition_and_error_paths(tmp_path):
    phrases = pd.DataFrame(
        {
            "phrase": ["one", "two"],
            "embedding": [[0.1], [0.2]],
        },
        index=pd.Index(["p0", "p1"], name="phrase_id"),
    )
    cdf = CustomDataFrame(phrases, colspecs={"input": ["phrase", "embedding"]})
    cdf.interface = {
        "base_directory": str(tmp_path),
        "pack": {
            "type": "yaml",
            "filename": "from_input.yml",
            "directory": str(tmp_path),
            "index": "Name",
            "source": "input",
            "pack": {
                "columns": {"phrases": "phrase", "embeddings": "embedding"},
                "index_value": "corpus",
            },
        },
    }
    assert cdf._write_pack_store() is True
    written = yaml.safe_load((tmp_path / "from_input.yml").read_text(encoding="utf-8"))
    assert written[0]["phrases"] == ["one", "two"]

    cdf.interface["pack"]["source"] = "output"
    with pytest.raises(ValueError, match="is not loaded"):
        cdf._write_pack_store()

    cdf.interface["pack"] = "not-a-mapping"
    with pytest.raises(ValueError, match="must be a mapping"):
        cdf._write_pack_store()

    cdf.interface["pack"] = {
        "type": "yaml",
        "filename": "bad.yml",
        "directory": str(tmp_path),
    }
    with pytest.raises(ValueError, match="nested pack"):
        cdf._write_pack_store()

    empty = CustomDataFrame(pd.DataFrame({"x": []}), colspecs={"input": ["x"]})
    empty.interface = {
        "base_directory": str(tmp_path),
        "pack": {
            "type": "yaml",
            "filename": "empty.yml",
            "directory": str(tmp_path),
            "pack": {"columns": {"xs": "x"}},
        },
    }
    assert empty._write_pack_store() is True
    written = yaml.safe_load((tmp_path / "empty.yml").read_text(encoding="utf-8"))
    assert written[0]["xs"] == []


def test_write_pack_store_explodes_output_then_packs(tmp_path):
    chunks = pd.DataFrame(
        {
            "filename": ["a.pdf"],
            "extraction_phrases": [[
                {
                    "phrase_id": "p0",
                    "phrase": "one",
                    "embedding": [0.1],
                    "doc_id": "a.pdf",
                },
                {
                    "phrase_id": "p1",
                    "phrase": "two",
                    "embedding": [0.2],
                    "doc_id": "a.pdf",
                },
            ]],
        },
        index=pd.Index(["c0"], name="unit_id"),
    )
    cdf = CustomDataFrame(
        chunks, colspecs={"input": ["filename", "extraction_phrases"]}
    )
    cdf.interface = {
        "base_directory": str(tmp_path),
        "output": {
            "type": "yaml",
            "filename": "phrases.yml",
            "directory": str(tmp_path),
            "index": "phrase_id",
            "explode": {"field": "extraction_phrases", "inherit": ["filename"]},
        },
        "pack": {
            "type": "yaml",
            "filename": "records.yml",
            "directory": str(tmp_path),
            "index": "Name",
            "pack": {
                "columns": {
                    "phrases": "phrase",
                    "embeddings": "embedding",
                    "doc_ids": "doc_id",
                },
                "index_value": "corpus",
            },
        },
    }
    assert cdf._write_pack_store() is True
    written = yaml.safe_load((tmp_path / "records.yml").read_text(encoding="utf-8"))
    assert written[0]["phrases"] == ["one", "two"]
    assert written[0]["doc_ids"] == ["a.pdf", "a.pdf"]


def test_save_flows_writes_cache_parameters_and_empty_pack(tmp_path):
    chunks = pd.DataFrame(
        {
            "filename": ["a.pdf"],
            "extraction_phrases": [[]],
            "phrase_kinds": ["benefit"],
        },
        index=pd.Index(["c0"], name="unit_id"),
    )
    cdf = CustomDataFrame(
        chunks,
        colspecs={
            "input": ["filename"],
            "cache": ["extraction_phrases"],
            "parameters": ["phrase_kinds"],
        },
    )
    cdf._d["parameters"] = pd.Series(
        {"phrase_kinds": "concern, benefit", "embed_pca_dim": None}
    )
    cdf._d["output"] = pd.DataFrame(index=pd.Index(["c0"], name="unit_id"))
    cdf._colspecs["output"] = []
    cdf.interface = {
        "base_directory": str(tmp_path),
        "parameters": {
            "type": "yaml",
            "filename": "parameters.yml",
            "directory": str(tmp_path),
            "index": "index",
            "select": "dialogue-v1",
        },
        "cache": {
            "type": "yaml",
            "filename": "_extract_cache.yml.gz",
            "directory": str(tmp_path),
            "index": "unit_id",
            "compress": "gzip",
        },
        "output": {
            "type": "yaml",
            "filename": "phrases.yml",
            "directory": str(tmp_path),
            "index": "phrase_id",
            "explode": {
                "field": "extraction_phrases",
                "inherit": ["filename"],
            },
        },
        "pack": {
            "type": "yaml",
            "filename": "records.yml",
            "directory": str(tmp_path),
            "index": "Name",
            "pack": {
                "columns": {
                    "phrases": "phrase",
                    "embeddings": "embedding",
                    "doc_ids": "doc_id",
                },
                "index_value": "corpus",
            },
        },
    }
    cdf.save_flows()
    assert not (tmp_path / "constants.yml").exists()
    parameters = yaml.safe_load((tmp_path / "parameters.yml").read_text(encoding="utf-8"))
    assert parameters[0]["phrase_kinds"] == "concern, benefit"
    assert parameters[0]["index"] == "dialogue-v1"
    assert parameters[0]["embed_pca_dim"] is None
    records = yaml.safe_load((tmp_path / "records.yml").read_text(encoding="utf-8"))
    assert records[0]["phrases"] == []
    assert (tmp_path / "_extract_cache.yml.gz").exists()


def test_parent_grain_skips_duplicate_columns_and_empty_partitions():
    cdf = CustomDataFrame(
        pd.DataFrame({"phrase": ["one"], "shared": [1]}, index=["p0"]),
        colspecs={"input": ["phrase", "shared"]},
    )
    cdf._d["cache"] = pd.DataFrame(
        {"shared": [9], "extra": ["keep"]}, index=["p0"]
    )
    cdf._colspecs["cache"] = ["shared", "extra"]
    cdf._d["output"] = pd.DataFrame(index=["p0"])
    combined = cdf._parent_grain_frame()
    assert list(combined.columns) == ["phrase", "shared", "extra"]
    assert combined.loc["p0", "shared"] == 1
    assert combined.loc["p0", "extra"] == "keep"

    vacant = CustomDataFrame(pd.DataFrame(), colspecs={"input": []})
    assert vacant._parent_grain_frame().empty


def test_to_flow_explodes_parent_grain(tmp_path):
    docs = pd.DataFrame(
        {
            "filename": ["a.pdf"],
            "units": [[{"unit_id": "a-0", "text": "hello"}]],
        },
        index=pd.Index(["doc-a"], name="Name"),
    )
    cdf = CustomDataFrame(docs, colspecs={"input": ["filename", "units"]})
    cdf._d["output"] = pd.DataFrame(index=docs.index)
    cdf._colspecs["output"] = []
    interface = {
        "output": {
            "type": "yaml",
            "filename": "chunks.yml",
            "directory": str(tmp_path),
            "index": "unit_id",
            "explode": {"field": "units", "inherit": ["Name", "filename"]},
        }
    }
    cdf.interface = interface
    cdf.to_flow(interface)
    written = yaml.safe_load((tmp_path / "chunks.yml").read_text(encoding="utf-8"))
    assert written[0]["unit_id"] == "a-0"
    assert written[0]["filename"] == "a.pdf"


def test_explode_ignores_tall_output_partition(tmp_path):
    """Previous phrases.yml must not join onto chunks before explode."""
    chunks = pd.DataFrame(
        {
            "filename": ["a.pdf"],
            "extraction_phrases": [
                [{"phrase_id": "p-new", "phrase": "fresh", "kind": "benefit"}]
            ],
        },
        index=pd.Index(["c0"], name="unit_id"),
    )
    cdf = CustomDataFrame(
        chunks[["filename"]],
        colspecs={"input": ["filename"]},
    )
    cdf._d["cache"] = chunks[["extraction_phrases"]]
    cdf._colspecs["cache"] = ["extraction_phrases"]
    cdf._d["output"] = pd.DataFrame(
        {
            "phrase": ["stale"],
            "embedding": [[0.1]],
            "doc_id": ["old.pdf"],
        },
        index=pd.Index(["old-p0"], name="phrase_id"),
    )
    cdf._colspecs["output"] = ["phrase", "embedding", "doc_id"]
    cdf.interface = {
        "output": {
            "type": "yaml",
            "filename": "phrases.yml",
            "directory": str(tmp_path),
            "index": "phrase_id",
            "explode": {
                "field": "extraction_phrases",
                "inherit": ["unit_id", "filename"],
            },
        }
    }
    cdf.to_flow(cdf.interface)
    written = yaml.safe_load((tmp_path / "phrases.yml").read_text(encoding="utf-8"))
    assert len(written) == 1
    assert written[0]["phrase"] == "fresh"
    assert written[0]["filename"] == "a.pdf"
    assert written[0]["unit_id"] == "c0"


def test_write_frame_for_store_keeps_output_when_parent_grain_empty():
    cdf = CustomDataFrame(
        pd.DataFrame({"score": [1]}, index=["a"]),
        colspecs={"output": ["score"]},
    )
    cdf._d["input"] = pd.DataFrame()
    details = {"type": "yaml", "index": "Name", "explode": {"field": "units"}}
    frame = cdf._write_frame_for_store("output", cdf._d["output"], details)
    assert "score" in frame.columns
