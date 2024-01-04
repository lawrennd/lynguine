import os

import pandas as pd
import numpy as np
import tempfile
import pytest
from pytest_mock import mocker
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from pandas.testing import assert_frame_equal

import ndlpy
from ndlpy.util.fake import Generate
from ndlpy.access.io import (
    read_json, write_json, read_json_file, write_json_file,
    write_csv, read_csv, write_excel, read_excel, read_local, read_fake, read_bibtex, write_yaml,
    read_yaml, write_json_directory, read_json_directory,
    write_yaml_directory, read_yaml_directory, write_markdown_directory, write_bibtex, write_bibtex_file,
    read_markdown_directory,
    bibtex_column_order, bibtex_sort_by
)
from ndlpy.util.misc import extract_full_filename, extract_root_directory
from ndlpy.util.dataframe import reorder_dataframe
import ndlpy.access.io as io_module
import ndlpy.config.context as context
import ndlpy.util.fake

import bibtexparser as bp

GSPREAD_AVAILABLE = True
try:
    import gspread_pandas as gspd
except ImportError:
    GSPREAD_AVAILABLE = False


# Sample data setup
sample_dict = {
    'date': [datetime(2022, 1, 1), datetime(2022, 1, 2)],
    'integer': [1, 2],
    'string': ['test1', 'test2']
}
sample_df = pd.DataFrame(sample_dict)

directory_name = '.'
details = {
    "directory": directory_name,
    "header": 0,
}

json_file_name = 'test.json'
json_details = details.copy()
json_details["filename"] = json_file_name

yaml_file_name = 'test.yaml'
yaml_details = details.copy()
yaml_details["filename"] = yaml_file_name

@pytest.fixture
def mock_read_json_file():
    with patch('ndlpy.access.io.read_json_file') as mock:
        yield mock

@pytest.fixture
def mock_write_json_file():
    with patch('ndlpy.access.io.write_json_file') as mock:
        yield mock

@pytest.fixture
def mock_open():
    with patch('builtins.open', new_callable=mock_open) as mock:
        yield mock

@pytest.fixture
def mock_json_load():
    with patch('json.load') as mock:
        yield mock

@pytest.fixture
def mock_json_dump():
    with patch('json.dump') as mock:
        yield mock

@pytest.fixture
def sample_context():
    return context.Context(
        data={
            "google_oauth" : {"key": "DAFAFD"},
            "gspread_pandas" : {"key": "DAFAFD"},
            "logging" : {
                "level" : "DEBUG",
                "filename" : "test_access_io.log"
            },
        }
    )

# Example test for read_json
def test_read_json(mocker):
    # Mock dependencies
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.json")
    mocker.patch('ndlpy.access.io.read_json_file', return_value=[{'a': 1, 'b': 2}])

    # Test details
    details = {'path': 'path/to/file.json'}

    # Execute the function
    result = io_module.read_json(details)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert result.to_dict('records') == [{'a': 1, 'b': 2}]

# Example test for write_json
def test_write_json(mocker):
    mock_write_json_file = mocker.patch('ndlpy.access.io.write_json_file')
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.json")

    # Test data and details
    df = pd.DataFrame([{'a': 1, 'b': 2}])
    details = {'path': 'path/to/file.json'}

    # Execute the function
    io_module.write_json(df, details)

    # Assertions
    mock_write_json_file.assert_called_once_with(df.to_dict('records'), "path/to/file.json")


# Test for read_yaml
def test_read_yaml(mocker):
    # Mock dependencies
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.yaml")
    mocker.patch('ndlpy.access.io.read_yaml_file', return_value=[{'c': 3, 'd': 4}])

    # Test details
    details = {'path': 'path/to/file.yaml'}

    # Execute the function
    result = io_module.read_yaml(details)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert result.to_dict('records') == [{'c': 3, 'd': 4}]

# Test for write_yaml
def test_write_yaml(mocker):
    mock_write_yaml_file = mocker.patch('ndlpy.access.io.write_yaml_file')
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.yaml")

    # Test data and details
    df = pd.DataFrame([{'c': 3, 'd': 4}])
    details = {'path': 'path/to/file.yaml'}

    # Execute the function
    io_module.write_yaml(df, details)

    # Assertions
    mock_write_yaml_file.assert_called_once_with(df.to_dict('records'), "path/to/file.yaml")

# Test for read_markdown
def test_read_markdown(mocker):
    mock_extract_full_filename = mocker.patch('ndlpy.access.io.extract_full_filename', return_value='test.md')
    mock_read_markdown_file = mocker.patch('ndlpy.access.io.read_markdown_file', return_value={'key': 'value'})

    details = {'filename': 'test.md'}
    result = ndlpy.access.io.read_markdown(details)

    assert isinstance(result, pd.DataFrame)
    assert result.to_dict('records')[0] == {'key': 'value'}
    mock_extract_full_filename.assert_called_once_with(details)
    mock_read_markdown_file.assert_called_once_with('test.md')

    
# Test for read_bibtex
def test_read_bibtex(mocker):
    # Mock dependencies
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.bib")
    mock_read_bibtex_file = mocker.patch('ndlpy.access.io.read_bibtex_file', return_value=[{'author': 'Doe', 'year': 2020, 'title': 'Sample'}])

    # Test details
    details = {
        'directory': 'path/to/',
        'filename' : 'file.bib',
    }

    # Execute the function
    result, details = io_module.read_bibtex(details)

    assert isinstance(result, pd.DataFrame)
    assert result.to_dict('records') == [{'author': 'Doe', 'year': 2020, 'title': 'Sample'}]
    mock_read_bibtex_file.assert_called_once_with('path/to/file.bib')

