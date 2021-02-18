# -*- coding: utf-8 -*-
from itertools import chain
import json
import os
from pathlib import Path
import threading
from typing import Dict, List
import sys

import click
from evengsdk.client import EvengClient
from evengsdk.cli.helpers import (
    to_human_readable,
    thread_executor,
    display_status,
    get_active_lab
)
from evengsdk.inventory import build_inventory


client = None
thread_local = threading.local()


def _get_client_session():
    if not hasattr(thread_local, "client"):
        thread_local.client = client
    return thread_local.client


def _get_lab_folder(name: str) -> List:
    """Get labs from nested folder structure

    Args:
        name (str): name of folder

    Returns:
        [list]: list of labs from folder(s)
    """
    session = _get_client_session()
    r = session.api.get_folder(name)

    # get the labs from the folder
    labs_from_folder = list()
    labs_from_folder.append(r.get('labs'))

    # let's get labs from nested folders too
    while len(nested_folders := r.get('folders')) > 1:
        for folder in nested_folders:
            # skip the '..' folder as it refers to the parent
            if folder["name"] == "..":
                continue
            else:
                r = session.api.get_folder(f'{folder["path"]}')
                labs_from_folder.append(r.get('labs'))
    return labs_from_folder


def _get_lab_details(path: str) -> Dict:
    """
    Worker for Thread Executor to parse labs from folders
    """
    session = _get_client_session()
    response = session.api.get_lab(path)
    if response:
        path = path.lstrip('/')
        response.update({'path': '/' + path})
    return response


def _get_all_labs(client: EvengClient) -> List:
    resp = client.api.list_folders()

    root_folders = resp['folders']
    labs_in_root_folder = resp.get('labs')

    # Get the lab information from all other folders (non-root)
    labs_in_nested_folders = chain(*thread_executor(
        _get_lab_folder, (x['name'] for x in root_folders)
    ))
    # flatten the results to single iterable
    # (labs from root folder + labs from nested)
    all_lab_info = chain(labs_in_root_folder, *labs_in_nested_folders)

    # Get the actual details for Each lab using the lab paths
    lab_details = thread_executor(
        _get_lab_details, (x['path'] for x in all_lab_info)
    )
    return lab_details


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option(
    '-f', '--output-format',
    default="pretty",
    help="output display format. [pretty, json]"
)
@click.pass_context
def read(ctx, path, output_format):
    """
    Get EVE-NG lab details
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    try:
        lab = client.api.get_lab(path)

        # Display output - JSON
        if output_format == "json":
            click.secho(json.dumps(lab, indent=2))
            sys.exit()

        # Display output
        click.secho(f'Lab {path}', fg='blue')
        click.secho(lab['name'].upper(), fg='yellow', dim=True)
        for output in to_human_readable(lab):
            click.echo(output)
        sys.exit()

    except Exception as e:
        click.secho(e, fg='red')
        sys.exit(e)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option(
    '-f', '--output-format',
    default="pretty",
    help="output display format. [pretty, json]"
)
@click.pass_context
def topology(ctx, path, output_format):
    """
    Retrieve lab topology
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    try:
        response = client.api.get_lab_topology(path)

        # Display output - JSON
        if output_format == "json":
            click.secho(json.dumps(response, indent=2))
            sys.exit()

        click.secho(f'Lab Topology @ {path}', fg='blue')
        if response:
            for link in response:
                for output in to_human_readable(link):
                    click.echo(output)
                click.echo()
        sys.exit()
    except Exception as e:
        sys.exit(str(e))


@click.command(name='export')
@click.option('--dest',
              help='destination path',
              type=click.Path(),
              default='.')
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def export_lab(ctx, path, dest):
    """
    Export and download lab file as ZIP archive
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.export_lab(path)
    if resp:
        name, content = resp
        full_filepath = dest / Path(name)
        full_filepath.write_bytes(content)
        click.secho(f"Success: {str(full_filepath.resolve())}", fg="green")
    else:
        sys.exit("Error: Could not download lab")


@click.command(name='import')
@click.option('--src',
              help='source path to ZIP lab file',
              type=click.Path(exists=True))
@click.option('--folder',
              default='/',
              help="folder on EVE-NG to import lab to")
@click.pass_context
def import_lab(ctx, folder, src):
    """
    Import lab into EVE-NG from ZIP archive
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.import_lab(Path(src), folder)
    display_status(resp)


