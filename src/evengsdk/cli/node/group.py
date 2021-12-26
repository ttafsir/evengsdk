# -*- coding: utf-8 -*-
from pathlib import Path
import os
import click

from tabulate import tabulate

from evengsdk.cli.node import NODE_STATUS_CODES, NODE_STATUS_COLOR


def get_configs(src):
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


def get_config(src):
    """
    load device config
    """
    with open(src, "r") as handle:
        stream = handle.read()
        return stream


@click.command()
@click.option("--lab-path", required=True)
@click.option("--node-id", required=True)
@click.option("--src", required=True, type=click.Path(exists=True))
@click.pass_context
def upload_config(ctx, node_id, lab_path, src):
    """
    Upload device configuration
    """
    client = ctx.obj["CLIENT"]
    config = get_config(src)
    client.api.upload_node_config(lab_path, node_id, config=config, enable=True)


@click.command()
@click.option("--lab-path", required=True)
@click.option("--node-id")
@click.pass_context
def start(ctx, lab_path, node_id):
    """
    start node in lab.
    """
    client = ctx.obj["CLIENT"]
    resp = client.api.start_node(lab_path, node_id)
    click.echo(resp)


@click.command()
@click.option("--lab-path", required=True)
@click.option("--node-id")
@click.pass_context
def stop(ctx, lab_path, node_id):
    """
    stop node in lab.
    """
    client = ctx.obj["CLIENT"]
    resp = client.api.stop_node(lab_path, node_id)
    if resp.get("status") and resp["status"] == "success":
        close_resp = client.delete("/labs/close")
        click.echo(close_resp)


@click.command()
@click.option("--lab-path", required=True)
@click.pass_context
def ls(ctx, lab_path):
    """
    list lab nodes
    """

    client = ctx.obj["CLIENT"]

    resp = client.api.list_nodes(lab_path)
    if resp:
        node_indexes = resp.keys()
        nodes_list = [(idx, resp[idx]) for idx in node_indexes]

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
        click.echo(tabulate(node_table, headers="keys", tablefmt="fancy_grid"))


@click.group()
@click.pass_context
def node(ctx):
    """
    EVE-NG lab commands
    """


node.add_command(ls)
node.add_command(start)
node.add_command(stop)
node.add_command(upload_config)
