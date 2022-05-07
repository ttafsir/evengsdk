# -*- coding: utf-8 -*-
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml

from evengsdk.cli.common import list_command, list_sub_command
from evengsdk.cli.console import cli_print, cli_print_error, cli_print_output, console
from evengsdk.cli.lab.topology import Topology
from evengsdk.cli.utils import get_active_lab, get_client, thread_executor
from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengApiError, EvengHTTPError


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


def _get_nested_labs(folders: List, session: EvengClient, labs: List = None) -> List:
    """recursively get all nested labs from folders"""
    if len(folders) == 1 and folders[0]["name"] in ("..", "/"):
        return []

    if labs is None:
        labs = []

    for folder in folders:
        if folder["name"] == "..":
            continue
        resp = session.api.get_folder(f'{folder["path"]}')
        nested_labs = resp.get("data", {}).get("labs")
        folders = resp.get("data", {}).get("folders")
        labs.append(nested_labs)
        if len(folders) >= 1:
            _get_nested_labs(folders, session, labs)
    return labs


def _get_lab_folder(name: str) -> List[Dict]:
    """Get labs from nested folder structure

    :param name: folder name
    :type name: str
    :return: list of labs
    """
    session = _get_client_session()
    resp = session.api.get_folder(name)

    # get the labs from the folder
    labs_from_folder = [resp.get("data", {}).get("labs")]

    # let's get labs from nested folders too
    sub_folders = resp.get("data", {}).get("folders")
    labs_from_sub_folders = _get_nested_labs(sub_folders, session)

    # flatten the results to single iterable
    labs_from_folder.extend(labs_from_sub_folders)
    return labs_from_folder


def _get_lab_details(path: str) -> Dict:
    """
    Worker for Thread Executor to parse labs from folders
    """
    session = _get_client_session()
    response = session.api.get_lab(path)
    if response:
        path = path.lstrip("/")
        response["data"].update({"path": f"/{path}"})
    return response


def _get_all_labs(client: EvengClient) -> List:
    """
    Get all labs from EVE-NG host by parsing all nested folders
    """
    with console.status("[bold green]Retrieving labs...") as status:
        status.update("Retrieving folders...")
        resp = client.api.list_folders()
        root_folders = resp.get("data", {}).get("folders")
        labs_in_root_folder = resp.get("data", {}).get("labs")

        # Get the lab information from all other folders (non-root)
        status.update("Retrieving nested folders...")

        # The EVE-NG PRO version shows labs in the root folder and The "Running"
        # folder if the lab is running. We need to skip the "Running" folder to
        # avoid duplicates.
        labs_in_nested_folders = chain(
            *thread_executor(
                _get_lab_folder,
                (x["name"] for x in root_folders if x["name"] != "Running"),
            )
        )
        # flatten the results to single iterable
        # (labs from root folder + labs from nested)
        all_lab_info = chain(labs_in_root_folder, *labs_in_nested_folders)
        status.update("Retrieving lab details from all folders...")
        return thread_executor(_get_lab_details, (x["path"] for x in all_lab_info))


def _create_network_link_worker(link: Dict, path: str, tasks: List) -> None:
    """
    Worker for Thread Executor to create network links
    """
    client = _get_client_session()
    r = client.api.connect_node_to_cloud(path, **link)
    status = "completed" if r["status"] == "success" else "failed"
    console.log(f"{tasks.pop(0)} {status}")


def create_network_links(topology: Topology, tasks: List = None) -> None:
    """
    Create network links
    """
    path = topology.path
    thread_executor(
        lambda link: _create_network_link_worker(link, path, tasks),
        topology.cloud_links,
    )


def _create_p2p_link_worker(link: Dict, path: str, tasks: List) -> None:
    """
    Worker for Thread Executor to create p2p links
    """
    client = _get_client_session()
    created = client.api.connect_node_to_node(path, **link)
    console.log(f"{tasks.pop(0)} {'completed' if created else 'failed'}")


def create_p2p_links(topology: Topology, tasks: List = None) -> None:
    """
    Create p2p links
    """
    path = topology.path
    thread_executor(
        lambda link: _create_p2p_link_worker(link, path, tasks),
        topology.p2p_links,
    )


def _create_node_workder(
    node: Dict, path: str, config: Optional[str], tasks: List = None
) -> None:
    """
    Worker for Thread Executor to create nodes
    """
    client = _get_client_session()
    resp = client.api.add_node(path, **node)
    create_result = "completed" if resp["status"] == "success" else "failed"

    # configure node
    if resp["status"] == "success" and config:
        node_id = resp["data"]["id"]
        resp = client.api.upload_node_config(path, node_id, config)
        if resp["status"] == "success":
            if config := topology.get_node_config(node["name"]):
                node_id = resp["data"]["id"]
                resp = client.api.upload_node_config(topology.path, node_id, config)
                if resp["status"] == "success":
                    client.api.enable_node_config(topology.path, node_id)

    if tasks:
        console.log(f"{tasks.pop(0)} {create_result}")


def create_and_configure_nodes(topology: Topology, tasks: List = None) -> None:
    """
    Create and configure nodes
    """
    path = topology.path
    params_set = [
        (node, path, topology.get_node_config(node["name"]), tasks)
        for node in topology.nodes
    ]
    with ThreadPoolExecutor(max_workers=5) as exec:
        exec.map(lambda p: _create_node_workder(*p), params_set)


