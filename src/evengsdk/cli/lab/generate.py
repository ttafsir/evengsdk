# -*- coding: utf-8 -*-
from collections import defaultdict
import json
import re

import click
import yaml


ALPHANUM_RE = r"[^\W\d_]+|\d+"


def build_lab_details(lab):
    return {'name': lab['name'],
            'author': lab['author'],
            'description': lab['description'],
            'filename': lab['filename']}


def build_node_details(nodes: dict) -> list:
    keys = (
        'console id left top icon image'
        'name ram template type config ethernet'
    )
    filtered_nodes = []
    for _, node in nodes.items():
        filtered_node = {k: v for k, v in node.items() if k in keys.split()}
        filtered_nodes.append(filtered_node)
    return filtered_nodes


def build_link_details(links: list) -> list:
    cloud_filters = "source source_label type"
    p2p_filters = "destination destination_label source source_label type"

    p2p_links = [x for x in links
                 if (x['source_type'] == 'node'
                     and x['destination_type'] == 'node')]

    cloud_links = [
        x for x in links
        if (x['source_type'] == 'network'
            or x['destination_type'] == 'network')
    ]

    filtered_clouds = defaultdict(list)

    for cloud in cloud_links:
        new_cloud = {k: v for k, v in cloud.items()
                     if k in cloud_filters.split()}
        cloud_id_regex = re.findall(ALPHANUM_RE, cloud['destination'])

        if len(cloud_id_regex) > 1:
            cloud_id = cloud_id_regex[-1]
            filtered_clouds[cloud_id].append(new_cloud)

    filtered_links = []
    for link in p2p_links:
        new_link = {k: v for k, v in link.items() if k in p2p_filters.split()}
        filtered_links.append(new_link)

    return {
        'point_to_point': filtered_links,
        'cloud': dict(filtered_clouds)
    }


def build_network_details(networks: dict) -> list:
    keys = "id name left top"
    visible_networks = [v for k, v in networks.items()
                        if int(v['visibility']) == 1]

    filtered_networks = []
    for net in visible_networks:
        new_dict = {}
        for k, v in net.items():
            if k in keys.split():
                new_dict.update({k: v})
        filtered_networks.append(new_dict)
    return filtered_networks


def build_topology(lab, nodes, links, networks):

    topology = {
        'lab': build_lab_details(lab),
        'nodes': build_node_details(nodes),
        'links': build_link_details(links),
        'networks': build_network_details(networks)
    }
    return topology


@click.command()
@click.option('--lab-path', required=True,
              help='Path to the lab in EVE-NG host. ex: /MYLAB.unl')
@click.option('-o', '--output-file',
              default='topology',
              help="output file destination")
@click.option('--yaml/--json')
@click.pass_context
def topology(ctx, lab_path, output_file, **kwargs):
    """
    Get lab topology
    """
    client = ctx.obj['CLIENT']

    lab_details = client.api.get_lab(lab_path)
    lab_nodes = client.api.list_nodes(lab_path)
    lab_links = client.api.get_lab_topology(lab_path)
    lab_networks = client.api.list_lab_networks(lab_path)

    topology = build_topology(lab_details, lab_nodes, lab_links, lab_networks)
    if kwargs.get('json'):
        content = json.dumps(topology)
        ext = 'json'
    else:
        content = yaml.safe_dump(topology)
        ext = 'yml'

    with open(f'{output_file}.{ext}', 'w') as handle:
        handle.write(content)


@click.command()
def inventory():
    pass


@click.group()
def generate():
    """
    Generate lab artifacts
    """


generate.add_command(topology)
generate.add_command(inventory)
