# -*- coding: utf-8 -*-
import click
from pprint import PrettyPrinter
from tabulate import tabulate


@click.command()
@click.pass_context
def status(ctx):
    """
    EVE-NG system commands
    """
    client = ctx.obj['CLIENT']
    status = client.api.get_server_status()
    pp = PrettyPrinter(indent=2)
    pp.pprint(status)


@click.group()
def system():
    """
    EVE-NG system commands
    """

system.add_command(status)