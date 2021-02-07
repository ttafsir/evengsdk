# -*- coding: utf-8 -*-
from itertools import chain
import threading

import click
from tabulate import tabulate
from evengsdk.cli.helpers import to_human_readable, thread_executor
from evengsdk.cli.lab.generate import generate
from evengsdk.inventory import build_inventory


client = None
thread_local = threading.local()


def _get_client_session():
    if not hasattr(thread_local, "client"):
        thread_local.client = client
    return thread_local.client


def _get_lab_folder(name):
    session = _get_client_session()
    r = session.api.get_folder(name)
    labs_from_folder = list()
    labs_from_folder.append(r.get('labs'))
    while len(nested_folders := r.get('folders')) > 1:
        for folder in nested_folders:
            if folder["name"] == "..":
                continue
            else:
                r = session.api.get_folder(f'{folder["path"]}')
                labs_from_folder.append(r.get('labs'))
    return labs_from_folder


def _get_lab_details(lab_path: str):
    session = _get_client_session()
    r = session.api.get_lab(lab_path)
    if r:
        path = lab_path.lstrip('/')
        r.update({'path': '/' + path})
    return r


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def info(ctx, lab_path):
    """
    Get EVE-NG lab details
    """
    client = ctx.obj['CLIENT']
    details = client.api.get_lab(lab_path)
    click.echo(tabulate([details], headers="keys", tablefmt="grid"))


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
def upload(ctx):
    pass


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def export(ctx, lab_path):
    """
    Export and download lab file as .zip archive
    """
    client = ctx.obj['CLIENT']
    resp = client.api.export_lab(lab_path)
    click.echo(resp)


@click.command()
@click.pass_context
def ls(ctx):
    """
    List the available labs in EVE-NG host
    """
    global client
    client = ctx.obj['CLIENT']
    resp = client.api.list_folders()

    root_folders = resp['folders']
    labs_in_root_folder = resp.get('labs')

    # Get the lab information from all other folders (non-root)
    labs_in_nested_folders = chain(*thread_executor(
        _get_lab_folder, (x['name'] for x in root_folders)
    ))
    # flatten the results to single iterable
    # (labs from root folder + labs from nested)
    all_lab_info = chain(*labs_in_root_folder, *labs_in_nested_folders)

    # Get the actual details for Each lab using the lab paths
    lab_details = thread_executor(
        _get_lab_details, (x['path'] for x in all_lab_info)
    )

    # Display output
    click.secho('Labs', fg='blue')
    for lab in lab_details:
        click.secho(lab['name'].upper(), fg='yellow', dim=True)
        for output in to_human_readable(lab):
            click.echo(output)
        click.echo()


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def links(ctx, lab_path):
    """
    Get EVE-NG lab topology
    """
    client = ctx.obj['CLIENT']

    links = client.api.get_lab_topology(lab_path)
    click.echo(tabulate(links, headers="keys", tablefmt="fancy_grid"))


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def networks(ctx, lab_path):
    """
    Get EVE-NG lab topology
    """
    client = ctx.obj['CLIENT']

    resp = client.api.list_lab_networks(lab_path)
    networks = [_dict for key, _dict in resp.items()]
    click.echo(tabulate(networks, headers="keys", tablefmt="fancy_grid"))


@click.command()
@click.option('--lab-path', default="/",
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def start(ctx, lab_path):
    """
    Start all nodes in lab
    """
    client = ctx.obj['CLIENT']
    status = client.api.start_all_nodes(lab_path)
    click.echo(status)


@click.command()
@click.option('--lab-path', default="/",
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.pass_context
def stop(ctx, lab_path):
    """
    Stop all nodes in lab
    """
    client = ctx.obj['CLIENT']
    status = client.api.stop_all_nodes(lab_path)
    click.echo(status)


@click.command()
@click.option('--lab-path', default="/",
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.option('-o', '--output', help="Output filename.")
@click.pass_context
def inventory(ctx, lab_path, output):
    """
    generate inventory file (INI).
    """
    eve_host = ctx.obj['HOST']
    client = ctx.obj['CLIENT']
    resp = client.api.list_nodes(lab_path)
    node_indexes = resp.keys()
    nodes_list = [resp[idx] for idx in node_indexes]

    inventory = build_inventory(eve_host, lab_path, nodes_list)
    if output:
        with open(output, 'w') as handle:
            handle.write(inventory)


@click.group()
@click.pass_context
def lab(ctx):
    """
    EVE-NG lab commands
    """


lab.add_command(info)
lab.add_command(ls)
lab.add_command(start)
lab.add_command(stop)
lab.add_command(inventory)
lab.add_command(links)
lab.add_command(networks)
lab.add_command(export)
lab.add_command(generate)
