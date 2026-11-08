import json
import os
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import git

from lynguine.util.misc import prompt_stdin, extract_full_filename
from lynguine.access.paths import confine_configured_path
from ..log import Logger
from ..config.context import Context

from ..config.interface import Interface

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

# CIP-0009 file-producing remotes; data_resources is ods CIP-0003 catalogue expand.
SUPPORTED_REMOTE_TYPES = frozenset({"url", "github", "data_resources"})


def _interface_flag(interface, key, default=False):
    """Read a boolean flag from an Interface or mapping."""
    if interface is None:
        return default
    try:
        return bool(interface[key])
    except (KeyError, TypeError, ValueError):
        # Interface.__getitem__ raises ValueError for missing keys.
        return default


def _resolve_item_directory(item):
    """Resolve and confine the local directory for an access item."""
    if "directory" not in item or item["directory"] is None:
        raise ValueError(
            'remote: materialise requires "directory" on the data item '
            "(local cache root)."
        )
    directory = os.path.expandvars(item["directory"])
    if not os.path.isabs(directory) and "base_directory" in item:
        directory = os.path.join(item["base_directory"], directory)
    return confine_configured_path(directory, item)


def _legacy_remote_source(source):
    """True if ``source`` looks like the pre-accept CIP-0009 remote mapping."""
    return isinstance(source, dict) and source.get("type") in {"url", "github"}


def load_data_resources_catalogue(catalogue_path, item=None):
    """Load a pods-style data-resources catalogue from a local JSON path.

    Accepts either a dict keyed by dataset name (``data_resources.json``) or
    a mapping with a top-level ``datasets`` list of entries that each include
    ``name``.
    """
    if not catalogue_path or not isinstance(catalogue_path, str):
        raise ValueError(
            'remote.type "data_resources" requires string remote.catalogue '
            "(local path to data_resources.json)"
        )
    path = os.path.expandvars(os.path.expanduser(catalogue_path))
    if not os.path.isabs(path) and isinstance(item, dict) and item.get(
        "base_directory"
    ):
        path = os.path.join(item["base_directory"], path)
    if isinstance(item, dict) and (
        "allowed_roots" in item or "base_directory" in item
    ):
        # Confine the catalogue file path the same way as other access paths.
        path_item = dict(item)
        path_item["directory"] = os.path.dirname(path) or "."
        path_item["filename"] = os.path.basename(path)
        path = extract_full_filename(path_item)
    if not os.path.isfile(path):
        raise ValueError(
            f'remote.type "data_resources" catalogue not found at "{path}". '
            "Materialise the catalogue first (remote.type: url)."
        )
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict) and "datasets" in raw and isinstance(
        raw["datasets"], list
    ):
        catalogue = {}
        for entry in raw["datasets"]:
            if not isinstance(entry, dict) or "name" not in entry:
                raise ValueError(
                    f'Catalogue "{path}" datasets list entries need a name'
                )
            name = entry["name"]
            catalogue[name] = {k: v for k, v in entry.items() if k != "name"}
        return catalogue
    if isinstance(raw, dict):
        return raw
    raise ValueError(
        f'Catalogue "{path}" must be a JSON object keyed by dataset name'
    )


def _dataset_file_jobs(entry):
    """Yield ``(url, relative_path)`` jobs from a catalogue entry (pods layout)."""
    urls = entry.get("urls") or []
    files = entry.get("files") or []
    if not urls or not files:
        raise ValueError(
            "data_resources entry requires non-empty urls and files lists"
        )
    if "suffices" in entry:
        for url, filenames, suffices in zip(urls, files, entry["suffices"]):
            for filename, suffix in zip(filenames, suffices):
                yield urljoin(url, filename), filename, suffix
    elif "dirs" in entry:
        for url, dirnames, filenames in zip(urls, entry["dirs"], files):
            for filename, dirname in zip(filenames, dirnames):
                rel = os.path.join(dirname, filename) if dirname not in (".", "") else filename
                file_url = urljoin(url, f"{dirname.rstrip('/')}/{filename}" if dirname not in (".", "") else filename)
                yield file_url, rel, ""
    else:
        for url, filenames in zip(urls, files):
            for filename in filenames:
                yield urljoin(url, filename), filename, ""