@click.command(name='list')
@click.option(
    '-f', '--output-format',
    default="pretty",
    help="output display format. [pretty, json]"
)
@click.pass_context
def ls(ctx, output_format):
    """
    List the available labs in EVE-NG host
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    lab_details = _get_all_labs(client)

    # Display output - JSON
    if output_format == "json":
        click.secho(json.dumps(lab_details, indent=2))
        sys.exit()

    # Display output - Human readable
    click.secho('Labs', fg='blue')
    for lab in lab_details:
        click.secho(lab['name'].upper(), fg='yellow', dim=True)
        for output in to_human_readable(lab):
            click.echo(output)
        click.echo()
    sys.exit()


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def links(ctx, path):
    """
    Get EVE-NG lab topology
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.get_lab_topology(path)

    # Display output
    click.secho('Links', fg='blue')
    for link in resp:
        click.secho(
            f"{link['source']} <> {link['destination']}",
            fg='yellow',
            dim=True
        )
        for output in to_human_readable(link):
            click.echo(output)
        click.echo()


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def networks(ctx, path):
    """
    Get EVE-NG lab topology
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.list_lab_networks(path)
    networks = [_dict for key, _dict in resp.items()]

    # Display output
    click.secho('Networks', fg='blue')
    for net in networks:
        click.secho(f"{net['name']}", fg='yellow', dim=True)
        for output in to_human_readable(net):
            click.echo(output)
        click.echo()


@click.command()
@click.option('--path', default="/", help='folder to create lab in')
@click.option('--name', help='lab name')
@click.option('--author', help='lab author')
@click.option('--description', help='lab description')
@click.option('--version', help='lab version')
@click.pass_context
def create(
    ctx,
    path: str,
    author: str,
    description: str,
    version: int,
    name: str
):
    """
    create a new lab
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    response = client.api.create_lab(
        name=name,
        author=author,
        path=path,
        description=description,
        version=version
    )
    display_status(response)


@click.command()
@click.option('--path', default="/", help='folder to create lab in')
@click.option('--name', help='lab name')
@click.option('--author', help='lab author')
@click.option('--description', help='lab description')
@click.option('--version', help='lab version')
@click.pass_context
def edit(
    ctx,
    path: str,
    author: str,
    description: str,
    version: int,
    name: str
):
    """
    edit a lab on EVE-NG host
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    response = client.api.edit_lab(
        name=name,
        author=author,
        full_path=path,
        description=description,
        version=version
    )
    display_status(response)


@click.command()
@click.option('--path', default="/", help='folder to create lab in')
@click.option('--name', help='lab name')
@click.pass_context
def delete(ctx, path, name):
    """
    edit a lab on EVE-NG host
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    response = client.api.delete_lab(name=name, path=path)
    display_status(response)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def start(ctx, path):
    """
    Start all nodes in lab
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    response = client.api.start_all_nodes(path)
    display_status(response)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def stop(ctx, path):
    """
    Stop all nodes in lab
    """
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    response = client.api.stop_all_nodes(path)
    display_status(response)


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('-o', '--output', help="Output filename.")
@click.pass_context
def inventory(ctx, path, output):
    """
    generate inventory file (INI).
    """
    eve_host = ctx.obj.host
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.list_nodes(path)
    node_indexes = resp.keys()
    nodes_list = [resp[idx] for idx in node_indexes]

    inventory = build_inventory(eve_host, path, nodes_list)
    if output:
        with open(output, 'w') as handle:
            handle.write(inventory)
    sys.exit()


@click.command(name="active")
@click.option('--path', help='path to active lab')
@click.pass_context
def active(ctx, path):
    """
    show current lab path
    """
    active_lab_dir = ctx.obj.active_lab_dir
    active_lab_filepath = Path(active_lab_dir) / 'active'

    # retrieve active lab from either the active lab file or ENV
    if not path:
        if active_lab_filepath.exists():
            active_lab = active_lab_filepath.read_text()
        else:
            active_lab = os.environ.get('EVE_NG_path')
        click.secho('Active Lab', fg='blue')
        click.echo(active_lab)

    # set path option as active lab
    else:
        client.login(
            username=ctx.obj.username,
            password=ctx.obj.password
        )
        # Make sure this is a lab that exists in EVE-NG
        labs = _get_all_labs(client)
        existing_lab = next((
            lab for lab in labs
            if lab['path'] == path), None
        )
        if not existing_lab:
            msg = click.style(
                f"\nLab @ {path} does not exist or could not be found.",
                fg="red"
            )
            sys.exit(msg)
        else:
            # TODO: Stop previously active lab?
            active_lab_filepath.write_text(path)
            click.secho(f'Active Lab set to {path}', fg='green')


@click.group()
@click.pass_context
def lab(ctx):
    """
    EVE-NG lab commands
    """
    global client

    # get active lab path from eve-ng dir or ENV
    ctx.obj.active_lab = get_active_lab(ctx.obj.active_lab_dir)

    client = ctx.obj.client


lab.add_command(read)
lab.add_command(ls)
lab.add_command(start)
lab.add_command(stop)
lab.add_command(create)
lab.add_command(edit)
lab.add_command(delete)
lab.add_command(inventory)
lab.add_command(active)
lab.add_command(topology)
lab.add_command(import_lab)
lab.add_command(export_lab)
