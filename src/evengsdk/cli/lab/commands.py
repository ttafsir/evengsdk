# -*- coding: utf-8 -*-
import os
import sys
import threading
from itertools import chain
from pathlib import Path
from typing import Dict, List

import click

from evengsdk.cli.utils import get_active_lab, get_client, thread_executor
from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengApiError, EvengHTTPError
from evengsdk.plugins.display import display


# https://stackoverflow.com/questions/37310718/mutually-exclusive-option-groups-in-python-click
class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help_str = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help_str + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
                " The API supports editing a single field at a time."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`. You may only set one at a time".format(
                    self.name, ", ".join(self.mutually_exclusive)
                )
            )
        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


client = None
thread_local = threading.local()


def _get_client_session():
    if not hasattr(thread_local, "client"):
        thread_local.client = client
    return thread_local.client


def _get_lab_folder(name: str) -> List[Dict]:
    """Get labs from nested folder structure

    :param name: folder name
    :type name: str
    :return: list of labs
    """
    session = _get_client_session()
    r = session.api.get_folder(name)
    # get the labs from the folder
    labs_from_folder = [r.get("data", {}).get("labs")]
    # let's get labs from nested folders too
    nested_folders = r.get("data", {}).get("folders")
    while len(nested_folders) > 1:
        for folder in nested_folders:
            if folder["name"] == "..":
                continue
            r = session.api.get_folder(f'{folder["path"]}')
            labs_from_folder.append(r.get("data", {}).get("labs"))
    return labs_from_folder


def _get_lab_details(path: str) -> Dict:
    """
    Worker for Thread Executor to parse labs from folders
    """
    session = _get_client_session()
    response = session.api.get_lab(path)
    if response:
        path = path.lstrip("/")
        response["data"].update({"path": "/" + path})
    return response


def _get_all_labs(client: EvengClient) -> List:
    """
    Get all labs from EVE-NG host by parsing all nested folders
    """
    resp = client.api.list_folders()
    root_folders = resp.get("data", {}).get("folders")
    labs_in_root_folder = resp.get("data", {}).get("labs")

    # Get the lab information from all other folders (non-root)
    labs_in_nested_folders = chain(
        *thread_executor(_get_lab_folder, (x["name"] for x in root_folders))
    )
    # flatten the results to single iterable
    # (labs from root folder + labs from nested)
    all_lab_info = chain(labs_in_root_folder, *labs_in_nested_folders)
    return thread_executor(_get_lab_details, (x["path"] for x in all_lab_info))


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def read(ctx, path, output):
    """
    Get EVE-NG lab details
    """
    try:
        client = get_client(ctx)
        resp = client.api.get_lab(path)
        lab = resp.get("data", {})
        click.secho(f"Lab: {lab.get('name')}", fg="bright_blue")
        click.echo(display(output, lab))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("--output", type=click.Choice(["json"]), default="json")
@click.pass_context
def topology(ctx, path, output):
    """
    Retrieve lab topology
    """
    try:
        client = get_client(ctx)
        resp = client.api.get_lab_topology(path)
        topology = resp.get("data", {})
        click.secho(f"Lab Topology @ {path}", fg="bright_blue")
        click.echo(display(output, topology))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command(name="export")
@click.option("--dest", help="destination path", type=click.Path(), default=".")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def export_lab(ctx, path, dest):
    """
    Export and download lab file as ZIP archive
    """
    client = get_client(ctx)
    try:
        client.log.debug(f"Exporting lab {path} to {dest}")
        saved, zipname = client.api.export_lab(path)
        if saved:
            click.secho(display("text", f"Success: {zipname}"))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        client.log.error(f"{e}")
        raise


@click.command(name="import")
@click.option("--src", help="source path to ZIP lab file", type=click.Path(exists=True))
@click.option("--folder", default="/", help="folder on EVE-NG to import lab to")
@click.pass_context
def import_lab(ctx, folder, src):
    """
    Import lab into EVE-NG from ZIP archive
    """
    try:
        client = get_client(ctx)
        resp = client.api.import_lab(Path(src), folder)
        click.echo(display("text", resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command(name="list")
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def ls(ctx, output):
    """
    List the available labs in EVE-NG host
    """
    try:
        client = get_client(ctx)
        lab_details = _get_all_labs(client)
        click.secho("Labs", fg="bright_blue")
        click.echo(display(output, lab_details))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option("--path", default="/", help="folder to create lab in")
@click.option("--name", help="lab name")
@click.option("--author", help="lab author")
@click.option("--description", help="lab description")
@click.option("--version", help="lab version")
@click.pass_context
def create(ctx, path: str, author: str, description: str, version: int, name: str):
    """
    Create a new lab
    """
    try:
        client = get_client(ctx)
        response = client.api.create_lab(
            name=name,
            author=author,
            path=path,
            description=description,
            version=version,
        )
        click.echo(display("text", response.get("message", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option(
    "--author",
    help="lab author",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["version", "description", "body"],
)
@click.option(
    "--description",
    help="lab description.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "version", "body"],
)
@click.option(
    "--version",
    help="lab version.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "description", "body"],
)
@click.option(
    "--body",
    help="long description for lab.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "description", "version"],
)
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def edit(ctx, path: str, **kwargs):
    """Edit a lab on EVE-NG host. EVE-NG API supports updating
    a single field at a time.

    \b
    Examples:
        eve-ng lab edit --author "Tafsir Thiam"
        eve-ng lab edit --body "Lab to demonstrate VXLAN/BGP-EVPN on vEOS"
    """
    try:
        edit_param = {k: v for k, v in kwargs.items() if v is not None}
        client = get_client(ctx)
        click.echo(f"updating lab @: {path}")
        response = client.api.edit_lab(path, param=edit_param)
        click.echo(display("text", response.get("message", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option("--path", default="/", help="folder to create lab in")
@click.pass_context
def delete(ctx, path):
    """
    Delete a lab on EVE-NG host
    """
    try:
        client = get_client(ctx)
        response = client.api.delete_lab(path)
        click.echo(display("text", response.get("message", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def start(ctx, path):
    """Start all nodes in lab"""
    try:
        client = get_client(ctx)
        response = client.api.start_all_nodes(path)
        click.echo(display("text", response.get("message", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def stop(ctx, path):
    """
    Stop all nodes in lab
    """
    try:
        client = get_client(ctx)
        response = client.api.stop_all_nodes(path)
        if response.get("status") and response["status"] == "success":
            close_resp = client.delete("/labs/close")
            click.echo(display("text", close_resp.get("message", {})))
        else:
            click.echo(display("text", response.get("message", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command(name="show-active")
@click.pass_context
def show_active(ctx):
    """
    Show active lab
    """
    title = click.style("Active Lab: ", fg="bright_blue")
    active_lab = ctx.obj.active_lab or os.environ.get("EVE_NG_PATH")
    click.echo(f"{title}{active_lab}")


@click.command(name="set-active")
@click.option("--path", help="path to lab to activate")
@click.pass_context
def active(ctx, path):
    """
    Set current lab path
    """
    active_lab_dir = ctx.obj.active_lab_dir
    active_lab_filepath = Path(active_lab_dir) / "active"

    # retrieve active lab from either the active lab file or ENV
    if not path:
        if active_lab_filepath.exists():
            active_lab = active_lab_filepath.read_text()
        else:
            active_lab = os.environ.get("EVE_NG_PATH")
        click.secho("Active Lab", fg="bright_blue")
        click.echo(active_lab)

    # set path option as active lab
    else:
        client.login(username=ctx.obj.username, password=ctx.obj.password)
        # Make sure this is a lab that exists in EVE-NG
        labs = _get_all_labs(client)
        existing_lab = next((lab for lab in labs if lab["path"] == path), None)
        if not existing_lab:
            msg = click.style(
                f"\nLab @ {path} does not exist or could not be found.", fg="red"
            )
            sys.exit(msg)
        else:
            # TODO: Stop previously active lab?
            active_lab_filepath.write_text(path)
            click.secho(f"Active Lab set to {path}", fg="green")


@click.group()
@click.pass_context
def lab(ctx):
    """
    lab sub commands

    Manage EVE-NG labs
    """
    global client
    ctx.obj.active_lab = get_active_lab(ctx.obj.active_lab_dir)
    client = ctx.obj.client


lab.add_command(read)
lab.add_command(ls)
lab.add_command(start)
lab.add_command(stop)
lab.add_command(create)
lab.add_command(edit)
lab.add_command(delete)
lab.add_command(active)
lab.add_command(show_active)
lab.add_command(topology)
lab.add_command(import_lab)
lab.add_command(export_lab)
