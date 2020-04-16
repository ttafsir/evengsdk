import click

@click.command()
@click.pass_context
def status(ctx):
    """
    EVE-NG system commands
    """
    client = ctx.obj
    status = client.api.get_server_status()
    click.echo(status)


@click.group()
def system():
    """
    EVE-NG system commands
    """

system.add_command(status)