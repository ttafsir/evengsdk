# -*- coding: utf-8 -*-
import click

from evengsdk.cli.common import list_command
from evengsdk.cli.utils import get_client
from evengsdk.cli.console import cli_print_output


client = None


@list_command
@click.command(name="list-node-templates")
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

    if output == "table":
        table_data = []
        style = {"true": "green", "false": "red"}
        for key, value in resp["data"].items():
            template_image_available = "true" if "missing" not in value else "false"
            this_style = style[template_image_available]
            table_data.append(
                {
                    "name": key,
                    "description": value,
                    "available": f"[{this_style}]{template_image_available}[/{this_style}]",
                }
            )

        table_header = [
            ("Name", dict(justify="right", style="cyan", no_wrap=True)),
            ("Description", {}),
            ("Available", dict(justify="center")),
        ]
        cli_print_output(
            output,
            {"data": table_data},
            table_header=table_header,
            table_title="Node Templates",
        )
    else:
        cli_print_output("json", resp)


@click.command(name="show-template")
@click.argument("template_name")
@click.pass_context
def read_template(ctx, template_name):
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
    cli_print_output("json", resp, header=text_header)


@list_command
@click.command(name="list-network-types")
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
    if output == "table":
        table_data = [
            {"name": key, "description": value} for key, value in resp["data"].items()
        ]

        table_header = [
            ("Name", dict(justify="right", style="cyan", no_wrap=True)),
            ("Description", {}),
        ]
        cli_print_output(
            output,
            {"data": table_data},
            table_header=table_header,
            table_title="Network Types",
        )
    cli_print_output(output, resp, header="Network Types")


@list_command
@click.command(name="list-user-roles")
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
    if output == "table":
        table_data = [
            {"name": key, "description": value} for key, value in resp["data"].items()
        ]

        table_header = [
            ("Name", dict(justify="right", style="cyan", no_wrap=True)),
            ("Description", {}),
        ]
        cli_print_output(
            output,
            {"data": table_data},
            table_header=table_header,
            table_title="User Roles",
        )
    cli_print_output("json", resp, header="User Roles")


@list_command
@click.command(name="show-status")
@click.pass_context
def status(ctx, output):
    """View EVE-NG server status

    \b
    Examples:
        eveng show-status
    """
    client = get_client(ctx)
    resp = client.api.get_server_status()
    if output == "table":
        table_data = [
            {"name": key, "value": value} for key, value in resp["data"].items()
        ]

        table_header = [
            ("Name", dict(justify="right", style="cyan", no_wrap=True)),
            ("Value", {}),
        ]
        cli_print_output(
            output,
            {"data": table_data},
            table_header=table_header,
            table_title="Server Status",
        )
    cli_print_output(output, resp, header="System")
