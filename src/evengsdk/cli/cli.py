# -*- coding: utf-8 -*-
import os

import click

from evengsdk.client import EvengClient
from evengsdk.cli.lab.group import lab
from evengsdk.cli.node.group import node
from evengsdk.cli.system.group import system
from evengsdk.cli.version import __version__


class Context:

    def __init__(self):
        self.verbose = False
        self.logger = None


PASS_CTX = click.make_pass_decorator(Context, ensure=True)


@click.command()
def version():
    """Get the library version."""
    click.echo(click.style(f"{__version__}", bold=True))


@click.group()
@click.option('--host', envvar='EVE_NG_HOST', required=True)
@click.option('--username', prompt=True,
              envvar='EVE_NG_USERNAME',
              default=lambda: os.environ.get('USER', ''),
              show_default='current user', required=True)
@click.option('--password', prompt=True, hide_input=True,
              envvar='EVE_NG_PASSWORD', required=True)
@click.option('--port', default=80,
              help='HTTP port to connect to. Default is 80')
@PASS_CTX
def main(ctx, host, port, username, password):
    """
    EVE-NG CLI commands
    """

    client = EvengClient(host, log_file='cli.log')
    ctx.client = client
    ctx.host = host
    ctx.username = username
    ctx.password = password


main.add_command(version)
main.add_command(lab)
main.add_command(node)
main.add_command(system)