# Test for write_bibtex
def test_write_bibtex(mocker):
    mock_write_bibtex_file = mocker.patch('ndlpy.access.io.write_bibtex_file')
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.bib")

    # Test data and details
    df = pd.DataFrame([{'author': 'Doe', 'year': 2020, 'title': 'Sample'}])
    details = {'path': 'path/to/file.bib'}

    # Execute the function
    io_module.write_bibtex(df, details)

    # Assertions
    mock_write_bibtex_file.assert_called_once_with(df.to_dict('records'), "path/to/file.bib")

# Test for read_directory
def test_read_directory(mocker):
    # Mock dependencies
    mocker.patch('os.path.expandvars', side_effect=lambda x: x)
    mocker.patch('glob.glob', return_value=['file1.txt', 'file2.txt'])
    mocker.patch('re.match', return_value=True)
    mocker.patch('ndlpy.access.io.read_files', return_value=pd.DataFrame([{'data': 'content'}]))

    details = {'source': [{'directory': 'test_dir', 'glob': '*.txt'}],
               'store_fields' : {'sourceRoot': 'sourceRoot', 'sourceDirectory': 'sourceDirectory', 'sourceFilename': 'sourceFilename'},
               }
    filereader = lambda x: {'file': x}

    result = io_module.read_directory(details, filereader)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

# Test for read_list
def test_read_list(mocker):
    # Mock read_files function
    mocker.patch('ndlpy.access.io.read_files', return_value=pd.DataFrame([{'data': 'content'}]))

    filelist = ['file1.txt', 'file2.txt']

    result = io_module.read_list(filelist)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

# Test for read_files
def test_read_files(mocker):
    # Mock dependencies
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('ndlpy.access.io.default_file_reader', return_value=lambda x: {'file': x})

    filelist = ['file1.txt', 'file2.txt']

    result = io_module.read_files(filelist)

    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(filelist)
    assert all(f in result['sourceFile'].values for f in filelist)


# Test for write_directory
def test_write_directory(mocker):
    # Mock dependencies
    mocker.patch('os.path.expandvars', side_effect=lambda x: x)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.makedirs')
    mock_filewriter = mocker.patch('ndlpy.access.io.write_json_file', side_effect=lambda data, filename, **args: None)

    df = pd.DataFrame([{'filename': 'file1.json', 'root': '/path', 'directory': '/to', 'data': 'content1'},
                       {'filename': 'file2.json', 'root': '/path', 'directory': '/to', 'data': 'content2'}])
    details = {'store_fields': {'filename': 'filename', 'directory': 'directory', 'root': 'root'}}

    io_module.write_directory(df, details)

    # Assertions
    assert mock_filewriter.call_count == len(df)

# Test for read_json_file
def test_read_json_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='{"key": "value"}'))
    mocker.patch('json.load', return_value={'key': 'value'})

    result = io_module.read_json_file("test.json")

    assert result == {'key': 'value'}
    mock_open.assert_called_once_with("test.json", "r")

# Test for write_json_file
def test_write_json_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('json.dump')

    io_module.write_json_file({'key': 'value'}, "test.json")

    mock_open.assert_called_once_with("test.json", "w")

# Test for default_file_reader
def test_default_file_reader():
    assert io_module.default_file_reader("markdown") == io_module.read_markdown_file
    assert io_module.default_file_reader("yaml") == io_module.read_yaml_file
    assert io_module.default_file_reader("json") == io_module.read_json_file
    assert io_module.default_file_reader("bibtex") == io_module.read_bibtex_file
    assert io_module.default_file_reader("docx") == io_module.read_docx_file
    with pytest.raises(ValueError):
        io_module.default_file_reader("unknown")

# Test for default_file_writer
def test_default_file_writer():
    assert io_module.default_file_writer("markdown") == io_module.write_markdown_file
    assert io_module.default_file_writer("yaml") == io_module.write_yaml_file
    assert io_module.default_file_writer("json") == io_module.write_json_file
    assert io_module.default_file_writer("bibtex") == io_module.write_bibtex_file
    assert io_module.default_file_writer("docx") == io_module.write_docx_file
    with pytest.raises(ValueError):
        io_module.default_file_writer("unknown")
        
# test for read_file
def test_read_file(mocker):
    mocker.patch('ndlpy.access.io.extract_file_type', return_value='yaml')
    mocker.patch('ndlpy.access.io.read_yaml_file', return_value={'key': 'value'})

    result = io_module.read_file("test.yaml")

    assert result == {'key': 'value'}

# test for read_yaml_file
def test_read_yaml_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='key: value'))
    mocker.patch('yaml.safe_load', return_value={'key': 'value'})

    result = io_module.read_yaml_file("test.yaml")

    assert result == {'key': 'value'}
    mock_open.assert_called_once_with("test.yaml", "r")


# test for write_yaml_file
def test_write_yaml_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    yaml_dump = mocker.patch('yaml.dump')

    io_module.write_yaml_file({'key': 'value'}, "test.yaml")

    mock_open.assert_called_once_with("test.yaml", "w")
    yaml_dump.assert_called_once()

