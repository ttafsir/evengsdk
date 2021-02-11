# -*- coding: utf-8 -*-
import sys

import click

from evengsdk.cli.helpers import to_human_readable


def exit_with_error(msg=""):
    if not msg:
        sys.exit(1)
    sys.exit(msg)


@click.command(name='list')
@click.argument('lab-path')
@click.pass_context
def ls(ctx, lab_path):
    """
    List lab links
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.get_lab_topology(lab_path)
    if not resp['status'].lower() == 'success':
        exit_with_error(resp['message'])

    # Display output
    click.secho('Links', fg='blue')
    for link in resp:
        click.secho(
            f"{link['source']} <> {link['destination']}",
            fg='yellow', dim=True
        )
        for output in to_human_readable(link):
            click.echo(output)
        click.echo()
        sys.exit()


@click.group()
@click.pass_context
def link(ctx):
    """
    View and manage lab links
    """
    global client
    client = ctx.obj.client


link.add_command(ls)
