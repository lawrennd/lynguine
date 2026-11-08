import json
import os
import pytest
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError
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


# --- CIP-0009 / CIP-0003 edge coverage ---------------------------------------


def _item(tmp_path, **extra):
    base = {
        "type": "yaml",
        "filename": "x.yml",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
    }
    base.update(extra)
    return base


def test_materialise_list_and_non_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: MockResponse(b"ok\n"),
    )
    nested = _item(tmp_path, remote={"type": "url", "url": "https://example.org/x.yml"})
    assert materialise([nested, "skip-me"]) == [
        materialise(nested),
        None,
    ]
    assert materialise("not-a-dict") is None


def test_materialise_remote_must_be_mapping(tmp_path):
    with pytest.raises(ValueError, match="must be a mapping"):
        materialise(_item(tmp_path, remote="https://example.org/x.yml"))


def test_materialise_url_requires_url_and_filename(tmp_path):
    with pytest.raises(ValueError, match="requires a string remote.url"):
        materialise(
            _item(tmp_path, remote={"type": "url", "url": None})
        )
    no_name = _item(tmp_path, remote={"type": "url", "url": "https://example.org/x.yml"})
    del no_name["filename"]
    with pytest.raises(ValueError, match='requires "filename"'):
        materialise(no_name)


def test_materialise_url_permission_denied(tmp_path):
    with pytest.raises(ValueError, match="Permission denied"):
        materialise(
            _item(
                tmp_path,
                remote={
                    "type": "url",
                    "url": "https://example.org/x.yml",
                    "license": "CC-BY",
                },
            ),
            prompt=lambda _m: False,
        )


def test_materialise_url_wraps_unexpected_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(ValueError, match="Failed remote.type \"url\""):
        materialise(
            _item(
                tmp_path,
                remote={"type": "url", "url": "https://example.org/x.yml"},
            ),
            prompt=lambda _m: True,
        )


def test_materialise_url_urlerror(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: (_ for _ in ()).throw(URLError("dns down")),
    )
    with pytest.raises(ValueError, match="URL error"):
        materialise(
            _item(
                tmp_path,
                remote={"type": "url", "url": "https://example.org/x.yml"},
            ),
            prompt=lambda _m: True,
        )


def test_materialise_url_writes_nested_path_with_progress(tmp_path, monkeypatch):
    """Cover parent makedirs + Content-Length progress path."""

    class SizedResponse(MockResponse):
        def info(self):
            return {"Content-Length": str(len(self.data))}

    class FakeBar:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def update(self, n):
            pass

    fake_tqdm = MagicMock()
    fake_tqdm.tqdm = FakeBar
    monkeypatch.setitem(__import__("sys").modules, "tqdm", fake_tqdm)
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: SizedResponse(b"abcdef"),
    )
    nested = tmp_path / "deep" / "cache"
    item = _item(
        tmp_path,
        filename="nested.yml",
        directory=str(nested),
        remote={"type": "url", "url": "https://example.org/nested.yml"},
    )
    path = materialise(item, prompt=lambda _m: True)
    assert open(path, "rb").read() == b"abcdef"


def test_materialise_github_permission_denied(tmp_path):
    with pytest.raises(ValueError, match="Permission denied"):
        materialise(
            _item(
                tmp_path,
                type="csv",
                filename="data.csv",
                directory=str(tmp_path / "repo"),
                remote={
                    "type": "github",
                    "url": "https://github.com/example/repo.git",
                    "license": "MIT",
                },
            ),
            prompt=lambda _m: False,
        )


def test_materialise_github_refresh_pull_error(tmp_path, monkeypatch):
    dest = tmp_path / "repo"
    dest.mkdir()
    (dest / ".git").mkdir()

    class BoomRepo:
        def __init__(self, path):
            self.git = MagicMock()
            self.git.pull.side_effect = Exception("network")

    monkeypatch.setattr("lynguine.access.download.git.Repo", BoomRepo)
    with pytest.raises(ValueError, match="Error pulling"):
        materialise(
            _item(
                tmp_path,
                type="csv",
                filename="data.csv",
                directory=str(dest),
                remote={
                    "type": "github",
                    "url": "https://github.com/example/repo.git",
                    "refresh": True,
                },
            ),
            prompt=lambda _m: True,
        )