# test for read_bibtex_file
def test_read_bibtex_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='@article{key, title={Title}}'))
    bibdata = bp.bibdatabase.BibDatabase()
    bibdata.entries = {'entries': [{'ID': 'key', 'ENTRYTYPE' : 'article', 'title': 'Title'}]}
    moker_bibtexparser_load = mocker.patch('bibtexparser.load', return_value=bibdata)

    result = io_module.read_bibtex_file("test.bib")

    assert result == {'entries': [{'ID': 'key', 'ENTRYTYPE' : 'article', 'title': 'Title'}]}
    mock_open.assert_called_once_with("test.bib", "r")

# test for write_bibtex_file
def test_write_bibtex_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_bibtexparser_dump = mocker.patch('bibtexparser.dump')

    io_module.write_bibtex_file([{'ID': 'key', 'ENTRYTYPE' : 'article', 'title': 'Title'}], "test.bib")

    mock_open.assert_called_once_with("test.bib", "w")
    mock_bibtexparser_dump.assert_called_once()

# test for write_yaml_file
def test_write_yaml_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_yaml_dump = mocker.patch('yaml.dump')

    data = {'key': 'value'}
    filename = "test.yaml"
    io_module.write_yaml_file(data, filename)

    mock_open.assert_called_once_with(filename, "w")
    mock_yaml_dump.assert_called_once()

# test for read_yaml_file
def test_read_yaml_meta_file(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mock_read_yaml = mocker.patch('ndlpy.access.io.read_yaml_file', return_value={'meta': 'data'})

    filename = "test"
    result = io_module.read_yaml_meta_file(filename)

    assert result == {'meta': 'data'}
    mock_read_yaml.assert_called_once_with("test.yml")

# test for write_yaml_meata_file
def test_write_yaml_meta_file(mocker):
    mock_write_yaml = mocker.patch('ndlpy.access.io.write_yaml_file')

    data = {'meta': 'data'}
    filename = "test"
    io_module.write_yaml_meta_file(data, filename)

    mock_write_yaml.assert_called_once_with(data, "test.yml")

# test for read_markdown_file
def test_read_markdown_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='---\nkey: value\n---\ncontent'))
    mock_frontmatter_load = mocker.patch('frontmatter.load', return_value=type('Post', (object,), {'metadata': {'key': 'value'}, 'content': 'content'}))

    filename = "test.md"
    result = io_module.read_markdown_file(filename)

    assert result == {'key': 'value', 'content': 'content'}
    mock_open.assert_called_once_with(filename, "r")
    mock_frontmatter_load.assert_called_once()

# test for read_docx_file
def test_read_docx_file(tmpdir,mocker):
    mocker.patch('tempfile.gettempdir', return_value=tmpdir)
    mocker.patch('pypandoc.convert_file')
    mock_read_markdown = mocker.patch('ndlpy.access.io.read_markdown_file', return_value={'key': 'value'})

    filename = "test.docx"
    result = io_module.read_docx_file(filename)

    assert result == {'key': 'value'}
    mock_read_markdown.assert_called_once_with(os.path.join(tmpdir, 'tmp.md'), True)

# test for read_talk_file
def test_read_talk_file(mocker):
    mock_read_markdown = mocker.patch('ndlpy.access.io.read_markdown_file', return_value={'key': 'value'})
    mock_remove_nan = mocker.patch('ndlpy.access.io.remove_nan', return_value={'key': 'value'})

    filename = "talk.md"
    result = io_module.read_talk_file(filename)

    assert result == {'key': 'value'}
    mock_read_markdown.assert_called_once_with(filename, True)
    mock_remove_nan.assert_called_once_with({'key': 'value'})

# test for read_talk_include_file
def test_read_talk_include_file(mocker):
    mock_read_markdown = mocker.patch('ndlpy.access.io.read_markdown_file', return_value={'key': 'value', 'nan_field': np.nan})
    mock_remove_nan = mocker.patch('ndlpy.access.io.remove_nan', return_value={'key': 'value'})

    filename = "talk_include.md"
    result = io_module.read_talk_include_file(filename)

    assert result == {'key': 'value'}
    mock_read_markdown.assert_called_once_with(filename, True)
    mock_remove_nan.assert_called_once_with({'key': 'value', 'nan_field': np.nan})

# test for test_write_url_file
def test_write_url_file():
    data = {}
    filename = "url.txt"
    content = "http://example.com"

    with pytest.raises(NotImplementedError):
        io_module.write_url_file(data, filename, content)
    
# test for write_markdown_file
def test_write_markdown_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    data = {'key': 'value', 'content': '# Markdown Content'}
    filename = "test.md"
    io_module.write_markdown_file(data, filename)

    # For some reason frontmatter writes to a BytesIO not a StringIO, so "wb" not "w"
    mock_open.assert_called_once_with(filename, "wb")
    handle = mock_open()
    handle.write.assert_called_with(b'---\nkey: value\n---\n\n# Markdown Content')

