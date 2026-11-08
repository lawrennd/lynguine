"""Access specs may Liquid-template against parameters (query/filename/limit)."""

from __future__ import annotations

from pathlib import Path

import yaml

from lynguine.assess.data import (
    CustomDataFrame,
    _liquid_expand_structure,
    _parameter_liquid_context,
)
from lynguine.config.interface import Interface


def test_liquid_expand_coerces_limit_to_int():
    out = _liquid_expand_structure(
        {"query": "({{ q }}) AND {{ window }}", "limit": "{{ n }}"},
        {"q": "subject:PhD", "window": "date:2y", "n": 40},
    )
    assert out["query"] == "(subject:PhD) AND date:2y"
    assert out["limit"] == 40
    assert isinstance(out["limit"], int)


def test_parameter_liquid_context_and_from_flow_filename(tmp_path: Path):
    base = tmp_path
    (base / "hello.csv").write_text("id,val\na,1\nb,2\n", encoding="utf-8")
    params = base / "parameters.yml"
    params.write_text(
        yaml.safe_dump(
            [{"index": "t1", "stem": "hello", "n": 40}],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    iface = Interface(
        {
            "parameters": {
                "type": "yaml",
                "directory": ".",
                "filename": "parameters.yml",
                "index": "index",
                "select": "t1",
            },
            "input": {
                "type": "csv",
                "directory": ".",
                "filename": "{{ stem }}.csv",
                "index": "id",
            },
        },
        directory=str(base),
        user_file="flow.yml",
    )
    ctx = _parameter_liquid_context(iface)
    assert ctx["stem"] == "hello"
    assert ctx["n"] == 40

    cdf = CustomDataFrame.from_flow(iface)
    assert list(cdf.index) == ["a", "b"]
    assert "val" in cdf.columns
    assert list(cdf["val"]) == [1, 2]


def test_liquid_expand_vstack_mu_query():
    """Stacked mu slices (referia-mail / dods-research-mail pattern)."""
    out = _liquid_expand_structure(
        {
            "type": "vstack",
            "index": "mail_key",
            "specifications": [
                {
                    "type": "mu",
                    "query": "({{ query_phd }}) AND {{ date_window }}",
                    "limit": "{{ limit_per_slice }}",
                    "compute": [
                        {
                            "field": "mail_key",
                            "function": "render_liquid",
                            "args": {"template": "{{ slice }}::{{ uid }}"},
                            "row_args": {"slice": "slice", "uid": "uid"},
                        },
                    ],
                },
                {
                    "type": "mu",
                    "query": "({{ query_boards }}) AND {{ date_window }}",
                    "limit": "{{ limit_per_slice }}",
                },
            ],
        },
        {
            "query_phd": "subject:PhD OR subject:studentship",
            "query_boards": "from:jobs.ac.uk",
            "date_window": "date:2y",
            "limit_per_slice": 25,
        },
    )
    assert out["specifications"][0]["query"] == (
        "(subject:PhD OR subject:studentship) AND date:2y"
    )
    assert out["specifications"][1]["query"] == "(from:jobs.ac.uk) AND date:2y"
    assert out["specifications"][0]["limit"] == 25
    assert isinstance(out["specifications"][0]["limit"], int)
    # Row-time template: keys must not be emptied against the parameters ctx.
    assert out["specifications"][0]["compute"][0]["args"]["template"] == (
        "{{ slice }}::{{ uid }}"
    )


def test_liquid_expand_compute_args_but_not_template():
    out = _liquid_expand_structure(
        {
            "compute": [
                {
                    "field": "unit_paragraphs",
                    "function": "split_paragraph_units",
                    "args": {
                        "min_chars": "{{ min_unit_chars }}",
                        "template": "{{ body }}",
                    },
                }
            ]
        },
        {"min_unit_chars": 40},
    )
    assert out["compute"][0]["args"]["min_chars"] == 40
    assert out["compute"][0]["args"]["template"] == "{{ body }}"
