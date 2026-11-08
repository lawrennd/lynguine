import json
import os
import pytest
from unittest.mock import MagicMock
from urllib.error import HTTPError
from lynguine.access.download import FileDownloader, GitDownloader, Interface

class MockResponse:
    def __init__(self, data):
        self.data = data

    def read(self, n=-1):
        if n is None or n < 0:
            out, self.data = self.data, b""
            return out
        out, self.data = self.data[:n], self.data[n:]
        return out

    def info(self):
        return {}

    
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
        },
        directory=".",
        user_file="_linguine.yml",
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

    # Patch the imported urlopen in the download module, not urllib.request
    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    
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

    assert "Error cloning" in str(excinfo.value)
    assert "repository" in str(excinfo.value)


# --- CIP-0009 materialise(remote:) -------------------------------------------

from lynguine.access.download import materialise, SUPPORTED_REMOTE_TYPES


def test_materialise_noop_without_remote(tmp_path):
    item = {
        "type": "yaml",
        "filename": "local.yml",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
    }
    assert materialise(item) is None


def test_materialise_rejects_legacy_source_remote_shape(tmp_path):
    item = {
        "type": "yaml",
        "filename": "x.yml",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "source": {"type": "url", "url": "https://example.org/x.yml"},
    }
    with pytest.raises(ValueError, match='uses key "remote:"'):
        materialise(item)


def test_materialise_unknown_type(tmp_path):
    item = {
        "type": "yaml",
        "filename": "x.yml",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {"type": "s3", "url": "s3://bucket/x"},
    }
    with pytest.raises(ValueError, match="Unknown remote.type"):
        materialise(item)
    assert "url" in SUPPORTED_REMOTE_TYPES
    assert "github" in SUPPORTED_REMOTE_TYPES


def test_materialise_url_downloads_when_missing(tmp_path, monkeypatch):
    dest_dir = tmp_path / "cache"
    dest_dir.mkdir()
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"name: Ada\n")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "yaml",
        "filename": "candidates.yml",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "url",
            "url": "https://example.org/candidates.yml",
        },
    }
    path = materialise(item)
    assert path.endswith("candidates.yml")
    assert os.path.exists(path)
    assert open(path, "rb").read() == b"name: Ada\n"
    assert calls == ["https://example.org/candidates.yml"]


def test_materialise_url_skips_when_cached(tmp_path, monkeypatch):
    dest_dir = tmp_path / "cache"
    dest_dir.mkdir()
    cached = dest_dir / "candidates.yml"
    cached.write_text("cached: true\n")
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"fresh\n")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "yaml",
        "filename": "candidates.yml",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "url",
            "url": "https://example.org/candidates.yml",
            "refresh": False,
        },
    }
    path = materialise(item)
    assert path == str(cached.resolve()) or os.path.samefile(path, cached)
    assert calls == []
    assert cached.read_text() == "cached: true\n"


def test_materialise_url_refresh_redownloads(tmp_path, monkeypatch):
    dest_dir = tmp_path / "cache"
    dest_dir.mkdir()
    cached = dest_dir / "candidates.yml"
    cached.write_text("old\n")
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"new\n")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "yaml",
        "filename": "candidates.yml",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "url",
            "url": "https://example.org/candidates.yml",
            "refresh": True,
        },
    }
    path = materialise(item)
    assert open(path, "rb").read() == b"new\n"
    assert calls == ["https://example.org/candidates.yml"]


def test_materialise_url_http_error(tmp_path, monkeypatch):
    dest_dir = tmp_path / "cache"
    dest_dir.mkdir()

    def fake_urlopen(url):
        raise HTTPError(url, 404, "Not Found", None, None)

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "yaml",
        "filename": "missing.yml",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "url",
            "url": "https://example.org/missing.yml",
        },
    }
    with pytest.raises(ValueError, match='remote.type "url"'):
        materialise(item)


def test_materialise_github_clones(tmp_path, monkeypatch):
    dest_dir = tmp_path / "repo"
    cloned = []

    def fake_clone(url, path):
        cloned.append((url, path))
        os.makedirs(os.path.join(path, ".git"), exist_ok=True)

    monkeypatch.setattr("lynguine.access.download.git.Repo.clone_from", fake_clone)
    item = {
        "type": "csv",
        "filename": "data/candidates.csv",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "github",
            "url": "https://github.com/example/allocations.git",
        },
    }
    path = materialise(item)
    assert os.path.isdir(os.path.join(path, ".git"))
    assert cloned[0][0] == "https://github.com/example/allocations.git"


def test_materialise_github_skips_when_cloned(tmp_path, monkeypatch):
    dest_dir = tmp_path / "repo"
    dest_dir.mkdir()
    (dest_dir / ".git").mkdir()
    calls = []

    def boom(*a, **k):
        calls.append(True)
        raise AssertionError("should not clone or pull")

    monkeypatch.setattr("lynguine.access.download.git.Repo.clone_from", boom)
    monkeypatch.setattr("lynguine.access.download.git.Repo", boom)
    item = {
        "type": "csv",
        "filename": "data/candidates.csv",
        "directory": str(dest_dir),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "github",
            "url": "https://github.com/example/allocations.git",
            "refresh": False,
        },
    }
    path = materialise(item)
    assert os.path.samefile(path, dest_dir)
    assert calls == []


def test_materialise_does_not_infer_url_from_filename(tmp_path, monkeypatch):
    """Filename that looks like a URL must not trigger a fetch (no remote:)."""
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"x")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "yaml",
        "filename": "https://example.org/looks-like-url.yml",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
    }
    assert materialise(item) is None
    assert calls == []