# test for create_document_content
def test_create_document_content():

    # Test Case 1: All parameters provided
    kwargs_1 = {
        'filename': 'document.md',
        'directory': '/path/to',
        'content': 'Sample content',
        'additional': 'extra data'
    }
    result_1 = io_module.create_document_content(**kwargs_1)
    assert result_1 == ({'additional': 'extra data'}, '/path/to/document.md', 'Sample content')

    # Test Case 2: Missing 'content'
    kwargs_2 = {
        'filename': 'document.md',
        'directory': '/path/to',
        'additional': 'extra data'
    }
    result_2 = io_module.create_document_content(**kwargs_2)
    assert result_2 == ({'additional': 'extra data'}, '/path/to/document.md', '')

    # Test Case 3: Only 'content' provided
    kwargs_3 = {'content': 'Sample content'}
    with pytest.raises(ValueError):
        result_3 = io_module.create_document_content(**kwargs_3)

    
# test for create_letter 
def test_create_letter(mocker):
    mock_create_document_content = mocker.patch('ndlpy.access.io.create_document_content', return_value=('data', 'filename.md', 'content'))
    mock_write_letter_file = mocker.patch('ndlpy.access.io.write_letter_file')

    io_module.create_letter()

    mock_create_document_content.assert_called_once()
    mock_write_letter_file.assert_called_once_with(data='data', filename='filename.md', content='content')

# test for write_letter_file
def test_write_letter_file(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_frontmatter_dump = mocker.patch('frontmatter.dump')

    data = {'key': 'value', 'content': 'Letter content'}
    filename = "letter.md"
    io_module.write_letter_file(data, filename, 'content')

    mock_open.assert_called_once_with(filename, "wb")
    mock_frontmatter_dump.assert_called_once()

# test for write_formlink 
def test_write_formlink(mocker):
    mock_write_url_file = mocker.patch('ndlpy.access.io.write_url_file')

    data = {'key': 'value'}
    filename = "formlink.txt"
    content = "http://example.com/form"
    io_module.write_formlink(data, filename, content)

    mock_write_url_file.assert_called_once_with(data, filename, content, True)

# test for write_docx_file
def test_write_docx_file(tmpdir, mocker):
    mocker.patch('tempfile.gettempdir', return_value=tmpdir)
    mock_write_markdown_file = mocker.patch('ndlpy.access.io.write_markdown_file')
    mocker.patch('pypandoc.convert_file')

    data = {'key': 'value'}
    filename = "document.docx"
    content = "Content"
    io_module.write_docx_file(data, filename, content)

    tmpfile = os.path.join(tmpdir, 'tmp.md')
    mock_write_markdown_file.assert_called_once_with(data, tmpfile, content, True)

# test for write_tex_file
def test_write_tex_file(tmpdir, mocker):
    mocker.patch('tempfile.gettempdir', return_value=tmpdir)
    mock_write_markdown_file = mocker.patch('ndlpy.access.io.write_markdown_file')
    mocker.patch('pypandoc.convert_file')

    data = {'key': 'value'}
    filename = "document.tex"
    content = "Content"
    io_module.write_tex_file(data, filename, content)

    tmpfile = os.path.join(tmpdir, 'tmp.md')
    mock_write_markdown_file.assert_called_once_with(data, tmpfile, content, True)

# test for read_csv
def test_read_csv(mocker):
    mock_read_csv = mocker.patch('pandas.read_csv', return_value=pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}))
    mocker.patch('ndlpy.access.io.extract_dtypes', return_value={'col1': 'int'})
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value='test.csv')

    details = {'header': 0, 'delimiter': ',', 'quotechar': '"'}
    result = io_module.read_csv(details)

    assert isinstance(result, pd.DataFrame)
    mock_read_csv.assert_called_once_with('test.csv', dtype={'col1': 'int'}, header=0, delimiter=',', quotechar='"')

# test for read_excel
def test_read_excel(mocker):
    mock_read_excel = mocker.patch('pandas.read_excel', return_value=pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}))
    mocker.patch('ndlpy.access.io.extract_dtypes', return_value={'col1': 'int'})
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value='test.xlsx')

    details = {'header': 0, 'sheet': 'Sheet1'}
    result = io_module.read_excel(details)

    assert isinstance(result, pd.DataFrame)
    mock_read_excel.assert_called_once_with('test.xlsx', sheet_name='Sheet1', dtype={'col1': 'int'}, header=0)

# Tests for read_local
def test_read_local_valid_dict():
    details = {'data': [{'a': 1, 'b': 2}], 'index': [0]}
    df = read_local(details)
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == 'index'
    assert list(df.columns) == ['a', 'b']

def test_read_local_invalid_input(mocker):
    log_mock = mocker.patch('ndlpy.access.io.log')
    with pytest.raises(ValueError):
        read_local(['not', 'a', 'dict'])
    log_mock.error.assert_called_once()

def test_read_local_missing_keys(mocker):
    log_mock = mocker.patch('ndlpy.access.io.log')
    with pytest.raises(ValueError):
        read_local({'values': [{'a': 1, 'b': 2}]})  # 'data' key is missing
    log_mock.error.assert_called_once()

def test_read_local_default_index_name():
    details = {'data': [{'a': 1, 'b': 2}], 'index': [0]}
    df = read_local(details)
    assert df.index.name == 'index'

def test_read_local_error_logging(mocker):
    log_mock = mocker.patch('ndlpy.access.io.log')
    with pytest.raises(ValueError):
        read_local({'wrong_key': 'value'})
    log_mock.error.assert_called_once()


