# Introduction

`Evengsdk` is a Python library with command-line utilities to manage EVE-NG servers and network topologies.

`Evengsdk` provides the flexibility to your EVE-NG hosts and topologies in different ways:

* **evengsdk**: The `evengsdk` library provides a set of classes to manage EVE-NG servers and network topologies.
* **eve-ng CLI**: The eve-ng command-line utility provides a set of commands to manage EVE-NG servers and network topologies without the need to write Python code.
* **Topology Builder**: The topology builder lets you build a topology from a YAML declaration file.

## Requirements

Evengsdk works with both the community and PRO versions of EVE-NG. You will need a working instance of EVE-NG to use Evengsdk.

Evengsdk requires Python 3.8 or later.

## Installation

You can install Evengsdk from PyPI with pip:

```sh
pip install eve-ng
```

## Quick Start

### Basic Usage

You can interact with the EVE-NG API through the `client.api` interface

```python
from evengsdk.client import EvengClient
from pprint import pprint

client = EvengClient("10.246.32.254", log_file="test.log")
client.login(username="admin", password="eve")

resp = client.api.list_node_templates()
```

### Build a Topology

```python
from evengsdk.client import EvengClient


client = EvengClient("10.246.32.254", log_file="test.log", ssl_verify=False, protocol="https")
client.disable_insecure_warnings()  # disable warnings for self-signed certificates
client.login(username="admin", password="eve")
client.set_log_level("DEBUG")

# create a lab
lab = {"name": "test_lab", "description": "Test Lab", "path": "/"}
resp = client.api.create_lab(**lab)
if resp['status'] == "success":
  print("lab created successfully.")

# we need the lab path to create objects in the lab
lab_path = f"{lab['path']}{lab['name']}.unl"

# create management network
mgmt_cloud = {"name": "eve-mgmt", "network_type": "pnet1"}
client.api.add_lab_network(lab_path, **mgmt_cloud)

# create Nodes
nodes = [
    {"name": "leaf01", "template": "veos", "image": "veos-4.22.0F", "left": 50},
    {"name": "leaf02", "template": "veos", "image": "veos-4.22.0F", "left": 200},
]
for node in nodes:
    client.api.add_node(lab_path, **node)

# connect nodes to management network
mgmt_connections = [
    {"src": "leaf01", "src_label": "Mgmt1", "dst": "eve-mgmt"},
    {"src": "leaf02", "src_label": "Mgmt1", "dst": "eve-mgmt"}
]
for link in mgmt_connections:
    client.api.connect_node_to_cloud(lab_path, **link)

# create p2p links
p2p_links = [
    {"src": "leaf01", "src_label": "Eth1", "dst": "leaf02", "dst_label": "Eth1"},
    {"src": "leaf01", "src_label": "Eth1", "dst": "leaf02", "dst_label": "Eth2"},
]
for link in p2p_links:
    client.api.connect_node_to_node(lab_path, **link)

client.logout()
```
