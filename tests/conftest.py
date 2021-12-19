from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def root_dir():
    return Path(__file__).parents[1].resolve()


@pytest.fixture(scope="session")
def data_dir():
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def index_template():
    return Path(__file__).parents[1] / "neocitizen" / "index.html"