def test_from_flow_materialises_remote_url(tmp_path, monkeypatch):
    import lynguine.config.interface
    import lynguine.assess.data

    cache = tmp_path / "cache"
    cache.mkdir()
    yaml_body = "- Name: Ada\n  score: 1\n"

    def fake_urlopen(url):
        return MockResponse(yaml_body.encode("utf-8"))

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    interface = lynguine.config.interface.Interface(
        {
            "input": {
                "type": "yaml",
                "filename": "candidates.yml",
                "directory": str(cache),
                "index": "Name",
                "remote": {
                    "type": "url",
                    "url": "https://example.org/candidates.yml",
                },
            },
        },
        user_file="test.yml",
        directory=str(tmp_path),
    )
    cdf = lynguine.assess.data.CustomDataFrame.from_flow(interface)
    assert "Ada" in list(cdf.index) or cdf.index[0] == "Ada"
    assert (cache / "candidates.yml").exists()


def test_from_flow_remote_coexists_with_directory_source(tmp_path, monkeypatch):
    """CIP-000F source: lists remain usable; remote: is orthogonal."""
    import lynguine.config.interface
    import lynguine.assess.data

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "nested").mkdir()
    # Pretend github materialise already filled the tree; skip network.
    (repo / ".git").mkdir()
    (repo / "nested" / "row.yml").write_text("Name: Ada\nscore: 2\n")

    def boom(*a, **k):
        raise AssertionError("should not hit network")

    monkeypatch.setattr("lynguine.access.download.urlopen", boom)
    monkeypatch.setattr("lynguine.access.download.git.Repo.clone_from", boom)

    interface = lynguine.config.interface.Interface(
        {
            "input": {
                "type": "yaml_directory",
                "directory": str(repo),
                "index": "Name",
                "remote": {
                    "type": "github",
                    "url": "https://github.com/example/allocations.git",
                    "refresh": False,
                },
                "source": [
                    {
                        "directory": ".",
                        "glob": "**/*.yml",
                        "recursive": True,
                    }
                ],
            },
        },
        user_file="test.yml",
        directory=str(tmp_path),
    )
    cdf = lynguine.assess.data.CustomDataFrame.from_flow(interface)
    assert len(cdf) >= 1


# --- ods CIP-0003 data_resources catalogue expand ----------------------------


def test_materialise_data_resources_downloads_named_entry(tmp_path, monkeypatch):
    cat_dir = tmp_path / "catalogue"
    cat_dir.mkdir()
    catalogue = {
        "bmi_steps": {
            "details": "BMI vs steps",
            "citation": "Yanai & Lercher",
            "license": None,
            "files": [["steps-bmi-data.csv"]],
            "urls": ["https://example.org/bmi_steps/"],
        }
    }
    cat_path = cat_dir / "data_resources.json"
    cat_path.write_text(json.dumps(catalogue), encoding="utf-8")

    cache = tmp_path / "bmi_steps"
    cache.mkdir()
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"gender,steps,bmi\nF,1000,22\n")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "csv",
        "filename": "steps-bmi-data.csv",
        "directory": str(cache),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "data_resources",
            "catalogue": str(cat_path),
            "name": "bmi_steps",
        },
    }
    path = materialise(item, prompt=lambda _m: True)
    assert path.endswith("steps-bmi-data.csv")
    assert os.path.exists(path)
    assert calls == ["https://example.org/bmi_steps/steps-bmi-data.csv"]
    assert "data_resources" in SUPPORTED_REMOTE_TYPES


def test_materialise_data_resources_skips_when_cached(tmp_path, monkeypatch):
    cat_dir = tmp_path / "catalogue"
    cat_dir.mkdir()
    cat_path = cat_dir / "data_resources.json"
    cat_path.write_text(
        json.dumps(
            {
                "bmi_steps": {
                    "files": [["steps-bmi-data.csv"]],
                    "urls": ["https://example.org/bmi_steps/"],
                }
            }
        ),
        encoding="utf-8",
    )
    cache = tmp_path / "bmi_steps"
    cache.mkdir()
    cached = cache / "steps-bmi-data.csv"
    cached.write_text("gender,steps,bmi\nF,1,20\n", encoding="utf-8")
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"fresh\n")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)
    item = {
        "type": "csv",
        "filename": "steps-bmi-data.csv",
        "directory": str(cache),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "data_resources",
            "catalogue": str(cat_path),
            "name": "bmi_steps",
        },
    }
    path = materialise(item, prompt=lambda _m: True)
    assert os.path.samefile(path, cached)
    assert calls == []


def test_materialise_data_resources_requires_local_catalogue(tmp_path):
    item = {
        "type": "csv",
        "filename": "x.csv",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "data_resources",
            "catalogue": str(tmp_path / "missing.json"),
            "name": "bmi_steps",
        },
    }
    with pytest.raises(ValueError, match="catalogue not found"):
        materialise(item)


def test_materialise_data_resources_unknown_name(tmp_path):
    cat_path = tmp_path / "data_resources.json"
    cat_path.write_text(json.dumps({"other": {"files": [["a"]], "urls": ["https://x/"]}}))
    item = {
        "type": "csv",
        "filename": "x.csv",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
        "remote": {
            "type": "data_resources",
            "catalogue": str(cat_path),
            "name": "bmi_steps",
        },
    }
    with pytest.raises(ValueError, match='Dataset "bmi_steps" not found'):
        materialise(item)