@pytest.fixture
def valid_details():
    return {
        'nrows': 5,
        'cols': {
            'col1': 'familyName',
            'col2': 'givenName',
            'col3': 'address',
        }
    }

@pytest.fixture
def valid_details_list():
    # Return the cols as a list instead of a dict
    return {
        'nrows': 5,
        'cols' : ['familyName', 'givenName', 'address']
    }

@pytest.fixture
def mock_generate(mocker):
    mocker.patch.object(ndlpy.util.fake.Generate, 'familyName', return_value='Ogedegbe')
    mocker.patch.object(ndlpy.util.fake.Generate, 'givenName', return_value='Henrietta')
    mocker.patch.object(ndlpy.util.fake.Generate, 'address', return_value='123 Main St')

# test for read_fake with cols input as list
def test_read_fake_with_valid_list_input(mock_generate, valid_details_list):
    df = read_fake(valid_details_list)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (5, 3)  # 5 rows and 3 columns
    assert all(col in df.columns for col in valid_details_list['cols'])

def test_read_fake_invalid_list(mock_generate):
    with pytest.raises(ValueError):
        read_fake({'nrows': 10, 'cols': ["not_a_valid_generate_attribute"]})

# test for read_fake with cols input as dict
def test_read_fake_with_valid_input(mock_generate, valid_details):
    df = read_fake(valid_details)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (5, 3)  # 5 rows and 3 columns
    assert all(col in df.columns for col in valid_details['cols'])
    
def test_read_fake_with_non_dict_input(mock_generate):
    with pytest.raises(ValueError):
        read_fake(['not', 'a', 'dict'])

def test_read_fake_missing_required_keys(mock_generate):
    with pytest.raises(ValueError):
        read_fake({'nrows': 5})

def test_read_fake_invalid_nrows(mock_generate):
    with pytest.raises(ValueError):
        read_fake({'nrows': -1, 'cols': {'col1': 'givenName'}})

def test_read_fake_invalid_cols(mock_generate):
    with pytest.raises(ValueError):
        read_fake({'nrows': 5, 'cols': 'not-a-dict'})

def test_read_fake_non_callable_generator(valid_details, mock_generate):
    valid_details['cols']['col1'] = 'non_callable'
    with pytest.raises(ValueError):
        read_fake(valid_details)

def test_read_fake_nonexistent_generator(valid_details, mock_generate):
    valid_details['cols']['col1'] = 'nonexistent_gen'
    with pytest.raises(ValueError):
        read_fake(valid_details)


# test for read_gsheet
def test_read_gsheet(sample_context, mocker):
    if GSPREAD_AVAILABLE:
        mocker.patch('ndlpy.access.io.ctxt', sample_context)
        mocker.patch('ndlpy.access.io.extract_dtypes', return_value={'col1': 'int'})
        mocker.patch('ndlpy.access.io.extract_full_filename', return_value='sheet_id')
        mocker.patch('ndlpy.access.io.extract_sheet', return_value=0)
        mock_spread = mocker.MagicMock()
        mocker.patch('gspread_pandas.Spread', return_value=mock_spread)
        mock_spread.sheet_to_df.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

        details = {'header': 0}
        result = io_module.read_gsheet(details)

        assert isinstance(result, pd.DataFrame)
        mock_spread.sheet_to_df.assert_called_once()

# test for write_excel
def test_write_excel(mocker):
    excel_writer = pd.ExcelWriter("test.xlsx", engine='xlsxwriter')
    mock_excel_writer = mocker.patch('pandas.ExcelWriter', return_value=excel_writer)
    mock_to_excel = mocker.patch('pandas.DataFrame.to_excel', return_value=pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}))
    mock_to_excel = mocker.patch('pandas.DataFrame.to_excel', return_value=pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}))
    
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value='test.xlsx')

    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    details = {'header': 0, 'sheet': 'Sheet1'}
    io_module.write_excel(df, details)

    mock_excel_writer.assert_called_once_with('test.xlsx', engine='xlsxwriter', datetime_format="YYYY-MM-DD HH:MM:SS.000")
    mock_to_excel.assert_called_once_with(excel_writer, sheet_name="Sheet1", startrow=0, index=False)

# test for write_csv
def test_write_csv(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value='test.csv')

    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    details = {'delimiter': ',', 'quotechar': '"'}
    io_module.write_csv(df, details)

    mock_open.assert_called_once_with('test.csv', 'w')

# test for write_gsheet
def test_write_gsheet(sample_context, mocker):
    if GSPREAD_AVAILABLE:
        mocker.patch('ndlpy.access.io.ctxt', sample_context)
        mocker.patch('ndlpy.access.io.extract_full_filename', return_value='sheet_id')
        mocker.patch('ndlpy.access.io.extract_sheet', return_value=0)
        mock_spread = mocker.MagicMock()
        mocker.patch('gspread_pandas.Spread', return_value=mock_spread)

        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        details = {'header': 0}
        io_module.write_gsheet(df, details)

        mock_spread.df_to_sheet.assert_called_once()

# test for gdrf_
def test_gdrf_(mocker):
    # Example usage of gdrf_
    test_reader = io_module.gdrf_(
        default_glob="*.test",
        filereader=lambda x: x,
        name="test_reader",
        docstr="Test directory reader."
    )

    # Check if the function has the correct properties
    assert callable(test_reader)
    assert test_reader.__name__ == "test_reader"
    assert "Test directory reader." in test_reader.__doc__

    # Example details to pass
    details = {'glob': '*.test', 'source': 'source_dir'}

    # Mock the read_directory function and check if it's called correctly
    mock_read_dir = mocker.patch('ndlpy.access.io.read_directory', return_value=pd.DataFrame([{'data': 'content'}]))
    test_reader(details)
    mock_read_dir.assert_called_once()

