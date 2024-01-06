import pytest
import os
import pytest
from unittest.mock import MagicMock
from ndlpy.access.download import FileDownloader, GitDownloader, Interface

class MockResponse:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    # Add any other necessary methods/attributes here

    
def mock_urlopen(url):
    if url == "http://example.com/file1/file1.txt":
        return MockResponse(b"response for file1")
    elif url == "http://example.com/file2/file2.txt":
        return MockResponse(b"response for file2")
    else:
        return MockResponse(b"default response")

@pytest.fixture
def monkeypatch_mock_urlopen(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

@pytest.fixture
def sample_settings(tmpdir):
    return Interface(
        data={
            "default_cache_path" : tmpdir,
            "overide_manual_authorize" : False,
        }
    )

@pytest.fixture
def sample_data_resources():
    return {
        "dataset1": {
            "urls": ["http://example.com/file1", "http://example.com/file2"],
            "files": ["file1.txt", "file2.txt"],
            "details": "Sample dataset details",
            "citation": "Sample citation",
            "size": 1024,
            "license": "Sample License"
        }
        # Add more datasets as needed
    }

@pytest.fixture
def file_downloader(sample_settings, sample_data_resources):
    return FileDownloader(sample_settings, sample_data_resources, "dataset1")

# Test for initialization and dataset setting
def test_initialization(file_downloader):
    assert file_downloader.data_name == "dataset1"
    file_downloader.data_name = "dataset2"
    assert file_downloader.data_name == "dataset2"

# Test for authorization logic
def test_authorization(file_downloader):
    # Mocking the prompt function to always return True
    assert file_downloader._authorize_download(prompt=lambda x: True) == True
    # Add more tests for different scenarios, including negative tests

# Test for download process logic
def test_download_process(monkeypatch, file_downloader, sample_data_resources):
    # Monkeypatch the _download_with_suffix, _download_with_dirs, and _download_simple methods
    # to track their calls and verify the correct method is called based on dataset configuration.
    called_methods = []

    def fake_download_suffices():
        called_methods.append('_download_suffices')

    def fake_download_dirs():
        called_methods.append('_download_dirs')

    def fake_download_simple():
        called_methods.append('_download_simple')

    monkeypatch.setattr(file_downloader, '_download_suffices', fake_download_suffices)
    monkeypatch.setattr(file_downloader, '_download_dirs', fake_download_dirs)
    monkeypatch.setattr(file_downloader, '_download_simple', fake_download_simple)

    # Simulate different dataset configurations
    file_downloader._process_data()
    assert '_download_suffices' in called_methods or '_download_dirs' in called_methods or '_download_simple' in called_methods

 # Test for download file logic
def test_download_file(file_downloader, monkeypatch):
    # Mocking the _download_url method to track its call
    called_methods = []

    def fake_download_url(url, dir_name=".", save_name=None, store_directory=None, messages=True, suffix=""):
        called_methods.append('_download_url')

    monkeypatch.setattr(file_downloader, '_download_url', fake_download_url)

    # Assuming dataset1 has a simple URL structure
    file_downloader._download_file("http://example.com", "file1.txt")
    assert '_download_url' in called_methods

# Test for handling missing dataset
def test_missing_dataset(file_downloader, monkeypatch):

    # Function to replace 'input' that always returns 'y'
    def mock_input(prompt=""):
        return "y"

    # Apply the monkeypatch for 'input' to use 'mock_input' instead
    monkeypatch.setattr("builtins.input", mock_input)
    with pytest.raises(ValueError):
        file_downloader.data_name = "unknown_dataset"
        file_downloader.download_data()

# Test for handling invalid dataset configurations
def test_invalid_dataset_config(file_downloader, sample_data_resources, monkeypatch):
    file_downloader.data_name = "dataset1"
    sample_data_resources["dataset1"]["urls"] = None  # Invalidate URL configuration

    # Function to replace 'input' that always returns 'y'
    def mock_input(prompt=""):
        return "y"

    # Apply the monkeypatch for 'input' to use 'mock_input' instead
    monkeypatch.setattr("builtins.input", mock_input)
    
    with pytest.raises(TypeError):
        file_downloader.download_data()

# Test for download_data with different dataset configurations
@pytest.mark.parametrize("config_key", ["suffices", "dirs", "simple"])
def test_download_data_varied_config(monkeypatch, file_downloader, sample_data_resources, config_key):
    
    called_methods = []
    def fake_method():
        called_methods.append(config_key)

    monkeypatch_methods = {
        "suffices": fake_method,
        "dirs": fake_method,
        "simple": fake_method
    }

    monkeypatch.setattr(file_downloader, f"_download_{config_key}", monkeypatch_methods[config_key])
    # Adjust the dataset configuration based on parametrized key
    if config_key == "simple":
        if "suffices" in sample_data_resources["dataset1"]:
            del sample_data_resources["dataset1"]["suffices"]
        if "dirs" in sample_data_resources["dataset1"]:
            del sample_data_resources["dataset1"]["dirs"]
    else:
        sample_data_resources["dataset1"][config_key] = True

    file_downloader._process_data()
    assert config_key in called_methods

# Test for handling network errors in _download_url
def test_network_errors_in_download_url(file_downloader, monkeypatch):
    def fake_urlopen(url):
        raise HTTPError(url, 404, "Not Found", None, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    
    with pytest.raises(ValueError):
        file_downloader._download_url("http://invalidurl.com", ".", "testfile.txt")



# Test case when the repo does not exist and needs to be cloned
def test_clone_repo(tmpdir, sample_settings, sample_data_resources, mocker):
    # Mock os.path.exists to simulate the repo does not exist
    mocker.patch('os.path.exists', return_value=False)
    # Mock os.makedirs to avoid actual directory creation
    mocker.patch('os.makedirs')
    # Mock git.Repo.clone_from
    mock_clone_from = mocker.patch('git.Repo.clone_from')

    data_name = "dataset1"
    git_url = "https://github.com/user/repo.git"

    downloader = GitDownloader(sample_settings, sample_data_resources, data_name, git_url)
    downloader._clone_or_pull_repo()

    mock_clone_from.assert_called_once_with(git_url, str(tmpdir))

# Test case when the repo exists and needs to pull updates
def test_pull_repo(tmpdir, sample_settings, sample_data_resources, mocker):
    # Mock os.path.exists and os.path.isdir to simulate the repo exists
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    # Mock git.Repo to simulate pulling from an existing repo
    mock_repo = MagicMock()
    mocker.patch('git.Repo', return_value=mock_repo)

    data_name = "dataset1"
    git_url = "https://github.com/user/repo.git"

    downloader = GitDownloader(sample_settings, sample_data_resources, data_name, git_url)
    downloader._clone_or_pull_repo()

    mock_repo.git.pull.assert_called_once()

# Test case for handling exceptions during cloning
def test_clone_repo_exception(sample_settings, sample_data_resources, mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.makedirs')
    mocker.patch('git.Repo.clone_from', side_effect=Exception("Clone failed"))

    data_name = "dataset1"
    git_url = "https://github.com/user/repo.git"

    downloader = GitDownloader(sample_settings, sample_data_resources, data_name, git_url)
    
    with pytest.raises(ValueError) as excinfo:
        downloader._clone_or_pull_repo()

    assert "Error cloning repository" in str(excinfo.value)