def test_materialise_github_wraps_unexpected_clone_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lynguine.access.download.clone_or_pull_repo",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("weird")),
    )
    with pytest.raises(ValueError, match='Failed remote.type "github"'):
        materialise(
            _item(
                tmp_path,
                type="csv",
                filename="data.csv",
                directory=str(tmp_path / "repo"),
                remote={
                    "type": "github",
                    "url": "https://github.com/example/repo.git",
                },
            ),
            prompt=lambda _m: True,
        )


def test_materialise_github_embeds_credential_token(tmp_path, monkeypatch):
    cloned = []

    def fake_clone(url, path):
        cloned.append(url)
        os.makedirs(os.path.join(path, ".git"), exist_ok=True)

    monkeypatch.setattr(
        "lynguine.access.download.git.Repo.clone_from", fake_clone
    )
    mgr = MagicMock()
    mgr.get_credential.return_value = {"value": "tokensecret"}
    monkeypatch.setattr(
        "lynguine.security.credentials.get_credential_manager",
        lambda: mgr,
    )
    path = materialise(
        _item(
            tmp_path,
            type="csv",
            filename="data.csv",
            directory=str(tmp_path / "repo"),
            remote={
                "type": "github",
                "url": "https://github.com/example/repo.git",
                "credential": "gh_token",
            },
        ),
        prompt=lambda _m: True,
    )
    assert os.path.isdir(os.path.join(path, ".git"))
    assert cloned[0].startswith("https://tokensecret@github.com/")
    mgr.get_credential.assert_called_once_with("gh_token")


def test_materialise_github_rejects_blank_credential(tmp_path):
    with pytest.raises(ValueError, match="credential must be a non-empty"):
        materialise(
            _item(
                tmp_path,
                type="csv",
                filename="data.csv",
                directory=str(tmp_path / "repo"),
                remote={
                    "type": "github",
                    "url": "https://github.com/example/repo.git",
                    "credential": "   ",
                },
            ),
            prompt=lambda _m: True,
        )


def test_materialise_github_requires_directory(tmp_path):
    item = _item(
        tmp_path,
        type="csv",
        filename="data.csv",
        remote={
            "type": "github",
            "url": "https://github.com/example/repo.git",
        },
    )
    del item["directory"]
    with pytest.raises(ValueError, match='requires "directory"'):
        materialise(item, prompt=lambda _m: True)


def test_materialise_github_relative_directory_joins_base(tmp_path, monkeypatch):
    cloned = []

    def fake_clone(url, path):
        cloned.append(path)
        os.makedirs(os.path.join(path, ".git"), exist_ok=True)

    monkeypatch.setattr(
        "lynguine.access.download.git.Repo.clone_from", fake_clone
    )
    path = materialise(
        {
            "type": "csv",
            "filename": "data.csv",
            "directory": "rel-repo",
            "base_directory": str(tmp_path),
            "allowed_roots": [str(tmp_path)],
            "remote": {
                "type": "github",
                "url": "https://github.com/example/repo.git",
            },
        },
        prompt=lambda _m: True,
    )
    assert os.path.samefile(path, tmp_path / "rel-repo")
    assert cloned and os.path.basename(cloned[0]) == "rel-repo"


def test_materialise_github_credential_scalar_and_url_shapes(tmp_path, monkeypatch):
    from lynguine.access.download import (
        _credential_secret,
        _github_url_with_token,
    )

    mgr = MagicMock()
    mgr.get_credential.return_value = "raw-token"
    monkeypatch.setattr(
        "lynguine.security.credentials.get_credential_manager",
        lambda: mgr,
    )
    assert _credential_secret({"credential": "k"}) == "raw-token"
    assert _github_url_with_token("git@github.com:org/repo.git", "tok") == (
        "git@github.com:org/repo.git"
    )
    assert (
        _github_url_with_token("https://github.com:443/org/repo.git", "tok")
        == "https://tok@github.com:443/org/repo.git"
    )


