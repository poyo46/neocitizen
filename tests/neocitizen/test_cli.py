import os
from tempfile import TemporaryDirectory
from typing import List, Optional

import pytest
from click.testing import CliRunner, Result

from neocitizen.api import NeocitiesApi
from neocitizen.cli import cli

from .env import TEST_API_KEY


def get_result(args: List[str], input: Optional[str] = None) -> Result:
    runner = CliRunner()
    return runner.invoke(cli, ["--key", os.environ[TEST_API_KEY]] + args, input=input)


@pytest.mark.parametrize(
    "args, expected_code",
    [
        (["upload"], 0),
        (["upload", "--dir=foo"], 0),
        (["upload", "--dir=foo", "--dir-on-server=bar"], 0),
        (["upload", "--file=foo.txt"], 0),
        (["upload", "--file=foo.txt:dir/foo.txt", "--file=bar.txt:dir/bar.txt"], 0),
        (["upload", "--file=foo.txt:dir1/foo.txt:dir2/foo.txt"], 1),
    ],
)
def test_upload(args, monkeypatch, expected_code):
    def upload_files(self, file_map):
        return {"result": "success"}

    def upload_dir(self, dir, dir_on_server):
        return {"result": "success"}

    monkeypatch.setattr(NeocitiesApi, "upload_files", upload_files)
    monkeypatch.setattr(NeocitiesApi, "upload_dir", upload_dir)

    result = get_result(args)
    assert result.exit_code == expected_code


@pytest.mark.parametrize(
    "args, input",
    [
        (["delete"], None),
        (["delete", "--yes"], None),
        (["delete", "--all"], "y"),
        (["delete", "--all"], "N"),
        (["delete", "--all", "--yes"], None),
        (["delete", "--file=foo", "--file=bar"], "y"),
        (["delete", "--file=foo", "--file=bar"], "N"),
        (["delete", "--file=foo", "--file=bar", "--yes"], None),
    ],
)
def test_delete(args, input, monkeypatch):
    def delete_files(self, filenames):
        return {"result": "success"}

    def delete_all(self, waiting_seconds):
        return {"result": "success"}

    monkeypatch.setattr(NeocitiesApi, "delete_files", delete_files)
    monkeypatch.setattr(NeocitiesApi, "delete_all", delete_all)

    result = get_result(args, input)
    assert result.exit_code == 0


def test_download(monkeypatch):
    def download_all(self, save_to):
        return None

    monkeypatch.setattr(NeocitiesApi, "download_all", download_all)

    with TemporaryDirectory() as temp_dir:
        result = get_result(["download", str(temp_dir)])
        assert result.exit_code == 0


@pytest.mark.parametrize(
    "args",
    [
        ["list"],
        ["list", "--path=foo"],
        ["list", "--format=json"],
        ["list", "--path=foo", "--format=json"],
    ],
)
def test_list(args, monkeypatch):
    def fetch_file_list(self, path_on_server):
        if path_on_server is None:
            dir = ""
        else:
            dir = path_on_server
        return {
            "result": "success",
            "files": [
                {
                    "path": "index.html",
                    "is_directory": False,
                    "size": 262,
                    "updated_at": "Mon, 20 Dec 2021 13:11:59 -0000",
                    "sha1_hash": "68f8f7bf71d3aad29a17f5979f75940199a9db88",
                },
                {
                    "path": dir,
                    "is_directory": True,
                    "updated_at": "Mon, 20 Dec 2021 13:11:59 -0000",
                },
                {
                    "path": f"{dir}/file0.html",
                    "is_directory": False,
                    "size": 268,
                    "updated_at": "Mon, 20 Dec 2021 13:11:59 -0000",
                    "sha1_hash": "ab4af11ff992e7e286099283d3bc50329717f9b9",
                },
                {
                    "path": f"{dir}/file1.html",
                    "is_directory": False,
                    "size": 268,
                    "updated_at": "Mon, 20 Dec 2021 13:11:59 -0000",
                    "sha1_hash": "778551cdcb5f9357075ace13237e5b4691edb1a3",
                },
            ],
        }

    monkeypatch.setattr(NeocitiesApi, "fetch_file_list", fetch_file_list)

    result = get_result(args)
    assert result.exit_code == 0
    if "--path=foo" not in args:
        assert "index.html" in result.output


@pytest.mark.parametrize(
    "args",
    [
        ["info"],
        ["info", "--sitename=youpi"],
        ["info", "--format=json"],
        ["info", "--sitename=youpi", "--format=json"],
    ],
)
def test_info(args, monkeypatch):
    def fetch_info(self, sitename):
        return {
            "result": "success",
            "info": {
                "sitename": sitename,
                "views": 336,
                "hits": 577,
                "created_at": "Sun, 05 Dec 2021 12:13:28 -0000",
                "last_updated": "Mon, 20 Dec 2021 12:34:27 -0000",
                "domain": None,
                "tags": [],
                "latest_ipfs_hash": None,
            },
        }

    monkeypatch.setattr(NeocitiesApi, "fetch_info", fetch_info)

    result = get_result(args)
    assert result.exit_code == 0
    assert "sitename" in result.output


def test_api_key(monkeypatch):
    def fetch_api_key(self):
        return {"result": "success", "api_key": os.environ[TEST_API_KEY]}

    monkeypatch.setattr(NeocitiesApi, "fetch_api_key", fetch_api_key)

    result = get_result(["key"])
    assert result.exit_code == 0
    assert os.environ[TEST_API_KEY] in result.output
