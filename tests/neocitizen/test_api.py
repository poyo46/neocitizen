import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import requests

import neocitizen.api
from neocitizen.api import NeocitiesApi
from neocitizen.errors import ApiError, ArgumentError, CredentialsRequiredError

API_KEY = "NEOCITIES_API_KEY"
TEST_API_KEY = f"TEST_{API_KEY}"
USERNAME = "NEOCITIES_USERNAME"
PASSWORD = "NEOCITIES_PASSWORD"


def del_env(*keys) -> None:
    for key in keys:
        if os.getenv(key) is not None:
            del os.environ[key]


class TestNeocitiesApi(object):
    def setup_method(self):
        del_env(API_KEY, USERNAME, PASSWORD)
        self.api = NeocitiesApi(api_key=os.environ[TEST_API_KEY])

    def teardown_method(self):
        del self.api
        del_env(API_KEY, USERNAME, PASSWORD)

    @classmethod
    def teardown_class(cls):
        api = NeocitiesApi(api_key=os.environ[TEST_API_KEY])
        api.delete_all(waiting_seconds=0)

    @pytest.mark.parametrize(
        "api_key, username, password, timeout, verbose",
        [
            ("*", None, None, None, None),
            (None, "*", "*", None, None),
            ("*", None, None, 30, None),
            ("*", None, None, None, True),
        ],
    )
    def test_can_initialize_with_arguments(
        self, api_key, username, password, timeout, verbose
    ):
        NeocitiesApi(
            api_key=api_key,
            username=username,
            password=password,
            timeout=timeout,
            verbose=verbose,
        )

    def test_can_initialize_with_environment_variable(self):
        # api_key
        os.environ[API_KEY] = "key"
        NeocitiesApi()
        del_env(API_KEY)

        # username and password
        os.environ[USERNAME] = "username"
        os.environ[PASSWORD] = "password"
        NeocitiesApi()

    def test_init_raises_error(self):
        with pytest.raises(CredentialsRequiredError):
            NeocitiesApi()

    def test_api_returns_error(self):
        with pytest.raises(ApiError):
            self.api._call_api(method="PUT", path="/foo")

    def test_call_api_raises_error(self, monkeypatch):
        with pytest.raises(Exception):
            monkeypatch.setattr(neocitizen.api, "BASE_URL", "https://foobar")
            api = neocitizen.api.NeocitiesApi(api_key=os.environ[TEST_API_KEY])
            api.fetch_info()

    @pytest.mark.parametrize(
        "dir_on_server",
        [None, "upload_test1", "upload_test2/"],
    )
    def test_can_upload_directory(self, dir_on_server, data_dir):
        # count the number of files before uploading
        file_list_response = self.api.fetch_file_list()
        count_before = len(file_list_response["files"])

        # upload
        upload_response = self.api.upload_dir(dir=data_dir, dir_on_server=dir_on_server)
        assert upload_response["result"] == "success"

        # count the number of files after uploading
        file_list_response = self.api.fetch_file_list()
        count_after = len(file_list_response["files"])

        assert count_before < count_after

    def test_can_delete_files(self, data_dir):
        # upload
        dir_on_server = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.api.upload_dir(dir=data_dir, dir_on_server=dir_on_server)

        # count the number of files before deleting
        file_list_response = self.api.fetch_file_list()
        count_before = len(file_list_response["files"])

        # file names
        filenames = []
        for file in file_list_response["files"]:
            if file["path"].startswith(dir_on_server):
                filenames.append(file["path"])

        # delete
        response = self.api.delete_files(filenames=filenames)
        assert response["result"] == "success"

        # count the number of files after uploading
        file_list_response = self.api.fetch_file_list()
        count_after = len(file_list_response["files"])

        assert count_before > count_after

    def test_can_delete_files_of_zero_length(self):
        response = self.api.delete_files(filenames=[])
        assert response["result"] == "success"

    def test_can_delete_all_files(self, index_template):
        response = self.api.delete_all(waiting_seconds=0)
        assert response["result"] == "success"

        # Make sure that all files except index.html have been deleted.
        file_list_response = self.api.fetch_file_list()
        assert len(file_list_response["files"]) == 1
        assert file_list_response["files"][0]["path"] == "index.html"

        # Make sure that index.html is initialized.
        info_response = self.api.fetch_info()
        sitename = info_response["info"]["sitename"]
        index_response = requests.get(f"https://{sitename}.neocities.org/index.html")
        with open(index_template) as f:
            assert index_response.text == f.read()

    def test_can_download_all_files(self, data_dir):
        self.api.upload_dir(dir=data_dir)
        file_list_response = self.api.fetch_file_list()
        expected_count = len(file_list_response["files"])
        with TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            self.api.download_all(save_to=temp_dir)
            count = len(list(temp_dir.glob("**/*")))
            assert count == expected_count

    def test_download_all_raises_error(self):
        with pytest.raises(ArgumentError):
            self.api.download_all(save_to=Path("file.txt"))

    @pytest.mark.parametrize(
        "path_on_server",
        [None, "foo"],
    )
    def test_can_fetch_file_list(self, path_on_server):
        response = self.api.fetch_file_list(path_on_server=path_on_server)
        assert response["result"] == "success"

    @pytest.mark.parametrize(
        "sitename",
        [None, "youpi"],
    )
    def test_can_fetch_info(self, sitename):
        response = self.api.fetch_info(sitename=sitename)
        assert response["result"] == "success"

    def test_can_fetch_api_key(self):
        response = self.api.fetch_api_key()
        assert response["result"] == "success"

    def test_can_verbose_output(self, data_dir):
        self.api.verbose = True
        self.api.upload_dir(dir=data_dir)
        self.api.delete_all(waiting_seconds=0)
        self.api.verbose = False