def materialise_data_resources(item, remote, interface=None, prompt=None):
    """Expand a named pods catalogue entry into cached files (ods CIP-0003)."""
    name = remote.get("name")
    if not name or not isinstance(name, str):
        raise ValueError(
            'remote.type "data_resources" requires string remote.name '
            "(dataset key in the catalogue)"
        )
    catalogue = load_data_resources_catalogue(
        remote.get("catalogue"), item=item
    )
    if name not in catalogue:
        raise ValueError(
            f'Dataset "{name}" not found in catalogue '
            f'"{remote.get("catalogue")}"'
        )
    entry = catalogue[name]
    if not isinstance(entry, dict):
        raise ValueError(f'Catalogue entry "{name}" must be a mapping')

    dest_root = _resolve_item_directory(item)
    refresh = bool(remote.get("refresh", False))

    auth_remote = {
        "details": remote.get("details", entry.get("details")),
        "citation": remote.get("citation", entry.get("citation")),
        "license": remote.get("license", entry.get("license")),
    }
    jobs = list(_dataset_file_jobs(entry))
    missing_or_refresh = [
        (url, rel, suffix)
        for url, rel, suffix in jobs
        if refresh or not os.path.exists(os.path.join(dest_root, rel))
    ]
    if not missing_or_refresh:
        log.debug(
            f'Skipping data_resources "{name}"; all files present under "{dest_root}"'
        )
    else:
        if not authorize_remote(
            auth_remote, interface, label=name, prompt=prompt
        ):
            raise ValueError(
                f'Permission denied for remote.type "data_resources" name "{name}"'
            )
        for url, rel, suffix in missing_or_refresh:
            dest = os.path.join(dest_root, rel)
            try:
                download_url_to(url, dest, suffix=suffix)
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(
                    f'Failed data_resources fetch for "{name}" file "{rel}" '
                    f"from {url}: {e}"
                ) from e

    if "filename" in item and item["filename"] is not None:
        return extract_full_filename(item)
    return dest_root


def authorize_remote(remote, interface=None, *, label="remote", prompt=None):
    """Prompt for licence acknowledgement before a remote materialise.

    Honours ``overide_manual_authorize`` on the interface for
    non-interactive runs (CIP-0009).
    """
    if prompt is None:
        prompt = prompt_stdin

    details = remote.get("details")
    if details:
        print(f"Acquiring resource: {label}\n")
        print("Details of data: ")
        print(details)
    if remote.get("citation"):
        print("\nPlease cite:\n" + remote["citation"])

    if _interface_flag(interface, "overide_manual_authorize", default=False):
        if remote.get("license"):
            print(
                "You have agreed to the following license:\n" + remote["license"]
            )
        return True

    if remote.get("license"):
        print(
            "You must also agree to the following license:\n" + remote["license"]
        )
        return prompt("Do you wish to proceed with the download? [yes/no] ")
    # No licence text and interactive mode: still confirm once.
    if details or remote.get("citation"):
        return prompt("Do you wish to proceed with the download? [yes/no] ")
    return True