# test for gdwf_
def test_gdwf_(mocker):
    # Example usage of gdwf_
    test_writer = io_module.gdwf_(
        filewriter=lambda x, y: None,
        name="test_writer",
        docstr="Test directory writer."
    )

    # Check if the function has the correct properties
    assert callable(test_writer)
    assert test_writer.__name__ == "test_writer"
    assert "Test directory writer." in test_writer.__doc__

    # Example dataframe and details
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    details = {'glob': '*.test', 'source': 'source_dir'}

    # Mock the write_directory function and check if it's called correctly
    mock_write_dir = mocker.patch('ndlpy.access.io.write_directory')
    test_writer(df, details)
    mock_write_dir.assert_called_once()

# test for populate_directory_readers
def test_populate_directory_readers():
    io_module.populate_directory_readers(io_module.directory_readers)
    for reader in io_module.directory_readers:
        assert hasattr(io_module, reader["name"])

# test for populate_directory_writers
def test_populate_directory_writers():
    io_module.populate_directory_writers(io_module.directory_writers)
    for writer in io_module.directory_writers:
        assert hasattr(io_module, writer["name"])
    
# Test functions
def test_read_json2(mock_read_json_file):
    full_filename = extract_full_filename(json_details)
    mock_read_json_file.return_value = sample_dict
    df = read_json(json_details)
    mock_read_json_file.assert_called_once_with(full_filename)
    assert_frame_equal(df, sample_df)

def test_write_json2(mock_write_json_file):
    full_filename = extract_full_filename(json_details)
    write_json(sample_df, json_details)
    mock_write_json_file.assert_called_once_with(
        sample_df.to_dict("records"),
        full_filename,
    )
    