def test_materialise_data_resources_rethrows_valueerror(tmp_path, monkeypatch):
    cat = tmp_path / "data_resources.json"
    cat.write_text(
        json.dumps(
            {
                "ok": {
                    "files": [["x.csv"]],
                    "urls": ["https://example.org/"],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "lynguine.access.download.download_url_to",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("HTTP error 404")),
    )
    with pytest.raises(ValueError, match="HTTP error 404"):
        materialise(
            {
                "type": "csv",
                "filename": "x.csv",
                "directory": str(tmp_path),
                "base_directory": str(tmp_path),
                "allowed_roots": [str(tmp_path)],
                "remote": {
                    "type": "data_resources",
                    "catalogue": str(cat),
                    "name": "ok",
                },
            },
            prompt=lambda _m: True,
        )


def test_authorize_remote_override_and_interactive_license(tmp_path):
    from lynguine.access.download import authorize_remote

    remote = {
        "details": "dataset notes",
        "citation": "Someone 2020",
        "license": "CC-BY",
    }
    iface = Interface(
        data={"overide_manual_authorize": True},
        directory=".",
        user_file="_lynguine.yml",
    )
    assert authorize_remote(remote, iface, label="demo") is True

    prompts = []

    def ask(msg):
        prompts.append(msg)
        return True

    assert (
        authorize_remote(
            remote,
            Interface(
                data={"overide_manual_authorize": False},
                directory=".",
                user_file="_lynguine.yml",
            ),
            label="demo",
            prompt=ask,
        )
        is True
    )
    assert prompts and "proceed" in prompts[0].lower()


def test_load_catalogue_datasets_list_and_relative_path(tmp_path):
    from lynguine.access.download import load_data_resources_catalogue

    cat_dir = tmp_path / "cats"
    cat_dir.mkdir()
    cat_path = cat_dir / "data_resources.json"
    cat_path.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "name": "bmi_steps",
                        "files": [["steps-bmi-data.csv"]],
                        "urls": ["https://example.org/bmi/"],
                    },
                    {"files": [["bad.csv"]]},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="need a name"):
        load_data_resources_catalogue(
            "cats/data_resources.json",
            item={
                "base_directory": str(tmp_path),
                "allowed_roots": [str(tmp_path)],
            },
        )
    cat_path.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "name": "bmi_steps",
                        "files": [["steps-bmi-data.csv"]],
                        "urls": ["https://example.org/bmi/"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    catalogue = load_data_resources_catalogue(
        "cats/data_resources.json",
        item={
            "base_directory": str(tmp_path),
            "allowed_roots": [str(tmp_path)],
        },
    )
    assert "bmi_steps" in catalogue
    assert "name" not in catalogue["bmi_steps"]


def test_load_catalogue_rejects_non_object_and_bad_path(tmp_path):
    from lynguine.access.download import load_data_resources_catalogue

    with pytest.raises(ValueError, match="requires string remote.catalogue"):
        load_data_resources_catalogue(None)
    bad = tmp_path / "list.json"
    bad.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_data_resources_catalogue(str(bad))


def test_materialise_data_resources_suffices_and_dirs(tmp_path, monkeypatch):
    calls = []

    def fake_urlopen(url):
        calls.append(url)
        return MockResponse(b"x")

    monkeypatch.setattr("lynguine.access.download.urlopen", fake_urlopen)

    cat = tmp_path / "data_resources.json"
    cat.write_text(
        json.dumps(
            {
                "with_suffix": {
                    "files": [["a.csv"]],
                    "urls": ["https://example.org/s/"],
                    "suffices": [["?dl=1"]],
                },
                "with_dirs": {
                    "files": [["b.csv"]],
                    "urls": ["https://example.org/d/"],
                    "dirs": [["subdir"]],
                },
            }
        ),
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    materialise(
        {
            "type": "csv",
            "directory": str(cache),
            "base_directory": str(tmp_path),
            "allowed_roots": [str(tmp_path)],
            "remote": {
                "type": "data_resources",
                "catalogue": str(cat),
                "name": "with_suffix",
            },
        },
        prompt=lambda _m: True,
    )
    assert any("?dl=1" in u for u in calls)
    assert (cache / "a.csv").exists()

    calls.clear()
    materialise(
        {
            "type": "csv",
            "directory": str(cache),
            "base_directory": str(tmp_path),
            "allowed_roots": [str(tmp_path)],
            "remote": {
                "type": "data_resources",
                "catalogue": str(cat),
                "name": "with_dirs",
            },
        },
        prompt=lambda _m: True,
    )
    assert (cache / "subdir" / "b.csv").exists()
    assert any("subdir/b.csv" in u for u in calls)


def test_materialise_data_resources_errors(tmp_path, monkeypatch):
    cat = tmp_path / "data_resources.json"
    cat.write_text(
        json.dumps(
            {
                "empty": {"files": [], "urls": []},
                "bad_entry": "not-a-mapping",
                "ok": {
                    "files": [["x.csv"]],
                    "urls": ["https://example.org/"],
                },
            }
        ),
        encoding="utf-8",
    )
    base = {
        "type": "csv",
        "directory": str(tmp_path),
        "base_directory": str(tmp_path),
        "allowed_roots": [str(tmp_path)],
    }
    with pytest.raises(ValueError, match="requires string remote.name"):
        materialise(
            {**base, "remote": {"type": "data_resources", "catalogue": str(cat)}},
            prompt=lambda _m: True,
        )
    with pytest.raises(ValueError, match="non-empty urls and files"):
        materialise(
            {
                **base,
                "remote": {
                    "type": "data_resources",
                    "catalogue": str(cat),
                    "name": "empty",
                },
            },
            prompt=lambda _m: True,
        )
    with pytest.raises(ValueError, match="must be a mapping"):
        materialise(
            {
                **base,
                "remote": {
                    "type": "data_resources",
                    "catalogue": str(cat),
                    "name": "bad_entry",
                },
            },
            prompt=lambda _m: True,
        )
    with pytest.raises(ValueError, match="Permission denied"):
        materialise(
            {
                **base,
                "filename": "x.csv",
                "remote": {
                    "type": "data_resources",
                    "catalogue": str(cat),
                    "name": "ok",
                    "license": "CC-BY",
                },
            },
            prompt=lambda _m: False,
        )

    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: (_ for _ in ()).throw(RuntimeError("fetch failed")),
    )
    with pytest.raises(ValueError, match="Failed data_resources fetch"):
        materialise(
            {
                **base,
                "filename": "x.csv",
                "remote": {
                    "type": "data_resources",
                    "catalogue": str(cat),
                    "name": "ok",
                },
            },
            prompt=lambda _m: True,
        )


def test_materialise_data_resources_returns_directory_without_filename(
    tmp_path, monkeypatch
):
    cat = tmp_path / "data_resources.json"
    cat.write_text(
        json.dumps(
            {
                "pack": {
                    "files": [["a.csv"]],
                    "urls": ["https://example.org/"],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: MockResponse(b"a"),
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    path = materialise(
        {
            "type": "csv",
            "directory": str(cache),
            "base_directory": str(tmp_path),
            "allowed_roots": [str(tmp_path)],
            "remote": {
                "type": "data_resources",
                "catalogue": str(cat),
                "name": "pack",
            },
        },
        prompt=lambda _m: True,
    )
    assert os.path.samefile(path, cache)
    assert (cache / "a.csv").exists()


def test_from_flow_pre_materialises_cache_before_input(tmp_path, monkeypatch):
    """Non-input remotes materialise before input (catalogue-first spine)."""
    import lynguine.config.interface
    import lynguine.assess.data
    import lynguine.access.download as download_mod

    order = []
    real_materialise = download_mod.materialise

    def tracking_materialise(item, interface=None, prompt=None):
        if isinstance(item, dict) and "filename" in item:
            order.append(item["filename"])
        return real_materialise(item, interface=interface, prompt=prompt)

    monkeypatch.setattr(download_mod, "materialise", tracking_materialise)
    monkeypatch.setattr(
        "lynguine.access.download.urlopen",
        lambda url: MockResponse(
            b"- Name: Ada\n  score: 1\n"
            if url.endswith("input.yml")
            else b"- Name: Meta\n  score: 0\n"
        ),
    )
    cache_dir = tmp_path / "cache"
    input_dir = tmp_path / "input"
    cache_dir.mkdir()
    input_dir.mkdir()
    interface = lynguine.config.interface.Interface(
        {
            "cache": {
                "type": "yaml",
                "filename": "meta.yml",
                "directory": str(cache_dir),
                "index": "Name",
                "remote": {
                    "type": "url",
                    "url": "https://example.org/meta.yml",
                },
            },
            "input": {
                "type": "yaml",
                "filename": "input.yml",
                "directory": str(input_dir),
                "index": "Name",
                "remote": {
                    "type": "url",
                    "url": "https://example.org/input.yml",
                },
            },
        },
        user_file="test.yml",
        directory=str(tmp_path),
    )
    cdf = lynguine.assess.data.CustomDataFrame.from_flow(interface)
    assert order[0] == "meta.yml"
    assert "input.yml" in order
    assert (cache_dir / "meta.yml").exists()
    assert (input_dir / "input.yml").exists()
    assert len(cdf) >= 1
