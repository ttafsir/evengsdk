# -*- coding: utf-8 -*-
from itertools import chain
import os
from pathlib import Path
import threading
from typing import Dict, List
import sys

import click
from evengsdk.client import EvengClient
from evengsdk.cli.helpers import (
    get_client,
    thread_executor,
    get_active_lab
)
from evengsdk.exceptions import EvengApiError, EvengHTTPError
from evengsdk.inventory import build_inventory
from evengsdk.plugins.display import display


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
@click.option('--output',
              type=click.Choice(['json', 'text']),
              default='text')
@click.pass_context
def read(ctx, path, output):
    """
    Get EVE-NG lab details
    """
    try:
        client = get_client(ctx)
        lab = client.api.get_lab(path)
        click.secho(lab['name'].upper(), fg='yellow')
        click.echo(display(output, lab))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('--output',
              type=click.Choice(['json', 'text', 'table']),
              default='text')
@click.pass_context
def topology(ctx, path, output):
    """
    Retrieve lab topology
    """
    try:
        client = get_client(ctx)
        resp = client.api.get_lab_topology(path)

        click.secho(f'Lab Topology @ {path}', fg='bright_blue')
        header = [
            'type',
            'source',
            'source_type',
            'source_label',
            'destination',
            'destination_type',
            'destination_label'
        ]
        click.echo(display(output, resp, header=header))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


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
    try:
        client = get_client(ctx)
        resp = client.api.export_lab(path)

        # get name and content from response
        name, content = resp
        full_filepath = dest / Path(name)

        # save file
        full_filepath.write_bytes(content)

        success_message = f"Success: {str(full_filepath.resolve())}"
        click.secho(display('text', success_message))

    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


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
    try:
        client = get_client(ctx)
        resp = client.api.import_lab(Path(src), folder)
        click.echo(display('text', resp))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command(name='list')
@click.option('--output',
              type=click.Choice(['json', 'text']),
              default='text')
@click.pass_context
def ls(ctx, output):
    """
    List the available labs in EVE-NG host
    """
    try:
        client = get_client(ctx)
        lab_details = _get_all_labs(client)

        # Display output - Human readable
        click.secho('Labs', fg='bright_blue')

        # header for table output
        header = ['author', 'filename', 'id', 'version', 'path']

        click.echo(
            display(output, lab_details, header=header, record_header='name')
        )
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


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
    Create a new lab
    """
    try:
        client = get_client(ctx)
        response = client.api.create_lab(
            name=name,
            author=author,
            path=path,
            description=description,
            version=version
        )
        click.echo(display('text', response))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


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
    Edit a lab on EVE-NG host
    """
    try:
        client = get_client(ctx)
        response = client.api.edit_lab(
            name=name,
            author=author,
            full_path=path,
            description=description,
            version=version
        )
        click.echo(display('text', response))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command()
@click.option('--path', default="/", help='folder to create lab in')
@click.option('--name', help='lab name')
@click.pass_context
def delete(ctx, path, name):
    """
    Delete a lab on EVE-NG host
    """
    try:
        client = get_client(ctx)
        response = client.api.delete_lab(name=name, path=path)
        click.echo(display('text', response))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def start(ctx, path):
    """
    Start all nodes in lab
    """
    try:
        client = get_client(ctx)
        response = client.api.start_all_nodes(path)
        click.echo(display('text', response))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.pass_context
def stop(ctx, path):
    """
    Stop all nodes in lab
    """
    try:
        client = get_client(ctx)
        response = client.api.stop_all_nodes(path)
        if response.get('status') and response['status'] == 'success':
            close_resp = client.delete('/labs/close')
            click.echo(display('text', close_resp))
        else:
            click.echo(display('text', response))
    except (EvengHTTPError, EvengApiError) as e:
        msg = click.style(str(e), fg='bright_white')
        sys.exit(f'{ctx.obj.error_fmt}{msg}')
    except Exception as e:
        sys.exit(f'{ctx.obj.unknown_error_fmt}{str(e)}')


@click.command()
@click.option('--path', default=None,
              callback=lambda ctx, params, v: v if v else ctx.obj.active_lab)
@click.option('-w', '--write', help="Output filename.")
@click.pass_context
def inventory(ctx, path, write):
    """
    generate inventory file (INI).
    """
    eve_host = ctx.obj.host
    client.login(username=ctx.obj.username, password=ctx.obj.password)
    resp = client.api.list_nodes(path)
    node_indexes = resp.keys()
    nodes_list = [resp[idx] for idx in node_indexes]

    inventory = build_inventory(eve_host, path, nodes_list)
    if write:
        with open(write, 'w') as handle:
            handle.write(inventory)
    sys.exit()


@click.command(name="show-active")
@click.pass_context
def show_active(ctx):
    """
    Show active lab
    """
    title = click.style('Active Lab: ', fg='bright_blue')
    active_lab = ctx.obj.active_lab or os.environ.get('EVE_NG_PATH')
    click.echo(f'{title}{active_lab}')


@click.command(name="set-active")
@click.option('--path', help='path to lab to activate')
@click.pass_context
def active(ctx, path):
    """
    Set current lab path
    """
    active_lab_dir = ctx.obj.active_lab_dir
    active_lab_filepath = Path(active_lab_dir) / 'active'

    # retrieve active lab from either the active lab file or ENV
    if not path:
        if active_lab_filepath.exists():
            active_lab = active_lab_filepath.read_text()
        else:
            active_lab = os.environ.get('EVE_NG_PATH')
        click.secho('Active Lab', fg='bright_blue')
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
lab.add_command(show_active)
lab.add_command(topology)
lab.add_command(import_lab)
lab.add_command(export_lab)
