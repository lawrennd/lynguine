"""CIP-0016: demand-driven Liquid mapping."""

import logging

import pandas as pd
import pytest

import lynguine.assess.data
from lynguine.util.liquid import liquid_root_identifiers


class Boom:
    """Cell whose repr/str must not run during mapping logs."""

    def __repr__(self):
        raise RuntimeError("repr should not be called")

    def __str__(self):
        raise RuntimeError("str should not be called")


def _packed_like_frame():
    cdf = lynguine.assess.data.CustomDataFrame(
        [
            {
                "title": "hello",
                "store_status": {"output": {"path": "/tmp/out"}},
                "selected_doc": "doc1",
                "embeddings": list(range(50)),
            }
        ]
    )
    cdf._augment_column_names(cdf)
    return cdf


def _count_get_value(cdf):
    columns = []
    orig = cdf.get_value

    def wrapped():
        columns.append(cdf.get_column())
        return orig()

    cdf.get_value = wrapped
    return columns


def test_liquid_root_identifiers_nested_path():
    assert liquid_root_identifiers("{{ store_status.output.path }}") == {"store_status"}


def test_liquid_root_identifiers_if_tag():
    assert liquid_root_identifiers("{% if selected_doc %}yes{% endif %}") == {"selected_doc"}


def test_liquid_root_identifiers_named_array():
    assert liquid_root_identifiers("{{ embeddings[0] }}") == {"embeddings"}


def test_liquid_root_identifiers_static_html():
    assert liquid_root_identifiers("<p>static html</p>") == set()


def test_liquid_root_identifiers_syntax_error():
    with pytest.raises(Exception):
        liquid_root_identifiers("{% for k, v in vars %}{{ k }}{% endfor %}")


def test_mapping_names_subset_skips_unmentioned():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    result = cdf.mapping(names=["store_status", "selected_doc"])
    assert set(result) == {"store_status", "selected_doc"}
    assert "embeddings" not in result
    assert set(columns) == {"store_status", "selected_doc"}


def test_mapping_full_still_includes_embeddings():
    cdf = _packed_like_frame()
    result = cdf.mapping()
    assert "embeddings" in result
    assert result["title"] == "hello"


def test_mapping_omits_unmapped_names():
    cdf = _packed_like_frame()
    result = cdf.mapping(names=["store_status", "not_a_column"])
    assert set(result) == {"store_status"}


def test_mapping_names_mapped_missing_column_raises():
    cdf = _packed_like_frame()
    cdf.update_name_column_map("ghost", "ghost_column")
    with pytest.raises(KeyError, match="ghost_column"):
        cdf.mapping(names=["ghost"])


def test_liquid_to_value_does_not_get_unmentioned_columns():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    rendered = cdf.liquid_to_value("{{ store_status.output.path }}")
    assert rendered == "/tmp/out"
    assert "embeddings" not in columns
    assert columns == ["store_status"]


def test_liquid_to_value_named_embeddings_still_fetched():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    rendered = cdf.liquid_to_value("{{ embeddings[0] }}")
    assert rendered == "0"
    assert "embeddings" in columns


def test_liquid_to_value_static_html_no_get_value():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    rendered = cdf.liquid_to_value("<p>static html</p>")
    assert rendered == "<p>static html</p>"
    assert columns == []


def test_liquid_to_value_title_context_excludes_embeddings():
    cdf = _packed_like_frame()
    captured = {}
    orig_from_string = cdf.compute._liquid_env.from_string

    def wrap(source):
        template = orig_from_string(source)
        orig_render = template.render

        def render(**kwargs):
            captured.update(kwargs)
            return orig_render(**kwargs)

        template.render = render
        return template

    cdf.compute._liquid_env.from_string = wrap
    cdf.liquid_to_value("{{ title }}")
    assert "title" in captured
    assert "embeddings" not in captured


def test_view_to_value_liquid_does_not_prebuild_full_mapping():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    rendered = cdf.view_to_value({"liquid": "{{ selected_doc }}"})
    assert rendered == "doc1"
    assert "embeddings" not in columns
    assert columns == ["selected_doc"]


def test_mapping_debug_log_does_not_stringify_cell():
    cdf = lynguine.assess.data.CustomDataFrame(
        [{"title": "hello", "embeddings": [Boom()]}]
    )
    cdf._augment_column_names(cdf)
    result = cdf.mapping(names=["title", "embeddings"])
    assert result["title"] == "hello"
    assert isinstance(result["embeddings"], list)


def test_liquid_to_value_parse_failure_falls_back_to_full_mapping(caplog):
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    with caplog.at_level(logging.WARNING, logger="lynguine.assess.data"):
        try:
            cdf.liquid_to_value("{% for k, v in vars %}{{ k }}{% endfor %}")
        except Exception:
            pass
    assert any("identifier extraction failed" in rec.message for rec in caplog.records)
    assert "embeddings" in columns
    assert "title" in columns


def test_mapping_cache_hit_on_second_liquid_block():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    cdf.liquid_to_value("{{ store_status.output.path }}")
    cdf.liquid_to_value("{% if store_status %}ok{% endif %}")
    assert columns.count("store_status") == 1


def test_mapping_cache_miss_after_set_value():
    cdf = _packed_like_frame()
    columns = _count_get_value(cdf)
    cdf.liquid_to_value("{{ title }}")
    cdf.set_column("title")
    cdf.set_value("changed")
    cdf.liquid_to_value("{{ title }}")
    assert columns.count("title") == 2
    assert cdf.liquid_to_value("{{ title }}") == "changed"


def test_mapping_cache_miss_after_set_index():
    cdf = lynguine.assess.data.CustomDataFrame(
        pd.DataFrame(
            {
                "title": ["a", "b"],
                "embeddings": [list(range(3)), list(range(3))],
            }
        )
    )
    cdf._augment_column_names(cdf)
    columns = _count_get_value(cdf)
    cdf.set_index(cdf.index[0])
    cdf.liquid_to_value("{{ title }}")
    cdf.set_index(cdf.index[1])
    rendered = cdf.liquid_to_value("{{ title }}")
    assert rendered == "b"
    assert columns.count("title") == 2