# File operation tests
def test_write_read_csv(tmpdir):
    details = {
        "filename": "test.csv",
        "directory": str(tmpdir),
        "header": 0,
        "delimiter": ",",
        "quotechar": "\"",
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    write_csv(data, details)
    read_data = read_csv(details)
    assert_frame_equal(data, read_data)

def test_write_read_excel(tmpdir):
    details = {
        "filename": "test.xlsx",
        "directory": str(tmpdir),
        "header": 0,
        "sheet": "Sheet1",
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    write_excel(data, details)
    read_data = read_excel(details)
    assert_frame_equal(data, read_data)

def test_write_read_json(tmpdir):
    details = {
        "filename": "test.json",
        "directory": str(tmpdir),
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    write_json(data, details)
    read_data = read_json(details)
    assert_frame_equal(data, read_data)

def test_write_read_yaml(tmpdir):
    details = {
        "filename": "test.yaml",
        "directory": str(tmpdir),
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    write_yaml(data, details)
    read_data = read_yaml(details)
    assert_frame_equal(read_data, data)

   
def test_write_bibtex_with_unique_ids(tmpdir):
    data = [
        {"ENTRYTYPE": "misc", "ID": "entry1", "title": "Title One"},
        {"ENTRYTYPE": "misc", "ID": "entry2", "title": "Title Two"}
    ]
    filename = os.path.join(tmpdir,"test_unique_ids.bib")
    write_bibtex_file(data, filename)
    assert os.path.exists(filename)
    os.remove(filename)

def test_write_bibtex_with_duplicate_ids(tmpdir):
    data = [
        {"ENTRYTYPE": "misc", "ID": "entry1", "title": "Title One"},
        {"ENTRYTYPE": "misc", "ID": "entry1", "title": "Title Two"}
    ]
    with pytest.raises(ValueError):
        write_bibtex_file(data, os.path.join(tmpdir, "test_duplicate_ids.bib"))

def test_write_bibtex_with_missing_id(tmpdir):
    data = [{"ENTRYTYPE": "misc", "title": "Title One"}]
    with pytest.raises(ValueError):
        write_bibtex_file(data, os.path.join(tmpdir, "test_missing_id.bib"))

def test_write_bibtex_with_invalid_id(tmpdir):
    data = [{"ENTRYTYPE": "misc", "ID": "123 Invalid_ID", "title": "Title One"}]
    with pytest.raises(ValueError):
        write_bibtex_file(data, os.path.join(tmpdir, "test_invalid_id.bib"))

def letter_suffix(n : int) -> str:
    """
    Return the nth letter of the alphabet, where a=0, b=1, c=2, ..., aa=26, ab=27, ..., zz=701, aaa=702, ...

    :param n: The number to be converted to a letter.
    :type n: int
    :return: The letter.
    :rtype: str
    """
    if n < 26:
        return chr(n + 97)
    else:
        return letter_suffix(n // 26 - 1) + letter_suffix(n % 26)
    
def test_write_read_bibtex(tmpdir):
    details = {
        "filename": "test.bib",
        "directory": str(tmpdir),
    }
    row = lambda: ndlpy.util.fake.to_bibtex(ndlpy.util.fake.bibliography_entry())
    bib_rows = ndlpy.util.fake.rows(200, row)

    # List any duplicated ids.
    ids = [entry["ID"] for entry in bib_rows]
    newids = ids.copy()
    duplicates = [id for id in ids if ids.count(id) > 1]
    if len(duplicates) > 0:
        # Deduplicate ids by adding the seqence a, b, c ..., aa, ab, ac ... to the end of the id.
        for ind in range(len(ids)):
            if ids.count(ids[ind]) > 1:
                dup_num = ids[:ind].count(ids[ind])
                newids[ind] = newids[ind] + letter_suffix(dup_num)
        for ind in range(len(ids)):
            bib_rows[ind]["ID"] = newids[ind]

    # Write the bibtex file.
    # Make sure it's reordered and sorted so that assert equals can match frames.
    data = reorder_dataframe(pd.DataFrame(bib_rows), order=bibtex_column_order).sort_values(by=bibtex_sort_by).reset_index(drop=True)
    
    write_bibtex(data, details)
    read_data, details = read_bibtex(details)
    assert_frame_equal(read_data, data)
    
def test_write_read_json_directory(tmpdir):
    extension = ".json"
    details = {
        "directory": str(tmpdir),
        "source": [
            {
                "directory": str(tmpdir),
                "glob": "*" + extension,
            },
        ],
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    for ind in data.index:
        data.at[ind, "sourceRoot"], data.at[ind, "sourceDirectory"] = extract_root_directory(str(tmpdir))
        data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
    data = data.sort_values(by="sourceFilename").reset_index(drop=True)
    write_json_directory(data, details)
    read_data = read_json_directory(details)
    read_data = read_data.sort_values(by="sourceFilename").reset_index(drop=True)
    assert_frame_equal(data, read_data)

def test_write_read_yaml_directory(tmpdir):
    extension = ".yaml"
    details = {
        "directory": str(tmpdir),
        "source": [
            {
                "directory": str(tmpdir),
                "glob": "*" + extension,
            },
        ],
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    for ind in data.index:
        data.at[ind, "sourceRoot"], data.at[ind, "sourceDirectory"] = extract_root_directory(str(tmpdir))
        data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
    data = data.sort_values(by="sourceFilename").reset_index(drop=True)
    write_yaml_directory(data, details)
    read_data = read_yaml_directory(details)
    assert_frame_equal(data, read_data)

def test_write_read_markdown_directory(tmpdir):
    extension = ".md"
    details = {
        "directory": str(tmpdir),
        "source": [
            {
                "directory": str(tmpdir),
                "glob": "*" + extension,
            },
        ],
    }
    data = pd.DataFrame(ndlpy.util.fake.rows(30))
    for ind in data.index:
        data.at[ind, "sourceRoot"], data.at[ind, "sourceDirectory"] = extract_root_directory(str(tmpdir))
        data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
    data = data.sort_values(by="sourceFilename").reset_index(drop=True)
    write_markdown_directory(data, details)
    read_data = read_markdown_directory(details)
    assert_frame_equal(data, read_data)

# test finalize_data
def test_finalize_data_index_name():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    details = {'index': {'name': 'test_index'}}

    finalized_df, _ = ndlpy.access.io.finalize_data(df, details)

    assert finalized_df.index.name == 'test_index'

def test_finalize_data_rename_columns():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    details = {'rename_columns': {'a': 'x', 'b': 'y'}}

    finalized_df, _ = ndlpy.access.io.finalize_data(df, details)

    assert all(column in finalized_df.columns for column in ['x', 'y'])

def test_finalize_data_ignore_columns():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
    details = {'ignore_columns': ['c']}

    finalized_df, _ = ndlpy.access.io.finalize_data(df, details)

    assert 'c' not in finalized_df.columns

def test_finalize_data_invalid_rename_column():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    details = {'rename_columns': {'x': 'new_x'}}

    with pytest.raises(ValueError):
        ndlpy.access.io.finalize_data(df, details)

def test_finalize_data_invalid_ignore_column():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    details = {'ignore_columns': ['x']}

    with pytest.raises(ValueError):
        ndlpy.access.io.finalize_data(df, details)


# test read_data
@pytest.mark.parametrize("data_type, read_func", [
    ('excel', 'ndlpy.access.io.read_excel'),
    ('gsheet', 'ndlpy.access.io.read_gsheet'),
    ('csv', 'ndlpy.access.io.read_csv'),
    ('bibtex', 'ndlpy.access.io.read_bibtex'),
    ('json', 'ndlpy.access.io.read_json'),
    ('yaml', 'ndlpy.access.io.read_yaml'),
    ('markdown', 'ndlpy.access.io.read_markdown'),
    ('bibtex_directory', 'ndlpy.access.io.read_bibtex_directory'),
    ('json_directory', 'ndlpy.access.io.read_json_directory'),
    ('yaml_directory', 'ndlpy.access.io.read_yaml_directory'),
    ('markdown_directory', 'ndlpy.access.io.read_markdown_directory'),
    ('directory', 'ndlpy.access.io.read_plain_directory'),
    ('meta_directory', 'ndlpy.access.io.read_meta_directory'),
    ('docx_directory', 'ndlpy.access.io.read_docx_directory'),
    ('fake', 'ndlpy.access.io.read_fake'),
    ('local', 'ndlpy.access.io.read_local'),
    ('uncategorised_type', None),
])
def test_read_data(mocker, data_type, read_func):
    if read_func is None:
        with pytest.raises(ValueError):
            ndlpy.access.io.read_data({'type': data_type})
        return
    details = {'type': data_type}
    mock_func = mocker.patch(read_func, return_value=pd.DataFrame({'a': [1, 2]}))

    result, details = ndlpy.access.io.read_data(details)

    mock_func.assert_called_once_with(details)
    assert all(result == pd.DataFrame({'a': [1, 2]}))
    assert not result.empty

# test convert_data
def test_convert_data(mocker):
    mock_read_data = mocker.patch('ndlpy.access.io.read_data', return_value=(pd.DataFrame({'a': [1, 2]}), {}))
    mock_write_data = mocker.patch('ndlpy.access.io.write_data')

    read_details = {'type': 'excel'}
    write_details = {'type': 'csv'}

    ndlpy.access.io.convert_data(read_details, write_details)

    mock_read_data.assert_called_once_with(read_details)
    mock_write_data.assert_called_once()

# test data exists
def test_data_exists_file(mocker):
    mocker.patch('os.path.exists', return_value=True)
    details = {'filename': 'test.csv'}
    assert ndlpy.access.io.data_exists(details)

    mocker.patch('os.path.exists', return_value=False)
    assert not ndlpy.access.io.data_exists(details)


# test load_or_create_df
def test_load_or_create_df_exists(mocker):
    existing_df = pd.DataFrame({'a': [1, 2]})
    details = {'filename': 'test.csv'}
    mocker.patch('ndlpy.access.io.data_exists', return_value=True)
    mocker.patch('ndlpy.access.io.read_data', return_value=(existing_df, details))

    result = ndlpy.access.io.load_or_create_df(details, None)

    assert result[0].equals(existing_df)

# test load_or_create_df
def test_load_or_create_df_not_exists(mocker):
    mocker.patch('ndlpy.access.io.data_exists', return_value=False)
    details = {'filename': 'test.csv', 'columns': ['col1', 'col2']}
    index = pd.Index([1, 2], name='index')

    result = ndlpy.access.io.load_or_create_df(details, index)

    assert result[0].index.equals(index)
    assert list(result[0].columns) == ['index', 'col1', 'col2']
   
# test load_or_create_df
def test_load_or_create_df_no_index(mocker):
    existing_df = pd.DataFrame({'a': [1, 2]})
    mocker.patch('ndlpy.access.io.data_exists', return_value=False)
    mocker.patch('ndlpy.access.io.read_data', return_value=existing_df)

    details = {'filename': 'test.csv'}
    with pytest.raises(FileNotFoundError):
        ndlpy.access.io.load_or_create_df(details, None)


@pytest.mark.parametrize("data_type, write_func", [
    ('excel', 'ndlpy.access.io.write_excel'),
    ('gsheet', 'ndlpy.access.io.write_gsheet'),
    ('csv', 'ndlpy.access.io.write_csv'),
    ('bibtex', 'ndlpy.access.io.write_bibtex'),
    ('json', 'ndlpy.access.io.write_json'),
    ('yaml', 'ndlpy.access.io.write_yaml'),
    ('markdown', 'ndlpy.access.io.write_markdown'),
    ('yaml_directory', 'ndlpy.access.io.write_yaml_directory'),
    ('markdown_directory', 'ndlpy.access.io.write_markdown_directory'),
    ('meta_directory', 'ndlpy.access.io.write_meta_directory'),
    ('uncategorised_type', None),
])
def test_write_data(mocker, data_type, write_func):
    details = {'type': data_type}
    if write_func is None:
        with pytest.raises(ValueError):
            ndlpy.access.io.write_data({'type': data_type}, details)
        return
    mock_func = mocker.patch(write_func)
    df = pd.DataFrame({'a': [1, 2]})

    ndlpy.access.io.write_data(df, details)

    mock_func.assert_called_once_with(df, details)

# test global data
def test_globals_data_exists(mocker):
    details = {'filename': 'globals.csv'}
    existing_df = pd.DataFrame({'a': [1, 2]})
    mocker.patch('ndlpy.access.io.data_exists', return_value=True)
    mocker.patch('ndlpy.access.io.read_data', return_value=(existing_df, details))

    result, details = ndlpy.access.io.globals_data(details)

    assert result.equals(existing_df)

# test globals_data
def test_globals_data_not_exists(mocker):
    mocker.patch('ndlpy.access.io.data_exists', return_value=False)
    details = {'filename': 'globals.csv', 'columns': ['col1', 'col2']}
    index = pd.Index([1, 2], name='index')

    result, details = ndlpy.access.io.globals_data(details, index)

    assert result.index.equals(index)
    assert list(result.columns) == ['index', 'col1', 'col2']
    
@pytest.mark.parametrize("func, config_key", [
    (ndlpy.access.io.write_globals, 'globals'),
    (ndlpy.access.io.write_cache, 'cache'),
    (ndlpy.access.io.write_scores, 'scores'),
    (ndlpy.access.io.write_series, 'series'),
])
def test_write_functions(mocker, func, config_key):
    mock_write_data = mocker.patch('ndlpy.access.io.write_data')
    config = {config_key: {'type': 'csv'}}
    df = pd.DataFrame({'index': [1, 2], 'col1': [3, 4]}, index=[1, 2])

    func(df, config)

    assert mock_write_data.call_count == 1
