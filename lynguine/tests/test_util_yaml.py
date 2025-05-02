import pytest
from unittest.mock import patch, MagicMock
from lynguine.util.yaml import (
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
    "_config.yml": {"field3": "value3", "field4": "value4"},
    "nonexistent_file.yml": {},
}


@pytest.fixture
def mock_read_yaml_file(monkeypatch):
    def mock_read(filename):
        if filename not in mock_yaml_content:
            raise ValueError(f"File not found: {filename}")
        return mock_yaml_content[filename]

    monkeypatch.setattr("lynguine.access.io.read_yaml_file", mock_read)


@pytest.fixture
def mock_read_markdown_file(monkeypatch):
    def mock_read(filename):
        if filename not in mock_yaml_content:
            raise ValueError(f"File not found: {filename}")
        return mock_yaml_content[filename]

    monkeypatch.setattr("lynguine.access.io.read_markdown_file", mock_read)


# Test update_from_file
def test_update_from_file(mock_read_yaml_file):
    test_dict = {"key1": "value1"}
    filename = "testfile.yml"

    updated_dict = update_from_file(test_dict, filename)

    assert updated_dict == {"key1": "value1", "key2": "new_value2", "key3": "value3"}


def test_update_from_file_non_existent():
    with patch("lynguine.access.io.read_yaml_file") as mock_read:
        mock_read.side_effect = ValueError("File not found")
        test_dict = {"key1": "value1"}
        filename = "nonexistent_file.yml"

        with pytest.raises(ValueError):
            update_from_file(test_dict, filename)


# Test header_field
def test_header_field_from_fields():
    fields = {"field1": "value1", "field2": "value2"}
    field_to_get = "field1"

    result = header_field(field_to_get, fields)

    assert result == "value1"


def test_header_field_from_config_file():
    # Mock the Interface.from_file method
    with patch("lynguine.config.interface.Interface.from_file") as mock_from_file:
        mock_interface = MagicMock()
        mock_interface.__getitem__.return_value = "value3"
        mock_interface.__contains__.return_value = True
        mock_from_file.return_value = mock_interface

        fields = {"field1": "value1", "field2": "value2"}
        field_to_get = "field3"

        result = header_field(field_to_get, fields)

        assert result == "value3"
        mock_from_file.assert_called_once_with(["_config.yml"], directory=".")


def test_header_field_not_found():
    # Mock the Interface.from_file method for field not found
    with patch("lynguine.config.interface.Interface.from_file") as mock_from_file:
        mock_interface = MagicMock()
        mock_interface.__contains__.return_value = False
        mock_from_file.return_value = mock_interface

        fields = {"field1": "value1", "field2": "value2"}
        field_to_get = "nonexistent_field"

        # Test for FileFormatError when field is not found
        with pytest.raises(FileFormatError) as excinfo:
            header_field(field_to_get, fields)
        
        assert "Field not found in file or defaults" in str(excinfo.value)
        assert field_to_get in str(excinfo.value)


def test_header_field_custom_config():
    # Mock the Interface.from_file method
    with patch("lynguine.config.interface.Interface.from_file") as mock_from_file:
        mock_interface = MagicMock()
        mock_interface.__getitem__.return_value = "custom_value"
        mock_interface.__contains__.return_value = True
        mock_from_file.return_value = mock_interface

        fields = {"field1": "value1"}
        field_to_get = "custom_field"
        user_file = ["custom_config.yml"]

        result = header_field(field_to_get, fields, user_file)

        assert result == "custom_value"
        mock_from_file.assert_called_once_with(user_file, directory=".")


# Test header_fields
def test_header_fields(mock_read_markdown_file):
    filename = "header_file.yml"

    headers = header_fields(filename)

    assert headers == {"field1": "value1", "field2": "value2"}


def test_header_fields_nonexistent_file():
    with patch("lynguine.access.io.read_markdown_file") as mock_read:
        mock_read.side_effect = ValueError("File not found")
        with pytest.raises(ValueError):
            header_fields("nonexistent_file.yml")


# Test extract_header_body
def test_extract_header_body(mock_read_markdown_file):
    filename = "header_body_file.yml"

    header, body = extract_header_body(filename)

    assert header == {"field1": "value1"}
    assert body == "This is the body content."


def test_extract_header_body_no_content(mock_read_markdown_file):
    filename = "header_file.yml"

    header, body = extract_header_body(filename)

    assert header == {"field1": "value1", "field2": "value2"}
    assert body is None


def test_extract_header_body_nonexistent_file():
    with patch("lynguine.access.io.read_markdown_file") as mock_read:
        mock_read.side_effect = ValueError("File not found")
        with pytest.raises(ValueError):
            extract_header_body("nonexistent_file.yml")


# Test FileFormatError
def test_file_format_error():
    # Test with just index
    error = FileFormatError(1)
    assert "File format error occured with index 1" in str(error)
    
    # Test with message
    error = FileFormatError(2, "Custom message")
    assert "Custom message" in str(error)
    
    # Test with field
    error = FileFormatError(3, field="test_field")
    assert "File format error occured with index 3" in str(error)
    assert "field: test_field" in str(error)
    
    # Test with both message and field
    error = FileFormatError(4, "Another message", "another_field")
    assert "Another message" in str(error)
    assert "field: another_field" in str(error)
