# -*- coding: utf-8 -*-
import click

from evengsdk.cli.utils import get_client
from evengsdk.cli.console import cli_print_output


client = None


@click.command(name="list-node-templates")
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def templates(ctx, output):
    """
    list EVE-NG node templates

    \b
    Examples:
        eveng list-node-templates
    """
    client = get_client(ctx)
    resp = client.api.list_node_templates()
    cli_print_output(output, resp, header="Node Templates")


@click.command(name="show-template")
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.argument("template_name")
@click.pass_context
def read_template(ctx, template_name, output):
    """
    get EVE-NG node template details

    \b
    Examples:
        eveng show-template veos
    """
    client = get_client(ctx)
    resp = client.api.node_template_detail(template_name)
    if resp:
        del resp["data"]["options"]["icon"]["list"]
    text_header = f"Node Template: {template_name}"
    cli_print_output(output, resp, header=text_header)


@click.command(name="list-network-types")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def network_types(ctx, output):
    """
    list EVE-NG network types

    \b
    Examples:
        eveng list-network-types
    """
    client = get_client(ctx)
    resp = client.api.list_networks()
    cli_print_output(output, resp, header="Network Types")


@click.command(name="list-user-roles")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def user_roles(ctx, output):
    """
    list EVE-NG user roles

    \b
    Examples:
        eveng list-user-roles
    """
    client = get_client(ctx)
    resp = client.api.list_user_roles()
    table_header = ["Role Name", "Description"]
    cli_print_output(output, resp, header="User Roles", table_header=table_header)


@click.command(name="show-status")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json")
@click.pass_context
def status(ctx, output):
    """View EVE-NG server status

    \b
    Examples:
        eveng show-status
    """
    client = get_client(ctx)
    resp = client.api.get_server_status()
    table_header = ["Component", "Status"]
    cli_print_output(output, resp, header="System", table_header=table_header)
