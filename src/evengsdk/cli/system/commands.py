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
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def templates(ctx, output):
    """
    list EVE-NG node templates
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_node_templates()
        if output != "json":
            click.secho("Node Templates", fg="blue")
        click.echo(display(output, resp.get("data", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{e}")


@click.command(name="show-template")
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.argument("template_name")
@click.pass_context
def read_template(ctx, template_name, output):
    """
    get EVE-NG node template details
    """
    try:
        client = get_client(ctx)
        resp = client.api.node_template_detail(template_name)
        if output != "json":
            click.secho(f"Node Template: {template_name}", fg="blue")
        click.echo(display(output, resp.get("data", {})))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{e}")


@click.command(name="list-network-types")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def network_types(ctx, output):
    """
    list EVE-NG network types
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_networks()
        if output != "json":
            click.secho("Network Types", fg="blue")
        table_header = ["Network Type", "Name"]
        click.echo(display(output, resp.get("data", {}), header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{e}")


@click.command(name="list-user-roles")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def user_roles(ctx, output):
    """
    list EVE-NG user roles
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_user_roles()
        if output != "json":
            click.secho("User Roles", fg="blue")
        table_header = ["Role Name", "Description"]
        click.echo(display(output, resp.get("data", {}), header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{e}")


@click.command(name="show-status")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def status(ctx, output):
    """View EVE-NG server status"""
    try:
        client = get_client(ctx)
        resp = client.api.get_server_status()
        if output != "json":
            click.secho("System", fg="blue")
        table_header = ["Component", "Status"]
        click.echo(display(output, resp.get("data", {}), header=table_header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ERROR}{msg}")
    except Exception as e:
        sys.exit(f"{UNKNOWN_ERROR}{e}")