def _save_response_to_file(response, save_path):
    """Write an HTTP response body to ``save_path`` (optional progress bar)."""
    try:
        file_size = int(response.info().get("Content-Length"))
    except (TypeError, ValueError):
        file_size = None

    parent = os.path.dirname(save_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

    with open(save_path, "wb") as f:
        if file_size:
            from tqdm import tqdm

            with tqdm(total=file_size, unit="B", unit_scale=True) as bar:
                for buff in iter(lambda: response.read(1024), b""):
                    f.write(buff)
                    bar.update(len(buff))
        else:
            f.write(response.read())


def download_url_to(url, save_path, *, suffix=""):
    """HTTP(S) GET ``url`` and write the body to ``save_path``."""
    try:
        response = urlopen(url + suffix)
    except HTTPError as e:
        raise ValueError(
            f'HTTP error {e.code} when accessing remote.type "url" at {url}'
        ) from e
    except URLError as e:
        raise ValueError(
            f'URL error {e.reason} when accessing remote.type "url" at {url}'
        ) from e
    _save_response_to_file(response, save_path)
    return save_path


def clone_or_pull_repo(git_url, repo_path):
    """Clone ``git_url`` into ``repo_path``, or pull if a ``.git`` dir exists."""
    if not os.path.exists(repo_path):
        os.makedirs(repo_path)

    git_dir = os.path.join(repo_path, ".git")
    if os.path.isdir(git_dir):
        try:
            repo = git.Repo(repo_path)
            repo.git.pull()
        except Exception as e:
            raise ValueError(
                f'Error pulling remote.type "github" repository at {git_url}: {e}'
            ) from e
    else:
        try:
            git.Repo.clone_from(git_url, repo_path)
        except Exception as e:
            raise ValueError(
                f'Error cloning remote.type "github" repository at {git_url}: {e}'
            ) from e
    return repo_path


def _credential_secret(remote):
    """Resolve optional ``remote.credential`` via CIP-0005 (no logging of values)."""
    key = remote.get("credential")
    if not key:
        return None
    if not isinstance(key, str) or not key.strip():
        raise ValueError('remote.credential must be a non-empty credential key name')
    from ..security.credentials import get_credential_manager

    credential = get_credential_manager().get_credential(key.strip())
    if isinstance(credential, dict) and "value" in credential:
        return credential["value"]
    return credential


def _github_url_with_token(url, secret):
    """Embed a token in an https Git URL without returning it to callers' logs."""
    if not secret:
        return url
    token = secret if isinstance(secret, str) else str(secret)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return url
    # netloc may already include userinfo; replace with token as username.
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    netloc = f"{token}@{host}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


def materialise(item, interface=None, prompt=None):
    """Materialise a ``remote:`` artefact before the local ``type:`` read.

    When ``item`` has no ``remote`` key, returns ``None`` (no-op), unless
    ``source`` is a legacy remote mapping (``type: url|github``), which
    raises a migration error pointing at ``remote:``.

    :param item: Access-stage data item (may be a list of items).
    :param interface: Optional Interface for authorize overrides.
    :param prompt: Optional yes/no prompt callable.
    :return: Local path materialised or confirmed, a list of paths for
        list items, or ``None`` when there is nothing to materialise.
    """
    if isinstance(item, list):
        return [materialise(entry, interface, prompt) for entry in item]

    if not isinstance(item, dict):
        return None

    if "remote" not in item:
        if "source" in item and _legacy_remote_source(item["source"]):
            raise ValueError(
                'Remote materialise uses key "remote:", not "source:". '
                "Directory discovery keeps source: lists (CIP-000F). "
                "Rename this block to remote: {type: url|github, url: ...}."
            )
        return None

    remote = item["remote"]
    if not isinstance(remote, dict):
        raise ValueError(
            'remote: must be a mapping with "type" '
            f"(got {type(remote).__name__})"
        )

    rtype = remote.get("type")
    if rtype not in SUPPORTED_REMOTE_TYPES:
        raise ValueError(
            f'Unknown remote.type "{rtype}". '
            f"Supported: {', '.join(sorted(SUPPORTED_REMOTE_TYPES))}."
        )

    if rtype == "data_resources":
        return materialise_data_resources(
            item, remote, interface=interface, prompt=prompt
        )

    url = remote.get("url")
    if not url or not isinstance(url, str):
        raise ValueError(f'remote.type "{rtype}" requires a string remote.url')

    refresh = bool(remote.get("refresh", False))
    secret = _credential_secret(remote)

    if rtype == "url":
        if "filename" not in item or item["filename"] is None:
            raise ValueError(
                'remote.type "url" requires "filename" on the data item'
            )
        dest = extract_full_filename(item)
        if os.path.exists(dest) and not refresh:
            log.debug(f'Skipping remote url fetch; cache present at "{dest}"')
            return dest
        if not authorize_remote(remote, interface, label=url, prompt=prompt):
            raise ValueError(
                f'Permission denied for remote.type "url" at {url}'
            )
        try:
            download_url_to(url, dest)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f'Failed remote.type "url" fetch for {url}: {e}'
            ) from e
        return dest

    # github
    repo_path = _resolve_item_directory(item)
    git_dir = os.path.join(repo_path, ".git")
    if os.path.isdir(git_dir) and not refresh:
        log.debug(
            f'Skipping remote github fetch; clone present at "{repo_path}"'
        )
        return repo_path
    if not authorize_remote(remote, interface, label=url, prompt=prompt):
        raise ValueError(
            f'Permission denied for remote.type "github" at {url}'
        )
    fetch_url = _github_url_with_token(url, secret)
    try:
        clone_or_pull_repo(fetch_url, repo_path)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f'Failed remote.type "github" fetch for {url}: {e}'
        ) from e
    return repo_path


