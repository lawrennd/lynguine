import os

import pandas as pd
import tempfile
import pytest
from pytest_mock import mocker
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from pandas.testing import assert_frame_equal

import ndlpy
import ndlpy.util.fake as fake
from ndlpy.access.io import (
    read_json, write_json, read_json_file, write_json_file,
    write_csv, read_csv, write_excel, read_excel, read_bibtex, write_yaml,
    read_yaml, write_json_directory, read_json_directory,
    write_yaml_directory, read_yaml_directory, write_markdown_directory, write_bibtex, write_bibtex_file,
    read_markdown_directory,
    bibtex_column_order, bibtex_sort_by
)
from ndlpy.util.misc import extract_full_filename, extract_root_directory
from ndlpy.util.dataframe import reorder_dataframe
import ndlpy.access.io as io_module

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

# Test for read_bibtex
def test_read_bibtex(mocker):
    # Mock dependencies
    mocker.patch('ndlpy.access.io.extract_full_filename', return_value="path/to/file.bib")
    mocker.patch('ndlpy.access.io.read_bibtex_file', return_value=[{'author': 'Doe', 'year': 2020, 'title': 'Sample'}])

    # Test details
    details = {'path': 'path/to/file.bib'}

    # Execute the function
    result = io_module.read_bibtex(details)

    # Assertions
    # Add assertions specific to the behavior of read_bibtex

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
    data = pd.DataFrame(fake.rows(30))
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
    data = pd.DataFrame(fake.rows(30))
    write_excel(data, details)
    read_data = read_excel(details)
    assert_frame_equal(data, read_data)

def test_write_read_json(tmpdir):
    details = {
        "filename": "test.json",
        "directory": str(tmpdir),
    }
    data = pd.DataFrame(fake.rows(30))
    write_json(data, details)
    read_data = read_json(details)
    assert_frame_equal(data, read_data)

def test_write_read_yaml(tmpdir):
    details = {
        "filename": "test.yaml",
        "directory": str(tmpdir),
    }
    data = pd.DataFrame(fake.rows(30))
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
    row = lambda: fake.to_bibtex(fake.bibliography_entry())
    bib_rows = fake.rows(200, row)

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
    read_data = read_bibtex(details)
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
    data = pd.DataFrame(fake.rows(30))
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
    data = pd.DataFrame(fake.rows(30))
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
    data = pd.DataFrame(fake.rows(30))
    for ind in data.index:
        data.at[ind, "sourceRoot"], data.at[ind, "sourceDirectory"] = extract_root_directory(str(tmpdir))
        data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
    data = data.sort_values(by="sourceFilename").reset_index(drop=True)
    write_markdown_directory(data, details)
    read_data = read_markdown_directory(details)
    assert_frame_equal(data, read_data)

# class TestUtils(unittest.TestCase):
#     def setUp(self):
#         self.sample_dict = {
#             'date': [datetime(2022, 1, 1), datetime(2022, 1, 2)],
#             'integer': [1, 2],
#             'string': ['test1', 'test2']
#         }
#         self.sample_df = pd.DataFrame(self.sample_dict)
#         self.directory_name = '.'
#         self.details = {
#             "directory": self.directory_name,
#             "header": 0,
#             }

#         self.json_file_name = 'test.json'
#         self.json_details = self.details.copy()
#         self.json_details["filename"] = self.json_file_name

#         self.yaml_file_name = 'test.yaml'
#         self.yaml_details = self.details.copy()
#         self.yaml_details["filename"] = self.yaml_file_name
        
#     @patch('ndlpy.access.io.read_json_file')
#     def test_read_json(self, mock_read_json_file):
#         full_filename = extract_full_filename(self.json_details)
#         mock_read_json_file.return_value = self.sample_dict
#         df = read_json(self.json_details)
#         mock_read_json_file.assert_called_once_with(full_filename)
#         assert_frame_equal(df, self.sample_df)

#     @patch('ndlpy.access.io.write_json_file')
#     def test_write_json(self, mock_write_json_file):
#         full_filename = extract_full_filename(self.json_details)
#         write_json(self.sample_df, self.json_details)
#         mock_write_json_file.assert_called_once_with(self.sample_df.to_dict("records"), full_filename, )

#     @patch('json.load')
#     @patch('builtins.open', new_callable=mock_open)
#     def test_read_json_file(self, mock_open, mock_json_load):
#         full_filename = extract_full_filename(self.json_details)
#         with open(full_filename, 'r') as f:
#             mock_json_load.return_value = self.sample_dict
#             d = read_json_file(full_filename)
#             mock_json_load.assert_called_once_with(f)
#             self.assertDictEqual(d, self.sample_dict)

#     @patch('json.dump')
#     @patch('builtins.open', new_callable=mock_open)
#     def test_write_json_file(self, mock_open, mock_json_dump):
#         full_filename = extract_full_filename(self.json_details)
#         with open(full_filename, 'w') as f:
#             write_json_file(self.sample_dict, self.json_details)
#             mock_json_dump.assert_called_once_with(self.sample_dict, f, sort_keys=False)
#     # Add similar tests for read_directory, write_directory, read_yaml_meta_file,
#     # write_yaml_meta_file, read_markdown_file, read_docx_file, write_markdown_file,
#     # create_letter, and write_letter_file here.

#     # The test for yaml_prep is a bit tricky, since it involves a complex transformation
#     # of the input data. It would be a good idea to split it into several smaller tests,
#     # each one verifying a different part of the transformation.

