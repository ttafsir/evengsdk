# -*- coding: utf-8 -*-
import sys

import click

from evengsdk.cli.helpers import to_human_readable


@click.command(name='list')
@click.argument('lab-path', envvar='EVE_NG_LAB_PATH')
@click.pass_context
def ls(ctx, lab_path):
    """
    List lab networks
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.list_lab_networks(lab_path)
    networks = [_dict for key, _dict in resp.items()]

    # Display output
    click.secho('Networks', fg='blue')
    for net in networks:
        click.secho(f"{net['name']}", fg='yellow', dim=True)
        for output in to_human_readable(net):
            click.echo(output)
        click.echo()
        sys.exit()


@click.group()
@click.argument('lab-path', envvar='EVE_NG_LAB_PATH')
@click.pass_context
def create(ctx):
    """
    Create EVE-NG lab network
    """
    pass


@click.group()
@click.option('--net-id', help='network ID to retrieve')
@click.argument('lab-path', envvar='EVE_NG_LAB_PATH')
@click.pass_context
def read(ctx, net_id):
    """
    Retrieve EVE-NG lab network
    """
    pass


@click.group()
@click.option('--net-id', help='network ID to retrieve')
@click.argument('lab-path', envvar='EVE_NG_LAB_PATH')
@click.pass_context
def edit(ctx, net_id):
    """
    Edit EVE-NG lab network
    """
    pass


@click.group()
@click.option('--net-id', help='network ID to retrieve')
@click.argument('lab-path', envvar='EVE_NG_LAB_PATH')
@click.pass_context
def delete(ctx, net_id):
    """
    Delete EVE-NG lab network
    """
    pass


@click.group()
@click.pass_context
def network(ctx):
    """
    View and manage EVE-NG lab networks
    """
    global client
    client = ctx.obj.client


network.add_command(ls)
network.add_command(create)
network.add_command(read)
network.add_command(edit)
network.add_command(delete)
