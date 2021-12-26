# -*- coding: utf-8 -*-
import sys

import click

from evengsdk.cli.utils import get_client
from evengsdk.exceptions import EvengHTTPError, EvengApiError
from evengsdk.plugins.display import display


@click.command(name="list")
@click.pass_context
def ls(ctx):
    """
    List folders on EVE-NG host
    """
    try:
        client = get_client(ctx)
        folders = client.api.list_folders()
        click.echo(display("json", folders))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{str(e)}")


@click.command()
@click.pass_context
@click.argument("path")
def create(ctx, path):
    """
    Create folder on EVE-NG host
    """
    pass


@click.command()
@click.argument("folder")
@click.pass_context
def read(ctx, folder):
    """
    Get folder details EVE-NG host
    """
    try:
        client = get_client(ctx)
        folder = client.api.get_folder(folder)
        click.echo(display("json", folder))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{str(e)}")


@click.command()
@click.pass_context
def edit(ctx):
    """
    Edit folder on EVE-NG host
    """
    pass


@click.command()
@click.pass_context
def delete(ctx):
    """
    Delete folder on EVE-NG host
    """
    pass


@click.group()
@click.pass_context
def folder(ctx):
    """folder sub commands

    Manage EVE-NG folders
    """
    global client
    client = ctx.obj.client


folder.add_command(ls)
# folder.add_command(create)
folder.add_command(read)
# folder.add_command(edit)
# folder.add_command(delete)
