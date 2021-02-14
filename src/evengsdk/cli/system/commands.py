# -*- coding: utf-8 -*-
import click
from evengsdk.cli.helpers import to_human_readable


client = None


@click.command()
@click.pass_context
def list_templates(ctx):
    """
    list EVE-NG node templates
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    pass


@click.command()
@click.pass_context
def read_template(ctx):
    """
    get EVE-NG node template details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    pass


@click.command()
@click.pass_context
def list_network_types(ctx):
    """
    list EVE-NG network types
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    pass


@click.command()
@click.pass_context
def list_user_roles(ctx):
    """
    list EVE-NG user roles
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    pass


@click.command()
@click.pass_context
def status(ctx):
    """
    EVE-NG server status and details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    status = client.api.get_server_status()

    click.secho('System', fg='blue')
    for output in to_human_readable(status):
        click.echo(output)


@click.group()
@click.pass_context
def system(ctx):
    """
    EVE-NG system commands
    """
    global client
    client = ctx.obj.client


system.add_command(status)
system.add_command(list_templates)
system.add_command(read_template)
system.add_command(list_network_types)
system.add_command(list_user_roles)
