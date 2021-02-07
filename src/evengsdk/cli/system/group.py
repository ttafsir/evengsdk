# -*- coding: utf-8 -*-
import click
from evengsdk.cli.helpers import to_human_readable


@click.command()
@click.pass_context
def status(ctx):
    """
    EVE-NG system commands
    """
    client = ctx.obj['CLIENT']
    status = client.api.get_server_status()

    click.secho('System', fg='blue')

    for output in to_human_readable(status):
        click.echo(output)


@click.group()
def system():
    """
    EVE-NG system commands
    """


system.add_command(status)