class FileDownloader:
    """
    A class for downloading data files from a url.
    """

    def __init__(self, interface, data_resources, data_name):
        """
        Initialize the FileDownloader class.
        :param data_resources: The data resources dictionary.
        :param data_name: The name of the data to download.
        """
        self.interface = interface
        self.data_resources = data_resources
        self.data_name = data_name
        if self.data_name not in self.data_resources:
            raise ValueError(f'Data "{self.data_name}" not found.')
        self._dr = self.data_resources[self.data_name]

    @property
    def interface(self):
        """
        Return the interface object.
        :return: The interface object.
        """
        return self._interface

    @interface.setter
    def interface(self, value):
        """
        Set the interface object.
        :param value: The interface object.
        :return: None
        """
        if not isinstance(value, Interface):
            raise TypeError("interface must be of type Interface.")
        self._interface = value

    @property
    def data_name(self):
        """
        Return the name of the data to download.
        :return: The name of the data to download.
        """
        return self._data_name

    @data_name.setter
    def data_name(self, value):
        """
        Set the name of the data to download.
        :param value: The name of the data to download.
        :return: None
        """
        self._data_name = value

    @property
    def data_resources(self):
        """
        Return the data resources dictionary.
        :return: The data resources dictionary.
        """
        return self._data_resources

    @data_resources.setter
    def data_resources(self, value):
        """
        Set the data resources dictionary.
        :param value: The data resources dictionary.
        :return: None
        """
        self._data_resources = value

    def _authorize_download(self, prompt=None):
        """
        Check with the user that they agree to terms and conditions for the data.
        :param data_name: The name of the data to download.
        :param prompt: A function that takes a string and returns a boolean.
        :return: True if the user agrees to the terms and conditions.
        :raises: ValueError if the data is not found.
        """

        if prompt is None:
            prompt = prompt_stdin

        print(f"Acquiring resource: {self.data_name}\n")
        print("Details of data: ")
        print(self._dr.get("details", "No details available."))

        if self._dr.get("citation"):
            print("\nPlease cite:\n" + self._dr["citation"])
        if self._dr.get("size"):
            print(
                f"\nAfter downloading, the data will take up {self._dr['size']} bytes of space."
            )

        storage_path = os.path.join(self.interface["default_cache_path"], self.data_name)
        print(f"\nData will be stored in {storage_path}.\n")

        if self.interface["overide_manual_authorize"]:
            if self._dr.get("license"):
                print(
                    "You have agreed to the following license:\n" + self._dr["license"]
                )
            return True
        else:
            if self._dr.get("license"):
                print(
                    "You must also agree to the following license:\n"
                    + self._dr["license"]
                )
            return prompt("Do you wish to proceed with the download? [yes/no] ")

    def _download_url(
        self,
        url,
        dir_name=".",
        save_name=None,
        store_directory=None,
        messages=True,
        suffix="",
    ):
        """
        Download a file from a url and save it to disk.

        :param url: The url to download from.
        :param dir_name: The directory to save the file to.
        :param save_name: The name to save the file as.
        :param store_directory: The directory to store the file in.
        :param messages: Whether to print messages to the console.
        :param suffix: The suffix to add to the url.
        :return: None
        """
        file_name = os.path.basename(url)
        if store_directory is not None:
            dir_name = os.path.join(dir_name, store_directory)
        if save_name is None:
            save_name = file_name
        save_path = os.path.join(dir_name, save_name)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        try:
            response = urlopen(url + suffix)
        except HTTPError as e:
            raise ValueError(f"HTTP error {e.code} when accessing {url}")
        except URLError as e:
            raise ValueError(f"URL error {e.reason} when accessing {url}")

        self._save_file(response, save_path)

    def _save_file(self, response, save_path):
        """
        Save the file with progress bar.

        :param response: The response object from urlopen.
        :param save_path: The path to save the file to.
        :return: None
        """
        try:
            file_size = int(response.info().get("Content-Length"))
        except (TypeError, ValueError):
            file_size = None

        with open(save_path, "wb") as f:
            if file_size:
                from tqdm import tqdm

                with tqdm(total=file_size, unit="B", unit_scale=True) as bar:
                    for buff in iter(lambda: response.read(1024), b""):
                        f.write(buff)
                        bar.update(len(buff))
            else:
                f.write(response.read())

    def download_data(self, prompt=prompt_stdin):
        """
        Check with the user that they are happy with terms and conditions for the data, then download it.
        :param prompt: A function that takes a string and returns a boolean.
        :return: None
        :raises: ValueError if the data is not found.
        """
        if not self._authorize_download(prompt):
            raise Exception("Permission to download data denied.")

        self._process_data()

    def _process_data(self):
        """
        Process the data for downloading based on its configuration.

        :return: None
        """
        if "suffices" in self._dr:
            self._download_suffices()
        elif "dirs" in self._dr:
            self._download_dirs()
        else:
            self._download_simple()

    def _download_suffices(self):
        """
        Download a data with a suffices.

        :return: None
        """
        for url, filenames, suffices in zip(
            self._dr["urls"], self._dr["files"], self._dr["suffices"]
        ):
            for filename, suffix in zip(filenames, suffices):
                self._download_file(url, filename, suffix=suffix)

    def _download_dirs(self):
        """
        Download a data with directories.

        :return: None
        """
        for url, dirnames, filenames in zip(
            self._dr["urls"], self._dr["dirs"], self._dr["files"]
        ):
            for filename, dirname in zip(filenames, dirnames):
                self._download_file(url, filename, dirname=dirname)

    def _download_simple(self):
        """
        Download the data.

        :return: None
        """
        for url, filenames in zip(self._dr["urls"], self._dr["files"]):
            for filename in filenames:
                self._download_file(url, filename)

    def _download_file(self, url, filename, dirname=None, suffix=""):
        """
        Download a file from a url and save it to disk.

        :param url: The url to download from.
        :param filename: The name to save the file as.
        :param dirname: The directory to store the file in.
        :param suffix: The suffix to add to the url.
        :return: None
        """

        full_url = os.path.join(url, dirname if dirname else "", filename).replace(
            " ", "%20"
        )
        save_name = filename if not suffix else filename + suffix
        self._download_url(
            url=full_url,
            store_directory=self.interface["default_cache_path"],
            save_name=save_name,
        )


class GitDownloader(FileDownloader):
    def __init__(self, interface, data_resources, data_name, git_url):
        super().__init__(interface, data_resources, data_name)
        self._git_url = git_url
        self._repo_path = self.interface["default_cache_path"]

    def _process_data(self):
        """
        Process the data for downloading based on its configuration.

        :return: None
        """
        self._clone_or_pull_repo()
        
    def _clone_or_pull_repo(self):
        """
        Clone the repository or pull updates if it already exists.

        :return: None
        """
        clone_or_pull_repo(self._git_url, self._repo_path)