def _create_network_worker(network: Dict, path: str, tasks: List) -> None:
    """
    Worker for Thread Executor to create p2p links
    """
    client = _get_client_session()
    resp = client.api.add_lab_network(path, **network)
    success = resp["status"] == "success"
    status = "completed" if success else "failed"
    console.log(f"{tasks.pop(0)} {status}. ID: {resp.get('data', {}).get('id')}")


def create_networks(topology: Topology, tasks: List = None) -> None:
    """
    Create networks
    """
    path = topology.path
    thread_executor(
        lambda net: _create_network_worker(net, path, tasks),
        topology.networks,
    )


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
    _client = get_client(ctx)
    try:
        resp = _client.api.get_lab(path)
        cli_print_output(output, resp, header=f"Lab: {resp.get('name')}")
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        resp = _client.api.get_lab_topology(path)
        if not resp.get("data"):
            cli_print_error("No Topology information available. Is the lab empty?")

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
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        with console.status("[bold green]Exporting lab..."):
            saved, zipname = _client.api.export_lab(path)
            if saved:
                cli_print(f"Lab exported to {zipname}")
    except (EvengHTTPError, EvengApiError) as err:
        if "Cannot remove UUID from exported" in str(err):
            err = "Cannot export lab. Does the lab exist?"
        console.print_error(err)


@click.command(name="import")
@click.option("--src", help="source path to ZIP lab file", type=click.Path(exists=True))
@click.option("--folder", default="/", help="folder on EVE-NG to import lab to")
@click.pass_context
def import_lab(ctx, folder, src):
    """
    Import lab into EVE-NG from ZIP archive
    """

    _client = get_client(ctx)
    try:
        with console.status("[bold green]Importing lab..."):
            resp = _client.api.import_lab(src, folder)
            cli_print_output("json", resp)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


@list_sub_command
@click.pass_context
def ls(ctx, output):
    """
    List the available labs in EVE-NG host

    \b
    Examples:
        eve-ng lab list
    """
    _client = get_client(ctx)
    try:
        resp = _get_all_labs(_client)
        lab_data = [x["data"] for x in resp] if resp else resp

        if not lab_data:
            cli_print_error("No labs found. Please create or import a lab first.")

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
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        response = _client.api.create_lab(
            name=name,
            author=author,
            path=path,
            description=description,
            version=version,
        )
        cli_print_output("text", response)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)

    if not Path(topology).exists():
        raise click.BadParameter(f"Topology file {topology} does not exist")

    topology_data = yaml.safe_load(Path(topology).read_text())
    topology = Topology(topology_data)

    if errors := topology.validate():
        cli_print_error(f"Topology validation failed: {errors}")

    # create device configs, if needed
    topology.build_node_configs(template_dir=template_dir)

    try:
        # create lab
        with console.status("[bold green]Creating lab..."):
            resp = _client.api.create_lab(**topology.lab)
            if resp["status"] == "success":
                console.log(f"Lab created: {topology.path}")

        # create nodes and apply configs, if needed
        node_tasks = [
            f"node [bold green]{n['name']}[/bold green]" for n in topology.nodes
        ]
        with console.status("[bold green]Creating nodes..."):
            create_and_configure_nodes(topology, tasks=node_tasks)

        # create networks
        network_tasks = [f"network {n['name']}" for n in topology.networks]
        with console.status("[bold green]Creating networks..."):
            create_networks(topology, tasks=network_tasks)

        # create network links
        link_tasks = [
            f"link [bold green]{link['src']}:{link['src_label']}[/bold green]"
            f" -> [bold green]{link['dst']}[/bold green]"
            for link in topology.cloud_links
        ]
        with console.status("[bold green]Creating links..."):
            create_network_links(topology, tasks=link_tasks)

        # create p2p links
        p2p_tasks = [
            f"link [bold green]{link['src']}:{link['src_label']}[/bold green]"
            f" <-> [bold green]{link['dst']}:{link['dst_label']}[/bold green]"
            for link in topology.p2p_links
        ]
        with console.status("[bold green]Creating links..."):
            create_p2p_links(topology, tasks=p2p_tasks)

        sys.exit(0)
    except (EvengHTTPError, EvengApiError) as err:
        if "already exists" not in str(err):
            _client.api.delete_lab(topology.path)
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        response = _client.api.edit_lab(path, param=edit_param)
        cli_print_output("text", response)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        with console.status("[bold green]wiping nodes...") as status:
            # wipe nodes
            resp1 = _client.api.wipe_all_nodes(path)
            console.log(f"{resp1['status']}: {resp1['message']}")
            # stop all nodes
            status.update("[bold green]closing lab...")
            resp2 = _client.api.close_lab()
            console.log(f"{resp2['status']}: {resp2['message']}")
            # delete the lab
            status.update("[bold green]deleting lab...")
            response = _client.api.delete_lab(path)
            cli_print_output("text", response)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        response = _client.api.start_all_nodes(path)
        cli_print_output("text", response)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
    _client = get_client(ctx)
    try:
        response = _client.api.stop_all_nodes(path)
        if response.get("status") and response["status"] == "success":
            close_resp = _client.delete("/labs/close")
            cli_print_output("text", close_resp)
        else:
            cli_print_output("text", response)
    except (EvengHTTPError, EvengApiError) as err:
        console.print_error(err)


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
