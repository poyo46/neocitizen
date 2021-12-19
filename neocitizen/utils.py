from pathlib import Path


def get_extension(path: Path) -> str:
    """
    Get the extension of the ``path``.

    Parameters
    ----------
    path : Path
        Any ``Path`` object.

    Notes
    -----
    This function is a modification of the `suffix` property of `pathlib`.
    https://github.com/python/cpython/blob/f025ae63dccf96c4a1d781a6438bd9ed1502f0a1/Lib/pathlib.py#L717

    Returns
    -------
    str
        Extension of ``path``.

    Examples
    --------
    >>> assert get_extension(Path("file.txt")) == ".txt"
    >>> assert get_extension(Path("file")) == ""
    >>> assert get_extension(Path(".txt")) == ".txt"
    >>> assert get_extension(Path("file.tar.gz")) == ".gz"
    >>> assert get_extension(Path("dir/")) == ""
    """
    i = path.name.rfind(".")
    if 0 <= i < len(path.name) - 1:
        return path.name[i:]
    else:
        return ""
