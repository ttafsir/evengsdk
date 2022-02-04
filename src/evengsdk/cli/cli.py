# -*- coding: utf-8 -*-
import logging
import os

import click

from evengsdk.client import EvengClient
from evengsdk.cli.console import cli_print
from evengsdk.cli.folders.commands import folder
from evengsdk.cli.lab.commands import lab
from evengsdk.cli.node.commands import node
from evengsdk.cli.users.commands import user
from evengsdk.cli.system.commands import (
    status,
    templates,
    read_template,
    user_roles,
    network_types,
)
from evengsdk.cli.version import __version__


ERROR = click.style("ERROR: ", fg="red")
UNKNOWN_ERROR = click.style("UNKNOWN ERROR: ", fg="red")
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
        self.active_lab_dir = os.environ.get("EVE_NG_LAB_DIR", ".eve-ng")
        self.error_fmt = ERROR
        self.unknown_error_fmt = UNKNOWN_ERROR


PASS_CTX = click.make_pass_decorator(Context, ensure=True)


def verbosity_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(Context)
        state.verbosity = value
        return value

    return click.option(
        "-v",
        "--verbose",
        count=True,
        expose_value=False,
        help="Enables verbosity.",
        callback=callback,
    )(f)


def debug_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(Context)
        state.debug = value
        return value

    return click.option(
        "--debug/--no-debug",
        expose_value=False,
        help="Enables or disables debug mode.",
        callback=callback,
    )(f)


def common_options(f):
    f = verbosity_option(f)
    f = debug_option(f)
    return f


@click.group()
@click.version_option(version=__version__)
@click.option("--host", envvar="EVE_NG_HOST", required=True)
@click.option(
    "--username",
    prompt=True,
    envvar="EVE_NG_USERNAME",
    default=lambda: os.environ.get("USER", ""),
    show_default="current user",
    required=True,
)
@click.option(
    "--password", prompt=True, hide_input=True, envvar="EVE_NG_PASSWORD", required=True
)
@click.option(
    "--port",
    default=80,
    envvar="EVE_NG_PORT",
    help="HTTP port to connect to. Default is 80",
)
@click.option(
    "--protocol",
    default="http",
    envvar="EVE_NG_PROTOCOL",
    help="Protocol to use. Default is http",
)
@click.option("--insecure", is_flag=False, envvar="EVE_NG_INSECURE", help="Disable SSL")
@click.option(
    "--verify", default=True, envvar="EVE_NG_SSL_VERIFY", help="Verify SSL certificate"
)
@common_options
@PASS_CTX
def main(ctx, host, port, username, password, verify, protocol, insecure):
    """CLI application to manage EVE-NG objects"""

    client = EvengClient(
        host,
        port=port,
        ssl_verify=verify,
        protocol=protocol,
        disable_insecure_warnings=insecure,
    )

    logging_level = (
        LOGGING_LEVELS[ctx.verbosity]
        if ctx.verbosity in LOGGING_LEVELS
        else logging.ERROR
    )

    if ctx.verbosity > 0:
        client.log = logging.getLogger("evengcli")
        client.log.addHandler(logging.StreamHandler())
        client.log.setLevel(logging_level)
        cli_print(
            f"Verbose logging is enabled. " f"(LEVEL={client.log.getEffectiveLevel()})",
            style="warning",
        )

    ctx.client = client
    ctx.host = host
    ctx.username = username
    ctx.password = password


main.add_command(folder)
main.add_command(lab)
main.add_command(node)
main.add_command(user)
main.add_command(status)
main.add_command(templates)
main.add_command(read_template)
main.add_command(user_roles)
main.add_command(network_types)
