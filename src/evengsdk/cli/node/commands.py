# -*- coding: utf-8 -*-
from pathlib import Path
import os
import sys
from typing import List, Dict

import click

from evengsdk.exceptions import EvengHTTPError, EvengApiError
from evengsdk.cli.utils import get_client, get_active_lab
from evengsdk.plugins.display import display
from evengsdk.cli.node import NODE_STATUS_CODES, NODE_STATUS_COLOR


client = None


def _get_configs(src: Path) -> List[Dict]:
    path = Path(src)
    configs = []
    for filename in os.listdir(path):
        filepath = Path(filename)
        hostname = filepath.stem
        fullpath = os.path.join(src, filepath)
        with open(fullpath, "r") as handle:
            stream = handle.read()
            configs.append({"hostname": hostname, "config": stream})
    return configs


def _get_config(src: Path) -> str:
    """load device config"""
    with open(src, "r") as handle:
        return handle.read()


@click.command()
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
        eveng node upload-config -n 4 -config "hostname testing" # upload config from string
        eveng node upload-config -n 4 -src config.txt            # load config from file
    """
    try:
        print(path)
        client = get_client(ctx)
        _config = config or _get_config(src)
        resp = client.api.upload_node_config(path, node_id, config=_config, enable=True)
        click.echo(display("json", resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        resp = client.api.start_node(path, node_id)
        click.echo(display("json", resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        resp = client.api.stop_node(path, node_id)
        click.echo(display("json", resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    "--console",
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
    console,
    cpu,
    ram,
):
    """Create lab node

    \b
    Example:
        eveng node create --name leaf05 --template veos --image veos-4.22.0F
    """
    try:
        client = get_client(ctx)
        node = {
            "name": name,
            "node_type": node_type,
            "template": template,
            "image": image,
            "ethernet": ethernet,
            "serial": serial,
            "console": console,
            "cpu": cpu,
            "ram": ram,
        }
        resp = client.api.add_node(path, **node)
        click.echo(display("json", resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        if node_id:
            client.api.get_node(path, node_id)
            resp = client.api.wipe_node(path, node_id)
        else:
            resp = client.api.wipe_all_nodes(path)
        click.echo(display("json", resp))
    except EvengHTTPError as e:
        if "Cannot find node" in str(e):
            sys.exit(click.style("could not find specified node in lab", fg="red"))
        else:
            sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        if node_id:
            client.api.get_node(path, node_id)
            resp = client.api.export_node(path, node_id)
        else:
            resp = client.api.export_all_nodes(path)
        click.echo(display("json", resp))
    except EvengHTTPError as e:
        if "Cannot find node" in str(e):
            sys.exit(click.style("could not find specified node in lab", fg="red"))
        else:
            sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        resp = client.api.get_node(path, node_id)
        node = resp.get("data", {})
        if output != "json":
            click.secho(node["name"].upper(), fg="bright_blue", dim=True)
        click.echo(display(output, node))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
    try:
        client = get_client(ctx)
        client.api.get_node(path, node_id)
        resp = client.api.delete_node(path, node_id)
        click.echo(display("text", resp.get("message")))
    except EvengHTTPError as e:
        if "Cannot find node" in str(e):
            sys.exit(click.style("could not find specified node in lab", fg="red"))
        else:
            sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


@click.command(name="list")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def ls(ctx, path, output):
    """
    list lab nodes

    \b
    Example:
        eve-ng node list   # list all nodes
    """
    try:
        client = get_client(ctx)
        resp = client.api.list_nodes(path)
        node_indexes = resp.get("data", {}).keys()
        nodes_list = [(idx, resp["data"][idx]) for idx in node_indexes]

        node_table = []
        for idx, n in nodes_list:
            status_code = n["status"]
            table_row = {
                "id": idx,
                "name": n["name"],
                "url": n["url"],
                "image": n["image"],
                "template": n["template"],
                "uuid": n["uuid"],
                "status": click.style(
                    NODE_STATUS_CODES[status_code], fg=NODE_STATUS_COLOR[status_code]
                ),
            }
            node_table.append(table_row)

        if output != "json":
            click.secho(f"Nodes @ {path}", fg="blue")

        keys_to_display = "id name url image uuid template status".split()
        click.echo(display(output, node_table, header=keys_to_display))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg="bright_white")
        sys.exit(f"{ctx.obj.error_fmt}{msg}")
    except Exception as e:
        sys.exit(f"{ctx.obj.unknown_error_fmt}{e}")


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
