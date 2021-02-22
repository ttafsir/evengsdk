# -*- coding: utf-8 -*-
import json
from pathlib import Path
import os
import sys

import click

from evengsdk.exceptions import EvengHTTPError
from evengsdk.cli.helpers import (
    to_human_readable,
    display_status,
    get_active_lab
)
from evengsdk.cli.nodes import NODE_STATUS_CODES, NODE_STATUS_COLOR


client = None


def get_configs(src):
    path = Path(src)
    configs = []
    for filename in os.listdir(path):
        filepath = Path(filename)
        hostname = filepath.stem
        fullpath = os.path.join(src, filepath)
        with open(fullpath, 'r') as handle:
            stream = handle.read()
            configs.append({'hostname': hostname, 'config': stream})
    return configs


def get_config(src):
    """
    load device config
    """
    with open(src, 'r') as handle:
        stream = handle.read()
        return stream


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.option('--src', required=True, type=click.Path(exists=True))
@click.pass_context
def upload_config(ctx, node_id, path, src):
    """
    Upload device configuration
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    config = get_config(src)
    client.api.upload_node_config(
        path, node_id,
        config=config,
        enable=True)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def start(ctx, path, node_id):
    """
    start node in lab.
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.start_node(path, node_id)
    display_status(resp)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def stop(ctx, path, node_id):
    """
    stop node in lab
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.stop_node(path, node_id)
    display_status(resp)


@click.command()
@click.option('--name', help="node name")
@click.option('--node-type',
              default="qemu",
              type=click.Choice(['iol', 'qemu', 'dynamips']))
@click.option('--template',
              required=True,
              help="node template to create node from")
@click.option('--image',
              help="image to boot node with")
@click.option('--ethernet',
              default=2,
              help="number of ethernet interfaces.")
@click.option('--serial',
              default=2,
              help="number of serial interfaces.")
@click.option('--console',
              default="telnet",
              type=click.Choice(['telnet', 'vnc']),
              help="number of serial interfaces.")
@click.option('--ram', default=1024, help="RAM for node")
@click.option('--cpu', default=1, help="CPU count for node")
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
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
    """
    Create lab node
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    node = {
        'name': name,
        'node_type': node_type,
        'template': template,
        'image': image,
        'ethernet': ethernet,
        'serial': serial,
        'console': console,
        'cpu': cpu,
        'ram': ram
    }
    resp = client.api.add_node(path, **node)
    if resp.get('id'):
        click.secho(json.dumps(resp), fg='green')
        sys.exit()
    sys.exit(click.style(resp, fg='red'))


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def wipe(ctx, path, node_id):
    """
    Create lab node
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    try:
        client.api.get_node(path, node_id)
        resp = client.api.wipe_node(path, node_id)
        display_status(resp)
        sys.exit()
    except EvengHTTPError as e:
        if 'Cannot find node' in str(e):
            sys.exit(click.style(
                'could not find specified node in lab', fg='red'))
        else:
            sys.exit(click.style(str(e), fg='red'))
    except Exception as e:
        sys.exit(click.style(str(e), fg='red'))


@click.command(name='export')
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def export_node(ctx, path, node_id):
    """
    Create export node configuration (save)
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    try:
        client.api.get_node(path, node_id)
        resp = client.api.export_node(path, node_id)
        display_status(resp)
        sys.exit()
    except EvengHTTPError as e:
        if 'Cannot find node' in str(e):
            sys.exit(click.style(
                'could not find specified node in lab', fg='red'))
        else:
            sys.exit(click.style(str(e), fg='red'))
    except Exception as e:
        sys.exit(click.style(str(e), fg='red'))


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def read(ctx, path, node_id):
    """
    Retrieve lab node details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    node = client.api.get_node(path, node_id)

    click.secho(node['name'].upper(), fg='yellow', dim=True)
    for output in to_human_readable(node):
        click.echo(output)
    click.echo()


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--node-id', required=True)
@click.pass_context
def delete(ctx, path, node_id):
    """
    Retrieve lab node details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    try:
        client.api.get_node(path, node_id)
        resp = client.api.delete_node(path, node_id)
        display_status(resp)
        sys.exit()
    except EvengHTTPError as e:
        if 'Cannot find node' in str(e):
            sys.exit(click.style(
                'could not find specified node in lab', fg='red'))
        else:
            sys.exit(click.style(str(e), fg='red'))
    except Exception as e:
        sys.exit(click.style(str(e), fg='red'))


@click.command(name='list')
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def ls(ctx, path):
    """
    list lab nodes
    """

    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.list_nodes(path)
    if resp:
        node_indexes = resp.keys()
        nodes_list = [(idx, resp[idx]) for idx in node_indexes]

        node_table = []
        for idx, n in nodes_list:
            status_code = n['status']
            table_row = {
                'id': idx,
                'name': n['name'],
                'url': n['url'],
                'image': n['image'],
                'template': n['template'],
                'uuid': n['uuid'],
                'status': click.style(NODE_STATUS_CODES[status_code],
                                      fg=NODE_STATUS_COLOR[status_code])
            }
            node_table.append(table_row)

        click.secho(f'Nodes @ {path}', fg='blue')

        keys_to_display = "id name url image uuid template status".split()
        for node in node_table:
            click.secho(node['name'].upper(), fg='yellow', dim=True)
            for output in to_human_readable(node, keys=keys_to_display):
                click.echo(output)
            click.echo()


@click.group()
@click.pass_context
def node(ctx):
    """
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
