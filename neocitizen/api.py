import logging
import os
import traceback
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Optional

import click
import requests
from requests.auth import HTTPBasicAuth
from requests.models import PreparedRequest, Response

from neocitizen.errors import ApiError, ArgumentError, CredentialsRequiredError

from .types import PathType
from .utils import get_extension

logger = logging.getLogger(__name__)

BASE_URL = "https://neocities.org/api"

# https://github.com/neocities/neocities/blob/master/models/site.rb
VALID_EXTENSIONS = [
    ".html",
    ".htm",
    ".txt",
    ".text",
    ".css",
    ".js",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".md",
    ".markdown",
    ".eot",
    ".ttf",
    ".woff",
    ".woff2",
    ".json",
    ".geojson",
    ".csv",
    ".tsv",
    ".mf",
    ".ico",
    ".pdf",
    ".asc",
    ".key",
    ".pgp",
    ".xml",
    ".mid",
    ".midi",
    ".manifest",
    ".otf",
    ".webapp",
    ".less",
    ".sass",
    ".rss",
    ".kml",
    ".dae",
    ".obj",
    ".mtl",
    ".scss",
    ".webp",
    ".xcf",
    ".epub",
    ".gltf",
    ".bin",
    ".webmanifest",
    ".knowl",
    ".atom",
    ".opml",
    ".rdf",
]


