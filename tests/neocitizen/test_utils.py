from pathlib import Path

import pytest

from neocitizen.utils import get_extension


@pytest.mark.parametrize(
    "path, expected",
    [
        (Path("file.txt"), ".txt"),
        (Path("file"), ""),
        (Path(".txt"), ".txt"),
        (Path("file.tar.gz"), ".gz"),
        (Path("dir/"), ""),
    ],
)
def test_get_extension(path, expected):
    assert get_extension(path) == expected
