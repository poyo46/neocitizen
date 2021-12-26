import hashlib
import os
import shutil
from datetime import datetime
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import Any, Dict, Optional

from neocitizen.errors import ApiError, ArgumentError
from neocitizen.types import PathType
from tests.env import TEST_API_KEY


class NeocitiesMockServer(object):
    def __init__(self, dir: Path) -> None:
        self.dir = dir
        self.api_key = os.environ[TEST_API_KEY]

    def _response(
        self, content: Optional[Dict] = None, is_error: Optional[bool] = None
    ) -> Dict:
        response = {"result": "error" if is_error else "success"}
        if content is not None:
            response.update(content)
        return response

    def _post_upload(self, **kwargs) -> Any:
        for name, data in kwargs["files"].items():
            path = self.dir / name
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, mode="wb") as f:
                f.write(data)
        return self._response(
            content={"message": "your file(s) have been successfully uploaded"}
        )

    def _cannot_delete_index_error(self) -> Any:
        return self._response(
            content={
                "error_type": "cannot_delete_index",
                "message": "you cannot delete your index.html file, canceled deleting",
            },
            is_error=True,
        )

    def _missing_files_error(self, name: str) -> Any:
        return self._response(
            content={
                "error_type": "missing_files",
                "message": f"{name} was not found on your site, canceled deleting",
            },
            is_error=True,
        )

    def _post_delete(self, **kwargs) -> Any:
        deleted_names = []
        for name in kwargs["data"]["filenames[]"]:
            if name == "index.html":
                raise ApiError(self._cannot_delete_index_error())
            path = self.dir / name
            if any([n in name for n in deleted_names]):
                continue
            if not path.exists():
                raise ApiError(self._missing_files_error(name))
            if path.is_file():
                os.remove(str(path))
            if path.is_dir():
                shutil.rmtree(str(path))
            deleted_names.append(name)
        return self._response(content={"message": "file(s) have been deleted"})

    def _get_list(self) -> Any:
        files = []
        for path in self.dir.glob("**/*"):
            updated_at = datetime.fromtimestamp(path.stat().st_mtime)
            file = {
                "path": str(path.relative_to(self.dir)),
                "is_directory": path.is_dir(),
                "updated_at": updated_at.strftime("%a, %d %b %Y %H:%M:%S -0000"),
            }
            if path.is_file():
                file["size"] = path.stat().st_size
                with open(path, mode="rb") as f:
                    file["sha1_hash"] = hashlib.sha1(f.read()).hexdigest()
            files.append(file)
        return self._response(content={"files": files})

    def _get_info(self, **kwargs) -> Any:
        params = kwargs.get("params", None)
        if params and "sitename" in params.keys():
            sitename = params["sitename"]
        else:
            sitename = "neocli-test"
        info = {
            "sitename": sitename,
            "views": 376,
            "hits": 627,
            "created_at": "Sun, 05 Dec 2021 12:13:28 -0000",
            "last_updated": "Mon, 20 Dec 2021 16:10:20 -0000",
            "domain": None,
            "tags": ["foo", "bar"],
            "latest_ipfs_hash": None,
        }
        return self._response(content={"info": info})

    def _get_key(self) -> Any:
        return self._response(content={"api_key": self.api_key})

    def _call_api(self, method: str, path: str, **kwargs) -> Any:
        if method == "POST" and path == "/upload":
            return self._post_upload(**kwargs)
        elif method == "POST" and path == "/delete":
            return self._post_delete(**kwargs)
        elif method == "GET" and path == "/list":
            return self._get_list()
        elif method == "GET" and path == "/info":
            return self._get_info(**kwargs)
        elif method == "GET" and path == "/key":
            return self._get_key()
        raise ApiError(
            self._response(
                content={
                    "error_type": "not_found",
                    "message": "the requested api call does not exist",
                },
                is_error=True,
            )
        )

    def download_all(self, save_to: PathType) -> None:
        parent = Path(save_to)
        if not parent.is_dir():
            raise ArgumentError("`save_to` must be a directory name.")

        copy_tree(str(self.dir), str(parent))
