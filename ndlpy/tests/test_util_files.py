import pytest
import subprocess
from unittest.mock import mock_open, patch
from ndlpy.util.files import get_cvs_version, get_svn_version, get_git_version, read_txt_file, extract_file_details

def test_get_cvs_version_found():
    mock_file_content = "D/filename/1.1/\n"
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        with patch('os.path.exists', return_value=True):
            version = get_cvs_version("filename", "/path/to/filename")
            assert version == "1.1"

def test_get_cvs_version_not_found():
    with patch('os.path.exists', return_value=False):
        version = get_cvs_version("filename", "/path/to/filename")
        assert version == ""

def test_get_svn_version_found():
    mock_file_content = "filename\ntype\nentry2\nentry3\nentry4\nentry5\nlastUpdate\ncheckSum\nlastChange\nversion\nuserName\n"
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        with patch('os.path.exists', return_value=True):
            version = get_svn_version("filename", "/path/to/filename")
            assert version == {'type': 'type', 'textLastUpdate': 'lastUpdate', 'checkSum': 'checkSum', 'lastChange': 'lastChange', 'version': 'version', 'userName': 'userName'}

def test_get_svn_version_not_found():
    with patch('os.path.exists', return_value=False):
        version = get_svn_version("filename", "/path/to/filename")
        assert version == []       


def test_get_git_version_success():
    with patch('os.path.exists', return_value=True):
        with patch('subprocess.check_output', return_value=b'1234567890abcdef'):
            version = get_git_version("filename.txt", "/path/to/filename.txt", "/path/to/git_repo")
            assert version == "1234567890abcdef"

def test_get_git_version_file_not_exist():
    with patch('os.path.exists', return_value=False):
        version = get_git_version("filename.txt", "/path/to/filename.txt", "/path/to/git_repo")
        assert version == ""

def test_get_git_version_command_fails():
    with patch('os.path.exists', return_value=True):
        with patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(1, ['git'])):
            version = get_git_version("filename.txt", "/path/to/filename.txt", "/path/to/git_repo")
            assert version == ""


def test_read_txt_file_success(tmpdir):
    file_content = "# Comment\nLine 1\n# Comment 2\nLine 2\n"
    p = tmpdir.join("example.txt")
    p.write(file_content)
    result = read_txt_file(p.basename, str(tmpdir))
    assert result == "Line 1\nLine 2\n"

def test_read_txt_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_txt_file("nonexistent.txt", "/path/to")


def test_extract_file_details_success(tmpdir):
    file_content = "# Comment\nValue1,Value2,Value3\n\nValue4,Value5,Value6"
    p = tmpdir.join("example.csv")
    p.write(file_content)
    result = extract_file_details(p.basename, str(tmpdir))
    assert result == [["Value1", "Value2", "Value3"], ["Value4", "Value5", "Value6"]]

def test_extract_file_details_not_found():
    with pytest.raises(FileNotFoundError):
        extract_file_details("nonexistent.csv", "/path/to")
