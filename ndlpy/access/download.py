import os

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import git

from ndlpy.util.misc import prompt_stdin
from ..log import Logger
from ..config.context import Context

from ..config.interface import Interface

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)


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
        # Ensure the cache path exists
        if not os.path.exists(self._repo_path):
            os.makedirs(self._repo_path)

        # Check if the repo already exists
        if os.path.isdir(os.path.join(self._repo_path, '.git')):
            try:
                repo = git.Repo(self._repo_path)
                repo.git.pull()
            except Exception as e:
                raise ValueError(f"Error pulling repository: {e}")
        else:
            try:
                git.Repo.clone_from(self._git_url, self._repo_path)
            except Exception as e:
                raise ValueError(f"Error cloning repository: {e}")
