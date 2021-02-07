# -*- coding: utf-8 -*-
import os

import click

from evengsdk.client import EvengClient
from evengsdk.cli.lab.group import lab
from evengsdk.cli.node.group import node
from evengsdk.cli.system.group import system


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
@click.pass_context
def main(ctx, host, port, username, password):

    # ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    client = EvengClient(host, log_file='cli.log')
    client.login(username=username, password=password)

    ctx.obj['CLIENT'] = client
    ctx.obj['HOST'] = host


main.add_command(lab)
main.add_command(node)
main.add_command(system)
