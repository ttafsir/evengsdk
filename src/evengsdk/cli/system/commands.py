# -*- coding: utf-8 -*-
import sys

import click

from evengsdk.cli.utils import get_client
from evengsdk.plugins.display import display
from evengsdk.exceptions import EvengHTTPError, EvengApiError


client = None
ERROR = click.style("ERROR: ", fg="red")
UNKNOWN_ERROR = click.style("UNKNOWN ERROR: ", fg="red")


@click.command(name="list-node-templates")
@click.option("--include-missing", is_flag=True, default=False)
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="text")
@click.pass_context
def templates(ctx, output, include_missing):
    """
    list EVE-NG node templates
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_node_templates(include_missing=include_missing)
        click.secho("Node Templates", fg="blue")
        table_header = ["Template", "Description"]
        click.echo(display(output, resp, header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{str(e)}")


@click.command(name="show-template")
@click.option("--output", type=click.Choice(["json", "text"]), default="text")
@click.argument("template_name")
@click.pass_context
def read_template(ctx, template_name, output):
    """
    get EVE-NG node template details
    """
    try:
        client = get_client(ctx)
        resp = client.api.node_template_detail(template_name)
        click.secho(f"Node Template: {template_name}", fg="blue")
        click.echo(display(output, resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{str(e)}")


@click.command(name="list-network-types")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="text")
@click.pass_context
def network_types(ctx, output):
    """
    list EVE-NG network types
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_networks()
        click.secho("Network Types", fg="blue")
        table_header = ["Network Type", "Name"]
        click.echo(display(output, resp, header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{str(e)}")


@click.command(name="list-user-roles")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="text")
@click.pass_context
def user_roles(ctx, output):
    """
    list EVE-NG user roles
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_user_roles()
        click.secho("User Roles", fg="blue")
        table_header = ["Role Name", "Description"]
        click.echo(display(output, resp, header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{str(e)}")


@click.command(name="show-status")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="text")
@click.pass_context
def status(ctx, output):
    """View EVE-NG server status"""
    try:
        client = get_client(ctx)
        status = client.api.get_server_status()
        click.secho("System", fg="blue")
        table_header = ["Component", "Status"]
        click.echo(display(output, status, header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{str(e)}")


# @click.group()
# @click.pass_context
# def system(ctx):
#     """
#     EVE-NG system commands
#     """
#     global client
#     client = ctx.obj.client


# system.add_command(status)
# system.add_command(templates)
# system.add_command(read_template)
# system.add_command(network_types)
# system.add_command(user_roles)
