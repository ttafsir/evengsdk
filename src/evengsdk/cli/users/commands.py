# -*- coding: utf-8 -*-
import click

from evengsdk.cli.common import list_sub_command
from evengsdk.cli.console import cli_print_output, console
from evengsdk.cli.utils import get_client
from evengsdk.exceptions import EvengApiError, EvengHTTPError


def user_sub_command(subcommand):
    """common options for user subcommands"""
    for decorator in reversed(
        (
            click.option("--name", "-n", help="User's name"),
            click.option("--username", "-u", help="login username", required=True),
            click.option("--password", "-p", help="login password"),
            click.option(
                "--expiration",
                "-e",
                help="expiration date for accout (UNIX timestamp). -1 means never expire. default is -1.",
                default=-1,
            ),
            click.option("--role", "-r", help="user role", default="user"),
            click.option("--email", help="user email"),
        )
    ):
        subcommand = decorator(subcommand)
    return subcommand


@list_sub_command
@click.pass_context
def ls(ctx, output):
    """
    list EVE-NG users

    \b
    Examples:
        eve-ng user list
    """
    _client = get_client(ctx)
    resp = _client.api.list_users()
    try:
        users = [user_dict for _, user_dict in resp["data"].items()]
        table_header = [
            ("Username", dict(justify="right", style="cyan", no_wrap=True)),
            ("Name", dict(justify="left", style="cyan", no_wrap=True)),
            ("Email", {}),
            ("Expiration", {}),
            ("Role", {}),
            ("IP", {}),
            ("Folder", {}),
            ("Lab", {}),
            ("Pod", {}),
        ]
        cli_print_output(
            output,
            {"data": users},
            header="User",
            table_header=table_header,
            table_title="Users",
        )
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@user_sub_command
@click.pass_context
def create(ctx, **options):
    """
    Create EVE-NG user

    \b
    Examples:
        eve-ng user create -u user1 -p password1 -e -1 --role user --name "John Doe"
    """
    _client = get_client(ctx)
    try:
        resp = _client.api.add_user(**options)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option("-u", "--username", help="user ID to get details for", required=True)
@click.pass_context
def read(ctx, username):
    """
    Retrieve EVE-NG user details
    """
    _client = get_client(ctx)
    try:
        resp = _client.api.get_user(username)
        cli_print_output("json", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@user_sub_command
@click.pass_context
def edit(ctx, **options):
    """
    Update EVE-NG user
        eve-ng user edit -u user1 --name "Jane Doe"
    """
    _client = get_client(ctx)
    try:
        username = options.pop("username")
        resp = _client.api.edit_user(username, data=options)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option("-u", "--username", help="User's name", required=True)
@click.pass_context
def delete(ctx, username):
    """
    Delete EVE-NG user
    """
    _client = get_client(ctx)
    try:
        _client.api.get_user(username)
        resp = _client.api.delete_user(username)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.group()
@click.pass_context
def user(ctx):
    """user sub commands

    Manage EVE-NG users
    """


user.add_command(ls)
user.add_command(create)
user.add_command(read)
user.add_command(edit)
user.add_command(delete)
