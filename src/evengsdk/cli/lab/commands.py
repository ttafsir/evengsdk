# -*- coding: utf-8 -*-
import os
import sys
import threading
from itertools import chain
from pathlib import Path
from typing import Dict, List

import click
import yaml

from evengsdk.cli.common import list_sub_command, list_command
from evengsdk.cli.console import cli_print, cli_print_error, cli_print_output, console
from evengsdk.cli.lab.topology import Topology
from evengsdk.cli.utils import get_active_lab, get_client, thread_executor
from evengsdk.client import EvengClient


# https://stackoverflow.com/questions/37310718/mutually-exclusive-option-groups-in-python-click
class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help_str = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help_str + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
                " The API supports editing a single field at a time."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`. You may only set one at a time".format(
                    self.name, ", ".join(self.mutually_exclusive)
                )
            )
        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


client = None
thread_local = threading.local()


def _get_client_session():
    if not hasattr(thread_local, "client"):
        thread_local.client = client
    return thread_local.client


def _get_lab_folder(name: str) -> List[Dict]:
    """Get labs from nested folder structure

    :param name: folder name
    :type name: str
    :return: list of labs
    """
    session = _get_client_session()
    r = session.api.get_folder(name)
    # get the labs from the folder
    labs_from_folder = [r.get("data", {}).get("labs")]
    # let's get labs from nested folders too
    nested_folders = r.get("data", {}).get("folders")
    while len(nested_folders) > 1:
        for folder in nested_folders:
            if folder["name"] == "..":
                continue
            r = session.api.get_folder(f'{folder["path"]}')
            labs_from_folder.append(r.get("data", {}).get("labs"))
    return labs_from_folder


def _get_lab_details(path: str) -> Dict:
    """
    Worker for Thread Executor to parse labs from folders
    """
    session = _get_client_session()
    response = session.api.get_lab(path)
    if response:
        path = path.lstrip("/")
        response["data"].update({"path": "/" + path})
    return response


def _get_all_labs(client: EvengClient) -> List:
    """
    Get all labs from EVE-NG host by parsing all nested folders
    """
    resp = client.api.list_folders()
    root_folders = resp.get("data", {}).get("folders")
    labs_in_root_folder = resp.get("data", {}).get("labs")

    # Get the lab information from all other folders (non-root)
    labs_in_nested_folders = chain(
        *thread_executor(_get_lab_folder, (x["name"] for x in root_folders))
    )
    # flatten the results to single iterable
    # (labs from root folder + labs from nested)
    all_lab_info = chain(labs_in_root_folder, *labs_in_nested_folders)
    return thread_executor(_get_lab_details, (x["path"] for x in all_lab_info))


def create_network_links(
    client: EvengClient, topology: Topology, tasks: List = None
) -> None:
    """
    Create network links
    """
    for link in topology.cloud_links:
        r = client.api.connect_node_to_cloud(topology.path, **link)
        status = "completed" if r["status"] == "success" else "failed"
        console.log(f"{tasks.pop(0)} {status}")


def create_p2p_links(
    client: EvengClient, topology: Topology, tasks: List = None
) -> None:
    """
    Create p2p links
    """
    for link in topology.p2p_links:
        created = client.api.connect_node_to_node(topology.path, **link)
        console.log(f"{tasks.pop(0)} {'completed' if created else 'failed'}")


def create_and_configure_nodes(
    client: EvengClient, topology: Topology, tasks: List = None
) -> None:
    """
    Create and configure nodes
    """
    for node in topology.nodes:
        # create node
        resp = client.api.add_node(topology.path, **node)
        create_result = "completed" if resp["status"] == "success" else "failed"

        # configure node
        if resp["status"] == "success":
            config = topology.get_node_config(node["name"])
            if config:
                node_id = resp["data"]["id"]
                resp = client.api.upload_node_config(
                    topology.path, node_id, config, enable=True
                )
        console.log(f"{tasks.pop(0)} {create_result}")


def create_networks(
    client: EvengClient, topology: Topology, tasks: List = None
) -> None:
    """
    Create networks
    """
    for network in topology.networks:
        resp = client.api.add_lab_network(topology.path, **network)
        success = resp["status"] == "success"
        status = "completed" if success else "failed"
        console.log(f"{tasks.pop(0)} {status}. ID: {resp.get('data', {}).get('id')}")


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.option("--output", type=click.Choice(["json", "text"]), default="json")
@click.pass_context
def read(ctx, path, output):
    """
    Get EVE-NG lab details

    \b
    Examples:
        eve-ng lab read
        eve-ng lab read --path /folder/to/lab.unl
    """
    client = get_client(ctx)
    resp = client.api.get_lab(path)
    cli_print_output(output, resp, header=f"Lab: {resp.get('name')}")


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@list_command
@click.pass_context
def topology(ctx, path, output):
    """
    Retrieve lab topology

    \b
    Examples:
        eve-ng lab topology
    """
    client = get_client(ctx)
    resp = client.api.get_lab_topology(path)
    table_header = [
        ("type", {}),
        ("source", dict(justify="center", style="cyan", no_wrap=True)),
        ("source_type", {}),
        ("source_label", {}),
        ("destination", dict(justify="center", style="magenta", no_wrap=True)),
        ("destination_type", {}),
        ("destination_label", {}),
    ]
    cli_print_output(
        output, resp, header=f"Lab Topology @ {path}", table_header=table_header
    )


@click.command(name="export")
@click.option("--dest", help="destination path", type=click.Path(), default=".")
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def export_lab(ctx, path, dest):
    """
    Export and download lab file as ZIP archive

    \b
    Examples:
        eve-ng lab export
    """
    client = get_client(ctx)
    with console.status("[bold green]Exporting lab..."):
        saved, zipname = client.api.export_lab(path)
        if saved:
            cli_print(f"Lab exported to {zipname}")
    sys.exit(0)


@click.command(name="import")
@click.option("--src", help="source path to ZIP lab file", type=click.Path(exists=True))
@click.option("--folder", default="/", help="folder on EVE-NG to import lab to")
@click.pass_context
def import_lab(ctx, folder, src):
    """
    Import lab into EVE-NG from ZIP archive
    """

    client = get_client(ctx)
    with console.status("[bold green]Importing lab..."):
        resp = client.api.import_lab(src, folder)
        cli_print_output("json", resp)


@list_sub_command
@click.pass_context
def ls(ctx, output):
    """
    List the available labs in EVE-NG host

    \b
    Examples:
        eve-ng lab list
    """
    client = get_client(ctx)
    resp = _get_all_labs(client)
    lab_data = [x["data"] for x in resp] if resp else resp
    table_header = [
        ("Name", dict(justify="right", style="cyan", no_wrap=True)),
        ("Path", {}),
        ("Description", {}),
        ("Author", {}),
        ("Lock", {}),
    ]
    cli_print_output(
        output,
        {"data": lab_data},
        header="Labs",
        table_header=table_header,
        table_title="Labs",
        record_header_key="name",
    )


@click.command()
@click.option("--path", default="/", help="folder to create lab in")
@click.option("--name", help="lab name", required=True)
@click.option("--author", help="lab author")
@click.option("--description", help="lab description")
@click.option("--version", help="lab version")
@click.pass_context
def create(ctx, path: str, author: str, description: str, version: int, name: str):
    """
    Create a new lab

    \b
    Examples:
        eve-ng lab create --name lab1 --author "John Doe" --description "My lab"
    """
    client = get_client(ctx)
    response = client.api.create_lab(
        name=name,
        author=author,
        path=path,
        description=description,
        version=version,
    )
    cli_print_output("text", response)


@click.command()
@click.option(
    "-t",
    "--topology",
    required=True,
    help="Toplogy file to import",
    type=click.Path(exists=True),
)
@click.option(
    "-d",
    "--template-dir",
    default="templates",
    help="Template directory",
    type=click.Path(),
)
@click.pass_context
def create_from_topology(ctx, topology, template_dir):
    """
    Create a new lab

    \b
    Examples:
        eveng lab create-from-topology --topology examples/test_topology.yml
    """
    client = get_client(ctx)

    if not Path(topology).exists():
        raise click.BadParameter(f"Topology file {topology} does not exist")

    topology_data = yaml.safe_load(Path(topology).read_text())
    topology = Topology(topology_data)

    errors = topology.validate()
    if errors:
        cli_print_error(f"Topology validation failed: {errors}")

    # create device configs, if needed
    topology.build_node_configs(template_dir=template_dir)

    try:
        # create lab
        with console.status("[bold green]Creating lab..."):
            resp = client.api.create_lab(**topology.lab)
            if resp["status"] == "success":
                console.log(f"Lab created: {topology.path}")

        # create nodes and apply configs, if needed
        node_tasks = [
            f"node [bold green]{n['name']}[/bold green]" for n in topology.nodes
        ]
        with console.status("[bold green]Creating nodes..."):
            create_and_configure_nodes(client, topology, tasks=node_tasks)

        # create networks
        network_tasks = [f"network {n['name']}" for n in topology.networks]
        with console.status("[bold green]Creating networks..."):
            create_networks(client, topology, tasks=network_tasks)

        # create network links
        link_tasks = [
            f"link [bold green]{link['src']}:{link['src_label']}[/bold green]"
            f" -> [bold green]{link['dst']}[/bold green]"
            for link in topology.cloud_links
        ]
        with console.status("[bold green]Creating links..."):
            create_network_links(client, topology, tasks=link_tasks)

        # create p2p links
        p2p_tasks = [
            f"link [bold green]{link['src']}:{link['src_label']}[/bold green]"
            f" <-> [bold green]{link['dst']}:{link['dst_label']}[/bold green]"
            for link in topology.p2p_links
        ]
        with console.status("[bold green]Creating links..."):
            create_p2p_links(client, topology, tasks=p2p_tasks)

    except Exception as e:
        if "already exists" not in str(e):
            client.api.delete_lab(topology.path)
        cli_print_error(f"Error creating lab: {e}")


@click.command()
@click.option(
    "--author",
    help="lab author",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["version", "description", "body"],
)
@click.option(
    "--description",
    help="lab description.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "version", "body"],
)
@click.option(
    "--version",
    help="lab version.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "description", "body"],
)
@click.option(
    "--body",
    help="long description for lab.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["author", "description", "version"],
)
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def edit(ctx, path: str, **kwargs):
    """Edit a lab on EVE-NG host. EVE-NG API supports updating
    a single field at a time.

    \b
    Examples:
        eve-ng lab edit --author "Tafsir Thiam"
        eve-ng lab edit --body "Lab to demonstrate VXLAN/BGP-EVPN on vEOS"
    """
    edit_param = {k: v for k, v in kwargs.items() if v is not None}
    client = get_client(ctx)
    response = client.api.edit_lab(path, param=edit_param)
    cli_print_output("text", response)


@click.command()
@click.option("--path", default="/", help="folder to create lab in")
@click.pass_context
def delete(ctx, path):
    """
    Delete a lab on EVE-NG host

    \b
    Examples:
        eve-ng lab delete --path /lab1
    """
    client = get_client(ctx)
    response = client.api.delete_lab(path)
    cli_print_output("text", response)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def start(ctx, path):
    """Start all nodes in lab

    \b
    Examples:
        eve-ng lab start
        eve-ng lab start --path /lab1
    """
    client = get_client(ctx)
    response = client.api.start_all_nodes(path)
    cli_print_output("text", response)


@click.command()
@click.option(
    "--path", default=None, callback=lambda ctx, _, v: v or ctx.obj.active_lab
)
@click.pass_context
def stop(ctx, path):
    """
    Stop all nodes in lab

    \b
    Examples:
        eve-ng lab stop
        eve-ng lab stop --path /lab1
    """
    client = get_client(ctx)
    response = client.api.stop_all_nodes(path)
    if response.get("status") and response["status"] == "success":
        close_resp = client.delete("/labs/close")
        cli_print_output("text", close_resp)
    else:
        cli_print_output("text", response)


@click.command(name="show-active")
@click.pass_context
def show_active(ctx):
    """
    Show active lab

    \b
    Examples:
        eve-ng lab show-active
    """
    active_lab = ctx.obj.active_lab or os.environ.get("EVE_NG_PATH")
    cli_print(f"Active Lab: {active_lab}")


@click.command(name="set-active")
@click.option("--path", help="path to lab to activate")
@click.pass_context
def active(ctx, path):
    """
    Set current lab path
    """
    active_lab_dir = ctx.obj.active_lab_dir
    active_lab_filepath = Path(active_lab_dir) / "active"

    # retrieve active lab from either the active lab file or ENV
    if not path:
        if active_lab_filepath.exists():
            active_lab = active_lab_filepath.read_text()
        else:
            active_lab = os.environ.get("EVE_NG_PATH")
        cli_print("Active Lab", style="info")
        cli_print(active_lab)

    # set path option as active lab
    else:
        client.login(username=ctx.obj.username, password=ctx.obj.password)
        # Make sure this is a lab that exists in EVE-NG
        resp = _get_all_labs(client)
        existing_lab = next(
            (lab["data"] for lab in resp if lab["data"]["path"] == path), None
        )
        if not existing_lab:
            msg = click.style(
                f"\nLab @ {path} does not exist or could not be found.", fg="red"
            )
            sys.exit(msg)
        else:
            # TODO: Stop previously active lab?
            active_lab_filepath.write_text(path)
            cli_print(f"Active Lab set to {path}", style="info")


@click.group()
@click.pass_context
def lab(ctx):
    """
    lab sub commands

    Manage EVE-NG labs
    """
    global client
    ctx.obj.active_lab = get_active_lab(ctx.obj.active_lab_dir)
    client = ctx.obj.client


lab.add_command(read)
lab.add_command(ls)
lab.add_command(start)
lab.add_command(stop)
lab.add_command(create)
lab.add_command(edit)
lab.add_command(delete)
lab.add_command(active)
lab.add_command(show_active)
lab.add_command(topology)
lab.add_command(import_lab)
lab.add_command(export_lab)
lab.add_command(create_from_topology)
