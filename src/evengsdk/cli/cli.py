# -*- coding: utf-8 -*-
import logging
import os

import click

from evengsdk.client import EvengClient
from evengsdk.cli.folders.commands import folder
from evengsdk.cli.lab.commands import lab
from evengsdk.cli.links.commands import link
from evengsdk.cli.networks.commands import network
from evengsdk.cli.nodes.commands import node
from evengsdk.cli.users.commands import user
from evengsdk.cli.system.commands import system
from evengsdk.cli.version import __version__


LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}  #: a mapping of `verbose` option counts to logging levels


class Context:

    def __init__(self):
        self.verbosity = 0
        self.logger = None
        self.debug = None
        self.active_lab_dir = os.environ.get('EVE_NG_LAB_DIR', '.eve-ng')


PASS_CTX = click.make_pass_decorator(Context, ensure=True)


def verbosity_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(Context)
        state.verbosity = value
        return value
    return click.option('-v', '--verbose', count=True,
                        expose_value=False,
                        help='Enables verbosity.',
                        callback=callback)(f)


def debug_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(Context)
        state.debug = value
        return value
    return click.option('--debug/--no-debug',
                        expose_value=False,
                        help='Enables or disables debug mode.',
                        callback=callback)(f)


def common_options(f):
    f = verbosity_option(f)
    f = debug_option(f)
    return f


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
@common_options
@PASS_CTX
def main(ctx, host, port, username, password):
    """
    EVE-NG CLI commands
    """
<<<<<<< HEAD

    client = EvengClient(host)
    logging_level = (
        LOGGING_LEVELS[ctx.verbosity]
        if ctx.verbosity in LOGGING_LEVELS
        else logging.DEBUG
    )

    if ctx.verbosity > 0:
        client.log = logging.getLogger('evengcli')
        client.log.addHandler(logging.StreamHandler())
        client.log.setLevel(logging_level)
        click.echo(
            click.style(
                f"Verbose logging is enabled. "
                f"(LEVEL={logging.getLogger().getEffectiveLevel()})",
                fg="yellow",
            )
        )

=======

    client = EvengClient(host, log_file='cli.log')
    ctx.password = password


main.add_command(folder)
main.add_command(version)
main.add_command(lab)
main.add_command(link)
main.add_command(node)
main.add_command(user)
main.add_command(system)
main.add_command(network)