class NeocitiesApi(object):
    """
    Neocities API Client.

    Parameters
    ----------
    api_key : str or None, optional
        Neocities API key available on https://neocities.org/settings/<USERNAME>#api_key
        (Replace ``<USERNAME>`` with your username).
        You can also use the environment variable ``NEOCITIES_API_KEY`` instead.
    username : str or None, optional
        User name for authentication.
        You can also use the environment variable ``NEOCITIES_USERNAME`` instead.
    password : str or None, optional
        Password for authentication.
        You can also use the environment variable ``NEOCITIES_PASSWORD`` instead.
    timeout : int, optional
        Number of timeout seconds for each API call, by default 60.
    verbose: bool, optional
        Verbose output or not, by default ``False``.

    Notes
    -----
    The Neocities API must be used under the following rules:
    * Do not spam the server with tons of API requests.
    * Try to limit recurring site updates to one per minute.
    * Do not use the API to "game" the site (increase ranking by manipulating our
      algorithms, or constantly updating your index.html with the same content).
      Sites caught doing this will be de-listed from the browse page.
    * Do not use the API to data mine / rip all of the sites.

    For more information about the API, please see https://neocities.org/api
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 60,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        api_key : str or None, optional
            Neocities API key available on
            https://neocities.org/settings/<USERNAME>#api_key
            (Replace ``<USERNAME>`` with your username).
            You can also use the environment variable ``NEOCITIES_API_KEY`` instead.
        username : str or None, optional
            User name for authentication.
            You can also use the environment variable ``NEOCITIES_USERNAME`` instead.
        password : str or None, optional
            Password for authentication.
            You can also use the environment variable ``NEOCITIES_PASSWORD`` instead.
        timeout : int, optional
            Number of timeout seconds for each API call, by default 60.
        verbose: bool, optional
            Verbose output or not, by default ``False``.

        Notes
        -----
        One of ``api_key`` or ``username`` / ``password`` is required.
        We recommend that you get the API key and set it to the environment variable
        ``NEOCITIES_API_KEY``.

        Raises
        ------
        CredentialsRequiredError
            If the credentials are missing.
        """
        api_key = api_key or os.getenv("NEOCITIES_API_KEY")
        username = username or os.getenv("NEOCITIES_USERNAME")
        password = password or os.getenv("NEOCITIES_PASSWORD")

        # credentials
        self.__headers = None
        self.__auth = None
        if api_key:
            self.__headers = {"Authorization": f"Bearer {api_key}"}
            logger.debug("Use the API key as credentials.")
        elif username and password:
            self.__auth = HTTPBasicAuth(username, password)
            logger.debug("Use username and password as credentials.")
        else:
            logger.error("API key or username/password is required.")
            raise CredentialsRequiredError

        # timeout
        self.__timeout = timeout
        logger.debug(f"timeout: {timeout} seconds")

        # verbose
        self.verbose = verbose
        logger.debug(f"verbose = {verbose}")

        # Every response returned from the Neocities API has a "result" element,
        # regardless of its success or failure. We will mimic this response for when the
        # process is successfully completed in the client.
        self.__success = {"result": "success"}

    def _call_api(self, method: str, path: str, **kwargs) -> Any:
        """
        Send a request to the Neocities server.

        Parameters
        ----------
        method : str
            HTTP method name such as ``"GET"`` and ``"POST"``.
        path : str
            API request path followed by ``BASE_URL``

        Notes
        -----
        If a variable-length keyword argument is specified, it will be passed directly
        to ``requests.Request``.

        Returns
        -------
        Any
            API response.

        Raises
        ------
        ApiError
            If the API response is not successful.

        See Also
        --------
        ``BASE_URL`` : Base URL for Neocities API.
        """
        try:
            request: PreparedRequest = requests.Request(
                method=method,
                url=BASE_URL + path,
                headers=self.__headers,
                auth=self.__auth,
                **kwargs,
            ).prepare()

            session = requests.Session()
            if self.verbose:
                click.echo(f"Calling Neocities API: {method} {path}")
            response: Response = session.send(request, timeout=self.__timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(response.json())
                raise ApiError(response.json())
        except Exception as e:
            logger.error(traceback.format_exc())
            raise e

    def upload_files(self, file_map: Dict[PathType, str]) -> Any:
        """
        Upload local files to your Neocities site.

        Parameters
        ----------
        file_map : Dict[PathType, str]
            Correspondence between local file paths and upload destinations.

        Notes
        -----
        The extensions of the files that can be uploaded are as follows:

            html htm txt text css js jpg jpeg png gif svg md markdown eot ttf woff woff2
            json geojson csv tsv mf ico pdf asc key pgp xml mid midi manifest otf webapp
            less sass rss kml dae obj mtl scss webp xcf epub gltf bin webmanifest knowl
            atom opml rdf

        For the latest information, please visit
        https://github.com/neocities/neocities/blob/master/models/site.rb

        Returns
        -------
        Any
            API response.
        """
        if self.verbose:
            click.echo("Upload files")

        files: Dict[str, bytes] = {}
        for local_path, path_on_server in file_map.items():
            # check file extension
            extension = get_extension(Path(local_path))
            if extension not in VALID_EXTENSIONS:
                message = f"Skip file '{str(local_path)}' because the extension '{extension}' is not allowed."  # noqa: E501
                logger.warn(message)
                click.echo(message)
                continue

            # read file
            with open(local_path, mode="rb") as f:
                files[path_on_server] = f.read()
                message = f"Correspondence: {str(local_path)} -> {path_on_server}"
                logger.debug(message)
                if self.verbose:
                    click.echo(message)

        if self.verbose:
            click.echo("Now uploading...")
        return self._call_api(method="POST", path="/upload", files=files)

    def upload_dir(self, dir: PathType, dir_on_server: Optional[str] = None) -> Any:
        """
        Upload a local directory to your Neocities site.

        Parameters
        ----------
        dir : PathType
            Local directory path.
        dir_on_server : str or None, optional
            Path to upload to; if None, the directory will be uploaded to the root path.

        Notes
        -----
        Empty directories will not be uploaded.

        Returns
        -------
        Any
            API response.
        """
        dir = Path(dir)
        if dir_on_server is None:
            dir_on_server = ""
        elif not dir_on_server.endswith("/"):
            dir_on_server += "/"
        message = f"Upload directory {str(dir)} to {dir_on_server or '/'}"
        logger.info(message)
        if self.verbose:
            click.echo(message)

        file_map = {}
        for path in dir.glob("**/*"):
            if path.is_file():
                file_map[path] = dir_on_server + str(path.relative_to(dir))

        return self.upload_files(file_map)

    def _initialize_index_html(self) -> Any:
        if self.verbose:
            click.echo("Initializing index.html")
        return self.upload_files({Path(__file__).with_name("index.html"): "index.html"})

    def delete_files(self, filenames: List[str]) -> Any:
        """
        Delete the files on your Neocities site.

        Parameters
        ----------
        filenames : List[str]
            List of file paths on your Neocities site.

        Returns
        -------
        Any
            API response.

        Warnings
        --------
        This operation cannot be undone. We recommend that you download the files
        beforehand to avoid accidentally deleting them.
        """
        if self.verbose:
            click.echo("Delete files")

        if len(filenames) == 0:
            return self.__success

        data = {"filenames[]": filenames}
        message = "File names to be deleted: \n" + "\n".join(filenames)
        logger.debug(message)
        if self.verbose:
            click.echo(message)
            click.echo("Now deleting...")
        return self._call_api(method="POST", path="/delete", data=data)

    def delete_all(self, waiting_seconds: int = 10) -> Any:
        """
        Delete all files on your Neocities site.

        Notes
        -----
        Since index.html cannot be deleted, replace it with an empty template file.

        Parameters
        ----------
        waiting_seconds : int, optional
            Number of seconds to wait before throwing an HTTP request for this deletion
            process, by default 10

        Returns
        -------
        Any
            API response.

        Warnings
        --------
        This operation cannot be undone. We recommend that you download the files
        beforehand to avoid accidentally deleting them.
        """
        if self.verbose:
            click.echo("Delete all files")

        # filenames
        file_list_response = self.fetch_file_list()
        filenames = [
            file["path"]
            for file in file_list_response["files"]
            if file["path"] != "index.html"
        ]

        # wait before deleting
        sleep(waiting_seconds)

        self.delete_files(filenames)
        return self._initialize_index_html()

    def download_all(self, save_to: PathType) -> None:
        """
        Download all the files on your Neocities site.

        Parameters
        ----------
        save_to : PathType
            Local directory where the files will be saved.

        Raises
        ------
        ArgumentError
            If ``save_to`` is not a directory.
        """
        parent = Path(save_to)
        logger.debug(f"save_to: {str(parent)}")
        if not parent.is_dir():
            raise ArgumentError("`save_to` must be a directory name.")

        # site name
        info_response = self.fetch_info()
        sitename = info_response["info"]["sitename"]
        logger.debug(f"sitename: {sitename}")

        # file list
        file_list_response = self.fetch_file_list()
        files = []
        for file in file_list_response["files"]:
            logger.debug(f"file: {str(file)}")
            filename = file["path"]
            files.append(
                {
                    "url": f"https://{sitename}.neocities.org/{filename}",
                    "local_path": parent / filename,
                    "is_directory": file["is_directory"],
                }
            )

        # save
        n = len(files)
        message = f"Download {n} files from https://{sitename}.neocities.org/"
        logger.info(message)
        with click.progressbar(files, label=message, length=n) as bar:
            for file in bar:
                # make directories to store the file
                os.makedirs(os.path.dirname(file["local_path"]), exist_ok=True)

                if file["is_directory"]:
                    continue

                # download the file
                logger.debug(f"Downloading {file['url']}")
                response: Response = requests.get(file["url"])
                with open(file["local_path"], mode="wb") as f:
                    f.write(response.content)

    def fetch_file_list(self, path_on_server: Optional[str] = None) -> Any:
        """
        Fetch the file list of your Neocities site.

        Parameters
        ----------
        path_on_server : str or None, optional
            If provided, the API will return a list of files for this path.

        Returns
        -------
        Any
            API response.
        """
        if path_on_server is None:
            params = None
        else:
            params = {"path": path_on_server}
        logger.debug(f"path_on_server: {path_on_server or '/'}")

        return self._call_api(method="GET", path="/list", params=params)

    def fetch_info(self, sitename: Optional[str] = None) -> Any:
        """
        Fetch information about any website on Neocities.

        Parameters
        ----------
        sitename : str or None, optional
            If provided, the API will return the information about this website.

        Returns
        -------
        Any
            API response.
        """
        if sitename is None:
            params = None
        else:
            params = {"sitename": sitename}
        logger.debug(f"sitename: {sitename}")

        return self._call_api(method="GET", path="/info", params=params)

    def fetch_api_key(self) -> Any:
        """
        Fetch an API key that you can use for credentials.

        Notes
        -----
        It will automatically generate a new API key if one doesn't exist yet for your
        site.

        Returns
        -------
        Any
            API response.
        """
        return self._call_api(method="GET", path="/key")
