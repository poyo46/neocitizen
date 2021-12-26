from pathlib import Path

import pytest

from neocitizen.api import NeocitiesApi

from .mock_server import NeocitiesMockServer


@pytest.fixture(autouse=True)
def set_mock_server(tmpdir, monkeypatch):
    server = NeocitiesMockServer(dir=Path(tmpdir))
    monkeypatch.setattr(NeocitiesApi, "_call_api", server._call_api)
    monkeypatch.setattr(NeocitiesApi, "download_all", server.download_all)
