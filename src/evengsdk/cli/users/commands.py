# -*- coding: utf-8 -*-
import click


@click.command(name="list")
@click.pass_context
def ls(ctx):
    """
    list EVE-NG users
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)


@click.command()
@click.pass_context
def create(ctx):
    """
    Create EVE-NG user
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)


@click.command()
@click.option("--user-id", help="user ID to delete")
@click.pass_context
def read(ctx, user_id):
    """
    Retrieve EVE-NG user details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)


@click.command()
@click.option("--user-id", help="user ID to delete")
@click.pass_context
def edit(ctx, user_id):
    """
    Update EVE-NG user
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)


@click.command()
@click.option("--user-id", help="user ID to delete")
@click.pass_context
def delete(ctx, user_id):
    """
    Delete EVE-NG user
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)


@click.group()
@click.pass_context
def user(ctx):
    """user sub commands

    Manage EVE-NG users
    """
    global client
    client = ctx.obj.client


user.add_command(ls)
user.add_command(create)
user.add_command(read)
user.add_command(edit)
user.add_command(delete)
