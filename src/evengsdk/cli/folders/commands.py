# -*- coding: utf-8 -*-
import click


@click.command(name='list')
@click.pass_context
def ls(ctx):
    """
    List folders on EVE-NG host
    """
    pass


@click.command()
@click.pass_context
def create(ctx):
    """
    Create folder on EVE-NG host
    """
    pass


@click.command()
@click.pass_context
def read(ctx):
    """
    Get folder details EVE-NG host
    """
    pass


@click.command()
@click.pass_context
def edit(ctx):
    """
    Edit folder on EVE-NG host
    """
    pass


@click.command()
@click.pass_context
def delete(ctx):
    """
    Delete folder on EVE-NG host
    """
    pass


@click.group()
@click.pass_context
def folder(ctx):
    """
    Manage EVE-NG folders
    """
    global client
    client = ctx.obj.client


folder.add_command(ls)
folder.add_command(create)
folder.add_command(read)
folder.add_command(edit)
folder.add_command(delete)
