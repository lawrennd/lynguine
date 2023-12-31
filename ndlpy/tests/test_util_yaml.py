import pytest
from ndlpy.util.yaml import (
    update_from_file,
    header_field,
    header_fields,
    extract_header_body,
    FileFormatError,
)

# Mock Data
mock_yaml_content = {
    "testfile.yml": {"key2": "new_value2", "key3": "value3"},
    "header_file.yml": {"field1": "value1", "field2": "value2"},
    "header_body_file.yml": {
        "field1": "value1",
        "content": "This is the body content.",
    },
    "user_config.yml": {"field1": "value1", "field2": "value2"},
}


@pytest.fixture
def mock_read_yaml_file(monkeypatch):
    def mock_read(filename):
        return mock_yaml_content[filename]

    monkeypatch.setattr("ndlpy.access.io.read_yaml_file", mock_read)


@pytest.fixture
def mock_read_markdown_file(monkeypatch):
    def mock_read(filename):
        return mock_yaml_content[filename]

    monkeypatch.setattr("ndlpy.access.io.read_markdown_file", mock_read)


# Test update_from_file
def test_update_from_file(mock_read_yaml_file):
    test_dict = {"key1": "value1"}
    filename = "testfile.yml"

    updated_dict = update_from_file(test_dict, filename)

    assert updated_dict == {"key1": "value1", "key2": "new_value2", "key3": "value3"}


# Test header_field
def test_header_field(mock_read_yaml_file):
    fields = {"field1": "value1"}
    field_to_get = "field1"

    result = header_field(field_to_get, fields, ["user_config.yml"])

    assert result == "value1"

    # Test for FileFormatError
    with pytest.raises(FileFormatError):
        header_field("nonexistent_field", fields, ["user_config.yml"])


# Test header_fields
def test_header_fields(mock_read_markdown_file):
    filename = "header_file.yml"

    headers = header_fields(filename)

    assert headers == {"field1": "value1", "field2": "value2"}


# Test extract_header_body
def test_extract_header_body(mock_read_markdown_file):
    filename = "header_body_file.yml"

    header, body = extract_header_body(filename)

    assert header == {"field1": "value1"}
    assert body == "This is the body content."
