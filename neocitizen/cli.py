import json

import click
from click import BadParameter

from neocitizen import __title__, __version__
from neocitizen.api import NeocitiesApi

api = None


@click.group()
@click.version_option(version=__version__, package_name=__title__)
@click.option(
    "--key",
    help="API key. You can also use the environment variable NEOCITIES_API_KEY instead.",  # noqa: E501
)
@click.option(
    "--username",
    help="User name for authentication. You can also use the environment variable NEOCITIES_USERNAME instead.",  # noqa: E501
)
@click.option(
    "--password",
    help="Password for authentication. You can also use the environment variable NEOCITIES_PASSWORD instead.",  # noqa: E501
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
def cli(key, username, password, verbose):
    global api
    api = NeocitiesApi(
        api_key=key, username=username, password=password, verbose=verbose
    )


@cli.command(help="Upload local data to your Neocities site.")
@click.option(
    "--dir",
    "-d",
    help="Local directory path.",
    nargs=1,
)
@click.option(
    "--dir-on-server",
    help="Destination directory.",
    nargs=1,
)
@click.option(
    "--file",
    "-f",
    multiple=True,
    help="(file path) or (local file path):(path on server)",
)
def upload(dir, dir_on_server, file):
    if dir:
        api.upload_dir(dir=dir, dir_on_server=dir_on_server)
    if len(file) == 0:
        return
    file_map = {}
    for item in file:
        paths = item.split(":")
        if len(paths) == 1:
            file_map[paths[0]] = paths[0]
        elif len(paths) == 2:
            file_map[paths[0]] = paths[1]
        else:
            raise BadParameter
    api.upload_files(file_map=file_map)


@cli.command(help="Delete the files on your Neocities site.")
@click.option(
    "--all", "-A", is_flag=True, help="Delete all files on your Neocities site."
)
@click.option(
    "--file",
    "-f",
    multiple=True,
    help="File path to delete.",
)
@click.option(
    "--yes", "-y", is_flag=True, help="Automatically answer 'yes' to all questions."
)
def delete(all, file, yes):
    if all:
        if not yes:
            if not click.confirm("Delete ALL files. Do you want to continue?"):
                return
        api.delete_all(waiting_seconds=2)
    elif len(file) > 0:
        if not yes:
            if not click.confirm(f"Delete {len(file)} files. Do you want to continue?"):
                return
        api.delete_files(filenames=file)


@cli.command(help="Download all the files on your Neocities site.")
@click.argument("dir", nargs=1, type=click.Path(exists=True))
def download(dir):
    api.download_all(save_to=dir)


@cli.command(name="list", help="Show file list your Neocities site.")
@click.option(
    "--path",
    help="If provided, show a list of files for this path.",
)
@click.option(
    "--format",
    type=click.Choice(["json"], case_sensitive=False),
    help="Output format.",
)
def file_list(path, format):
    response = api.fetch_file_list(path_on_server=path)
    if format == "json":
        text = json.dumps(response["files"])
    else:
        text = "\n".join([file["path"] for file in response["files"]])
    click.echo(text)


@cli.command(help="Show information about your Neocities site.")
@click.option(
    "--sitename",
    help="Neocisites sitename.",
)
@click.option(
    "--format",
    type=click.Choice(["json"], case_sensitive=False),
    help="Output format.",
)
def info(sitename, format):
    response = api.fetch_info(sitename=sitename)
    if format == "json":
        text = json.dumps(response["info"], indent=2)
    else:
        items = []
        for key, value in response["info"].items():
            items.append(f"{key}: {value}")
        text = "\n".join(items)
    click.echo(text)


@cli.command(name="key", help="Show API key.")
def api_key():
    response = api.fetch_api_key()
    click.echo(response["api_key"])