#     def test_write_read_yaml(self):
#         """access_tests: test the write to and read from a yaml file."""
#         filename = "test.yaml"
#         data = fake.row()
#         ndlpy.access.io.write_yaml_file(data, filename)
#         read_data = ndlpy.access.io.read_yaml_file(filename)
#         self.assertDictEqual(data,read_data)

#     def test_write_read_markdown(self):
#         """access_tests: test the write to and read from a yaml headed markdown file."""
#         filename = "test.markdown"
#         data = fake.row()
#         ndlpy.access.io.write_markdown_file(data, filename)
#         read_data = ndlpy.access.io.read_markdown_file(filename)
#         self.assertDictEqual(data, read_data)
        

#     def assert_frame_equal(self, df1, df2):
#         """Compare two data frames."""
#         #equals = df1.to_dict("records")==df2.to_dict("records")
#         #if not equals:
#         #    print(df1.compare(df2))
#         #result = df.compare(df2)
#         self.assertDictEqual(df1.to_dict(),df2.to_dict())
        
#     def test_write_read_csv(self):
#         """test_write_read_csv: test the write to and read from an csv file."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         details = {
#             "filename": "test.csv",
#             "directory": tmpDirectory.name,
#             "header": 0,
#             "delimiter": ",",
#             "quotechar": "\"",
#         }
#         data = pd.DataFrame(fake.rows(30))
#         ndlpy.access.io.write_csv(data, details)
#         read_data = ndlpy.access.io.read_csv(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()

#     def test_write_read_excel(self):
#         """test_write_read_excel: test the write to and read from an excel spreadsheet."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         details = {
#             "filename": "test.xlsx",
#             "directory": tmpDirectory.name,
#             "header": 0,
#             "sheet": "Sheet1",
#         }
#         data = pd.DataFrame(fake.rows(30))
#         ndlpy.access.write_excel(data, details)
#         read_data = ndlpy.access.read_excel(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()

#     def test_write_read_json(self):
#         """test_write_read_json: test the write to and read from an json file."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         details = {
#             "filename": "test.json",
#             "directory": tmpDirectory.name,
#         }
#         data = pd.DataFrame(fake.rows(30))
#         ndlpy.access.write_json(data, details)
#         read_data = ndlpy.access.read_json(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()

#     def test_write_read_yaml(self):
#         """test_write_read_yaml: test the write to and read from an yaml file."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         details = {
#             "filename": "test.yaml",
#             "directory": tmpDirectory.name,
#         }
#         data = pd.DataFrame(fake.rows(30))
#         ndlpy.access.write_yaml(data, details)
#         read_data = ndlpy.access.read_yaml(details)
#         self.assert_frame_equal(read_data, data)
#         tmpDirectory.cleanup()

#     def test_write_read_json_directory(self):
#         """test_write_read_json_directory: test the write to and read from an json directory."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         extension = ".json"
#         details = {
#             "directory": tmpDirectory.name,
#             "source": [
#                 {
#                     "filename": "sourceFilename",
#                     "directory": "sourceDirectory",
#                     "root": "sourceRoot",
#                     "glob": "*" + extension,
#                 },
#             ],
#         }
#         data = pd.DataFrame(fake.rows(30))
#         for ind in data.index:
#             data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
#             data.at[ind, "sourceDirectory"] = tmpDirectory.name
#             data.at[ind, "sourceRoot"] = "."
#         data = data.sort_values(by="sourceFilename").reset_index(drop=True)
#         ndlpy.access.write_json_directory(data, details)
#         read_data = ndlpy.access.read_json_directory(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()

#     def test_write_read_yaml_directory(self):
#         """test_write_read_yaml_directory: test the write to and read from an yaml directory."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         extension = ".yaml"
#         details = {
#             "directory": tmpDirectory.name,
#             "source": [
#                 {
#                     "filename": "sourceFilename",
#                     "directory": "sourceDirectory",
#                     "root": "sourceRoot",
#                     "glob": "*" + extension,
#                 },
#             ],
#         }
#         data = pd.DataFrame(fake.rows(30))
#         for ind in data.index:
#             data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
#             data.at[ind, "sourceDirectory"] = tmpDirectory.name
#             data.at[ind, "sourceRoot"] = "."
#         data = data.sort_values(by="sourceFilename").reset_index(drop=True)
#         ndlpy.access.write_yaml_directory(data, details)
#         read_data = ndlpy.access.read_yaml_directory(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()
        
#     def test_write_read_markdown_directory(self):
#         """test_write_read_markdown_directory: test the write to and read from an markdown directory."""
#         tmpDirectory = tempfile.TemporaryDirectory()
#         extension = ".md"
#         details = {
#             "directory": tmpDirectory.name,
#             "source": [
#                 {
#                     "filename": "sourceFilename",
#                     "directory": "sourceDirectory",
#                     "root": "sourceRoot",
#                     "glob": "*" + extension,
#                 },
#             ],
#         }
#         data = pd.DataFrame(fake.rows(30))
#         for ind in data.index:
#             data.at[ind, "sourceFilename"] = data.at[ind, "name"] + extension
#             data.at[ind, "sourceDirectory"] = tmpDirectory.name
#             data.at[ind, "sourceRoot"] = "."
#         data = data.sort_values(by="sourceFilename").reset_index(drop=True)
#         ndlpy.access.write_markdown_directory(data, details)
#         read_data = ndlpy.access.read_markdown_directory(details)
#         self.assert_frame_equal(data, read_data)
#         tmpDirectory.cleanup()
    
