# neocitizen: Python client library for Neocities API

[![PyPI Version](https://img.shields.io/pypi/v/neocitizen.svg)](https://pypi.org/pypi/neocitizen/)
[![Python Versions](https://img.shields.io/pypi/pyversions/neocitizen.svg)](https://pypi.org/pypi/neocitizen/)
[![License](https://img.shields.io/pypi/l/neocitizen.svg)](https://github.com/poyo46/neocitizen/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

[Neocities](https://neocities.org/) is a web hosting service for static pages.
This is a library that makes the [Neocities API](https://neocities.org/api) available from the CLI and Python.

## Installation

`neocitizen` is available on PyPI:

```console
$ pip install neocitizen
```

You can also use [poetry](https://python-poetry.org/) to add it to a Python project.

```console
$ poetry add neocitizen
```

## CLI Examples

**Upload the directory and check the result**

```
$ export NEOCITIES_API_KEY=<your api key here>
$ neocitizen upload --dir=/path/to/dir
$ neocitizen list
dir0
dir0/file00.html
dir0/file01.html
dir1
dir1/dir10
dir1/dir10/file100.html
dir1/dir11
dir1/dir11/file110.html
dir1/file10.html
dir1/file11.html
index.html
```

**Download**

```
$ export NEOCITIES_API_KEY=<your api key here>
$ neocitizen download /path/to/save
```

**Detailed usage**

```
$ neocitizen --help
Usage: neocitizen [OPTIONS] COMMAND [ARGS]...

Options:
  --version        Show the version and exit.
  --key TEXT       API key. You can also use the environment variable NEOCITIES_API_KEY instead.
  --username TEXT  User name for authentication. You can also use the environment variable NEOCITIES_USERNAME instead.
  --password TEXT  Password for authentication. You can also use the environment variable NEOCITIES_PASSWORD instead.
  -v, --verbose    Verbose output.
  --help           Show this message and exit.

Commands:
  delete    Delete the files on your Neocities site.
  download  Download all the files on your Neocities site.
  info      Show information about your Neocities site.
  key       Show API key.
  list      Show file list your Neocities site.
  upload    Upload local data to your Neocities site.
```

## Python Examples

**Code: example.py**

```python:example.py
from neocitizen import NeocitiesApi

api = NeocitiesApi()
response = api.fetch_info()
for key, value in response["info"].items():
    print(f"{key}: {value}")

```

**Run**

```
$ export NEOCITIES_API_KEY=<your api key here>
$ python example.py
sitename: neocli-test
views: 268
hits: 483
created_at: Sun, 05 Dec 2021 12:13:28 -0000
last_updated: Sun, 19 Dec 2021 13:37:13 -0000
domain: None
tags: []
latest_ipfs_hash: None
```
