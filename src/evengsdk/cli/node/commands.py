# -*- coding: utf-8 -*-
from pathlib import Path

import click

from evengsdk.cli.common import list_sub_command
from evengsdk.cli.console import cli_print, cli_print_error, cli_print_output, console
from evengsdk.cli.node import NODE_STATUS_CODES
from evengsdk.cli.utils import get_active_lab, get_client
from evengsdk.exceptions import EvengApiError, EvengHTTPError

client = None


def _get_config(src: Path) -> str:
    """load device config"""
    with open(src, "r") as handle:
        return handle.read()


@click.command("config")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id", required=True)
@click.option("-s", "--src", help="config file to upload", type=click.Path(exists=True))
@click.option("-c", "--config", default=None, help="config to upload", type=str)
@click.pass_context
def upload_config(ctx, node_id, path, src, config):
    """
    Upload device configuration

    \b
    Examples:
        eveng node config -n 1                             # view startup config
        eveng node config -n 4 --config "hostname testing" # upload config from string
        eveng node -config -n 4 -src config.txt            # load config from file
    """
    _client = get_client(ctx)
    try:
        _client.api.get_node(path, node_id)
        if any([src, config]):
            _config = config or _get_config(src)
            resp = _client.api.upload_node_config(path, node_id, config=_config)
            cli_print_output("text", resp)
        else:
            resp = _client.api.get_node_config_by_id(path, node_id)
            if resp["status"] == "success":
                resp = resp.get("data", {}).get("data")
                cli_print(resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id", required=True)
@click.pass_context
def start(ctx, path, node_id):
    """start node in lab

    \b
    Example:
        eve-ng node start -n 4
    """
    _client = get_client(ctx)
    try:
        _client.api.get_node(path, node_id)
        resp = _client.api.start_node(path, node_id)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id", required=True)
@click.pass_context
def stop(ctx, path, node_id):
    """stop node in lab

    \b
    Example:
        eve-ng node stop -n 1
    """
    _client = get_client(ctx)
    try:
        _client.api.get_node(path, node_id)
        resp = _client.api.stop_node(path, node_id)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option("--name", help="node name")
@click.option(
    "--node-type", default="qemu", type=click.Choice(["iol", "qemu", "dynamips"])
)
@click.option("--template", required=True, help="node template to create node from")
@click.option("--image", help="image to boot node with")
@click.option("--ethernet", default=2, help="number of ethernet interfaces.")
@click.option("--serial", default=2, help="number of serial interfaces.")
@click.option(
    "--console-type",
    default="telnet",
    type=click.Choice(["telnet", "vnc"]),
    help="number of serial interfaces.",
)
@click.option("--ram", default=1024, help="RAM for node")
@click.option("--cpu", default=1, help="CPU count for node")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def create(
    ctx,
    path,
    name,
    node_type,
    template,
    image,
    ethernet,
    serial,
    console_type,
    cpu,
    ram,
):
    """Create lab node

    \b
    Example:
        eve-ng node create --name leaf05 --template veos --image veos-4.22.0F
    """
    _client = get_client(ctx)
    node = {
        "name": name,
        "node_type": node_type,
        "template": template,
        "image": image,
        "ethernet": ethernet,
        "serial": serial,
        "console": console_type,
        "cpu": cpu,
        "ram": ram,
    }
    try:
        resp = _client.api.add_node(path, **node)
        cli_print_output("json", resp, header="Node created")
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id")
@click.pass_context
def wipe(ctx, path, node_id):
    """Create lab node

    \b
    Example:
    eve-ng node wipe -n 4   # wipe node with id 4
    eve-ng node wipe        # wipe all nodes
    """
    _client = get_client(ctx)
    try:
        if node_id:
            _client.api.get_node(path, node_id)
            resp = client.api.wipe_node(path, node_id)
        else:
            resp = _client.api.wipe_all_nodes(path)
        cli_print_output("text", resp, header="Node wiped")
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command(name="export")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id")
@click.pass_context
def export_node(ctx, path, node_id):
    """Create export node configuration (save)

    \b
    Example:
    eve-ng node export -n 4   # export node with id 4
    eve-ng node export        # export all nodes
    """
    _client = get_client(ctx)
    try:
        if node_id:
            _client.api.get_node(path, node_id)
            resp = _client.api.export_node(path, node_id)
        else:
            resp = _client.api.export_all_nodes(path)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id", required=True)
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def read(ctx, path, node_id, output):
    """Retrieve lab node details

    \b
    Example:
    eve-ng node read -n 4   # read node with id 4
    """
    _client = get_client(ctx)
    try:
        resp = _client.api.get_node(path, node_id)
        node_name = resp["data"]["name"].upper()
        cli_print_output(output, resp, header=node_name)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("-n", "--node-id", required=True)
@click.pass_context
def delete(ctx, path, node_id):
    """Delete lab node with specified id

    \b
    Example:
    eve-ng node delete -n 4   # delete node with id 4
    """
    _client = get_client(ctx)
    try:
        _client.api.get_node(path, node_id)
        resp = _client.api.delete_node(path, node_id)
        cli_print_output("text", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@list_sub_command
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def ls(ctx, path, output):
    """
    list lab nodes

    \b
    Example:
        eve-ng node list   # list all nodes
    """
    _client = get_client(ctx)
    resp = _client.api.list_nodes(path)

    try:
        node_data = resp.get("data", {})
        if not node_data:
            cli_print_error("No nodes found. Is this lab empty?")

        node_indexes = resp.get("data", {}).keys()
        nodes_list = [(idx, resp["data"][idx]) for idx in node_indexes]

        node_table = []
        for idx, n in nodes_list:
            node_status = n["status"]
            status = NODE_STATUS_CODES[node_status]
            table_row = {
                "id": idx,
                "name": n["name"],
                "url": n["url"],
                "image": n["image"],
                "template": n["template"],
                "status": f"{status[0]} {status[1]}",
                "console": n["console"],
                "ram": n["ram"],
                "cpu": n["cpu"],
            }
            node_table.append(table_row)

        table_header = [
            ("ID", dict(justify="right", style="cyan", no_wrap=True)),
            ("Name", {}),
            ("Url", {}),
            ("Image", {}),
            ("Template", {}),
            ("Status", {}),
            ("Console", {}),
            ("RAM", {}),
            ("CPU", {}),
        ]

        table_data = {"data": node_table}
        cli_print_output(
            output, table_data, table_header=table_header, table_title=f"Nodes @ {path}"
        )
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@click.group()
@click.pass_context
def node(ctx):
    """node sub commands

    Manage EVE-NG lab nodes
    """
    global client

    # get active lab path from eve-ng dir or ENV
    ctx.obj.active_lab = get_active_lab(ctx.obj.active_lab_dir)
    client = ctx.obj.client


node.add_command(ls)
node.add_command(create)
node.add_command(read)
node.add_command(delete)
node.add_command(start)
node.add_command(stop)
node.add_command(wipe)
node.add_command(export_node)
node.add_command(upload_config)
