# -*- coding: utf-8 -*-
import click

from evengsdk.cli.common import list_sub_command
from evengsdk.cli.console import cli_print_output
from evengsdk.cli.utils import get_client


@list_sub_command
@click.pass_context
def ls(ctx, output):
    """
    List folders on EVE-NG host

    \b
    Examples:
        eve-ng folder list
    """
    client = get_client(ctx)
    resp = client.api.list_folders()
    folder_data = resp["data"]["folders"]
    table_header = [
        ("Name", dict(justify="right", style="cyan", no_wrap=True)),
        ("Path", {}),
    ]
    cli_print_output(
        output,
        {"data": folder_data},
        header="Folders",
        table_header=table_header,
        table_title="Folders",
    )


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

    \b
    Examples:
        eve-ng folder read /path/to/folder
    """
    client = get_client(ctx)
    resp = client.api.get_folder(folder)
    cli_print_output("json", resp)


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
