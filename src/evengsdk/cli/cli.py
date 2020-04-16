import click
import os
from evengsdk.client import EvengClient
from evengsdk.cli.lab import lab
from evengsdk.cli.system import system

@click.group()
@click.option('--host', envvar='EVE_NG_HOST', required=True)
@click.option('--username', prompt=True,
              default=lambda: os.environ.get('USER', ''),
              show_default='current user', required=True)
@click.option('--password', prompt=True, hide_input=True,
              envvar='EVE_NG_PASSWORD', required=True)
@click.option('--port', default=80,
              help='HTTP port to connect to. Default is 80')
@click.pass_context
def main(ctx, host, port, username, password):

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    client = EvengClient(host, log_file='cli.log')
    client.login(username=username, password=password)

    ctx.obj = client



main.add_command(lab)
main.add_command(system)
