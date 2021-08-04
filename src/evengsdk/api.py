# -*- coding: utf-8 -*-

import copy
import json
from pathlib import Path
from random import randint
from typing import Dict, List, Tuple
from urllib.parse import quote_plus

NETWORK_TYPES = ["bridge", "ovs"]
VIRTUAL_CLOUD_COUNT = 9


class EvengApi:
    def __init__(self, clnt, timeout=30):
        """EVE-NG API wrapper object

        :param clnt: the EvengClient object for managing REST calls
        :type clnt: evengsdk.client.EvengClient
        :param timeout: connection timeout in seconds, defaults to 30
        :type timeout: int, optional
        """
        self.clnt = clnt
        self.log = clnt.log
        self.timeout = timeout
        self.version = None
        self.session = clnt.session
        self.supports_multi_tenants = False

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.session)

    def get_server_status(self):
        """Returns EVE-NG server status

        :return: HTTP response object
        """
        return self.clnt.get("/status")

    def list_node_templates(self, include_missing: bool = False):
        """List available node templates from EVE-NG

        :param include_missing: include templates with missing images,
                                defaults to False
        :type include_missing: bool, optional
        :return: HTTP response object
        """
        templates = self.clnt.get("/list/templates/")
        if not include_missing:
            templates = {k: v for k, v in templates.items() if "missing" not in v}
        return templates

    def node_template_detail(self, node_type: str):
        """List details for single node template all available
        images for the selected template will be included in the
        output.

        :param node_type: [description]
        :type node_type: str
        :return: [description]
        :rtype: [type]
        """
        return self.clnt.get(f"/list/templates/{node_type}")

    def list_users(self):
        """Return list of EVE-NG users"""
        return self.clnt.get("/users/")

    def list_user_roles(self):
        """Return user roles"""
        return self.clnt.get("/list/roles")

    def get_user(self, username: str):
        """get user details. Returns empty dictionary if the user does
        not exist.

        :param username: username to retrieve details for
        :type username: str
        """
        return self.clnt.get(f"/users/{username}")

    def add_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        name: str = "",
        email: str = "",
        expiration: str = "-1",
    ):
        """Add a new user in EVE-NG host

        :param username: a unique alphanumeric string used to login
        :type username: str
        :param password:  the user password used to login
        :type password: str
        :param role: user roles, defaults to 'user'.
                    choices are ['user', 'admin']
        :type role: str, optional
        :param name: user's full name, defaults to ''
        :type name: str, optional
        :param email: the email address of the user, defaults to ''
        :type email: str, optional
        :param expiration: date until the user is valid (UNIX timestamp)
                or -1 if never expires, defaults to '-1'
        :type expiration: str, optional
        """
        return self.clnt.post(
            "/users",
            data=json.dumps(
                {
                    "username": username,
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": role,
                    "expiration": expiration,
                }
            ),
        )

    def edit_user(self, username: str, data: dict = None):
        """Edit user details

        :param username: the user name for user to update
        :type username: str
        :param data: payload for user details to update, defaults to None
        :type data: dict, optional
        :raises ValueError: when data value is missing
        """
        if not data:
            raise ValueError("data field is required.")

        url = self.clnt.url_prefix + f"/users/{username}"
        existing_user = self.get_user(username)

        updated_user = {}
        if existing_user:
            updated_user = copy.deepcopy(existing_user)
            updated_user.update(data)
            return self.clnt.put(url, data=json.dumps(updated_user))

    def delete_user(self, username: str):
        return self.clnt.delete(f"/users/{username}")

    def list_networks(self):
        """List network types"""
        return self.clnt.get("/list/networks")

    def list_folders(self):
        """List all folders, including the labs contained within each"""
        return self.clnt.get("/folders/")

    def get_folder(self, folder: str):
        """Return details for given folder. folders contain lab files.

        :param folder: path to folder on server. ex. my_lab_folder
        :type folder: str
        """
        return self.clnt.get(f"/folders/{folder}")

    @staticmethod
    def normalize_path(path: str):
        if not path.startswith("/"):
            path = "/" + path
        path = Path(path).resolve()

        # Add extension if needed
        path = path.with_suffix(".unl")

        # make parts of the path url safe
        quoted_parts = [str(quote_plus(x)) for x in path.parts[1:]]

        # rejoin the path and return string
        new_path = Path("/").joinpath(*quoted_parts)
        return str(new_path)

    def get_lab(self, path: str):
        """Return details for a single lab

        :param path: path to lab file(including parent folder)
        :type path: str
        """
        url = "/labs" + self.normalize_path(path)
        return self.clnt.get(url)

    def export_lab(self, path: str, filename: str = "lab_export.zip"):
        """Export and download a lab as a .unl file

        :param path: the path of the lab (include parent folder)
        :type path: str
        :param filename: filename to save the export.
                        defaults to 'lab_export.zip'
        :type filename: str, optional
        """
        lab_filepath = Path(path)

        payload = {"0": str(lab_filepath), "path": ""}
        print(payload)

        resp = self.clnt.post("/export", data=json.dumps(payload))
        if resp:
            client = self.clnt
            download_url = f"http://{client.host}:{client.port}{resp}"
            _, r = self.clnt.get(download_url)

            with open(filename, "wb") as handle:
                handle.write(r.content)

    def list_lab_networks(self, path: str):
        """Get all networks configured in a lab

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        normalized_path = self.normalize_path(path)
        url = "/labs" + f"{normalized_path}/networks"
        return self.clnt.get(url)

    def get_lab_network(self, path: str, net_id: int):
        """Retrieve details for a single network in a lab

        :param path: path to lab file (include parent folder)
        :type path: str
        :param net_id: unique id for the lab network
        :type net_id: int
        """
        normalized_path = self.normalize_path(path)
        url = "/labs" + f"{normalized_path}/networks/{str(net_id)}"
        return self.clnt.get(url)

    def get_lab_network_by_name(self, path: str, name: str):
        """retrieve details for a single network using the
        lab name

        :param path: path to lab file (include parent folder)
        :type path: str
        :param name: name of the network
        :type name: str
        """
        networks = self.list_lab_networks(path)
        return next((v for k, v in networks.items() if v["name"] == name), None)

    def list_lab_links(self, path: str):
        """Get all remote endpoint for both ethernet and serial interfaces

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/links"
        return self.clnt.get(url)

    def list_nodes(self, path: str):
        """List all nodes in the lab

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes"
        return self.clnt.get(url)

    def get_node(self, path: str, node_id: str):
        """Retrieve single node from lab by ID

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: node ID to retrieve
        :type node_id: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/{node_id}"
        return self.clnt.get(url)

    def get_node_by_name(self, path: str, name: str):
        """Retrieve single node from lab by name

        :param path: path to lab file (include parent folder)
        :type path: str
        :param name: node name
        :type name: str
        """
        nodes = self.list_nodes(path)
        return next((v for k, v in nodes.items() if v["name"] == name), None)

    def get_node_configs(self, path: str):
        """Return information about node configs

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/configs"
        return self.clnt.get(url)

    def get_node_config_by_id(self, path: str, node_id: int):
        """Return configuration information about a specific node given
        the configuration ID

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: ID for node to retrieve configuration for
        :type node_id: int
        """
        url = "/labs" + f"{self.normalize_path(path)}/configs/{str(node_id)}"
        return self.clnt.get(url)

    def upload_node_config(self, path: str, node_id: str, config: str, enable=False):
        """Upload node's startup config.

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: node ID to upload config for
        :type node_id: str
        :param config: configuration string
        :type config: str
        :param enable: enable the node config after upload, defaults to False
        :type enable: bool, optional
        """
        url = "/labs" + f"{self.normalize_path(path)}/configs/{node_id}"
        payload = {"id": node_id, "data": config}
        return self.clnt.put(url, data=json.dumps(payload))

    @staticmethod
    def find_node_interface(name: str, intf_list: List):
        intf_list = list(intf_list)
        return next(
            ((idx, intf) for idx, intf in enumerate(intf_list) if intf["name"] == name),
            None,
        )

    def connect_node(
        self,
        path: str,
        src: str = "",
        src_port: str = "",
        dst: str = "",
        dst_port: str = "",
        dst_type: str = "network",
        media: str = "",
    ):
        """Connect node to a network or node

        :param path: path to lab file (include parent folder)
        :type path: str
        :param src: source device name, defaults to ""
        :type src: str, optional
        :param src_port: source port name, defaults to ""
        :type src_port: str, optional
        :param dst: destination device name, defaults to ""
        :type dst: str, optional
        :param dst_port: destination port, defaults to ""
        :type dst_port: str, optional
        :param dst_type: destination type, defaults to "network".
                        choices are ["node", "network"]
        :type dst_type: str, optional
        :param media: port media type, defaults to ""
        :type media: str, optional
        """
        dest_types = ["network", "node"]
        if dst_type not in dest_types:
            raise ValueError(f"destination type not in allowed types: {dest_types}")

        # normalize lab path
        normpath = self.normalize_path(path)

        # Connect node to either cloud (network) or node
        if dst_type == "network":
            self.log.debug(f"{path}: Connecting node {src} to cloud {dst}")
            return self.connect_node_to_cloud(normpath, src, src_port, dst, media=media)
        else:
            self.log.debug(f"{path}: Connecting node {src} to node {dst}")
            return self.connect_node_to_node(
                normpath, src, src_port, dst, dst_port, media=media
            )

    def connect_p2p_interface(
        self, path: str, node_id: str, interface: Tuple, net_id: str
    ):
        """Connect node interface to a network

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: Node ID
        :type node_id: str
        :param interface: [description]
        :type interface: Tuple
        :param net_id: [description]
        :type net_id: str
        """
        url = "/labs" f"{self.normalize_path(path)}/nodes/{node_id}/interfaces"

        # connect interfaces
        intf_id = interface[0]
        self.clnt.put(url, data=json.dumps({intf_id: str(net_id)}))

        # set visibility for bridge to "0" to hide bridge in the GUI
        return self.edit_lab_network(path, net_id, data={"visibility": "0"})

    def connect_node_to_cloud(
        self, path, node_name, node_port, net_name, media="ethernet"
    ):
        node = self.get_node_by_name(path, node_name)
        if node is None:
            raise ValueError(f"node {node_name} not found or invalid")

        net = self.get_lab_network_by_name(path, net_name)
        if net is None:
            raise ValueError(f"network {net_name} not found or invalid")

        node_id = node.get("id")
        all_ports = self.get_node_interfaces(path, node_id).get(media)
        found_interface = self.find_node_interface(node_port, all_ports)

        if not found_interface:
            raise ValueError(f"{node_port} invalid or missing for " f"{node_name}")

        intf_id = str(found_interface[0])
        net_id = net.get("id")

        url = "/labs" f"{self.normalize_path(path)}/nodes/{node_id}/interfaces"
        return self.clnt.put(url, data=json.dumps({intf_id: str(net_id)}))

    def connect_node_to_node(
        self,
        lab,
        src_node_name,
        src_node_i,
        dst_node_name,
        dst_node_i,
        media="ethernet",
    ):
        src_node = self.get_node_by_name(lab, src_node_name)
        dst_node = self.get_node_by_name(lab, dst_node_name)

        # Validate hosts
        if not all((src_node, dst_node)):
            raise ValueError("host(s) not found or invalid")

        # Node IDs
        src_node_id = src_node.get("id")
        dst_node_id = dst_node.get("id")

        if src_node_id and dst_node_id:
            # Get all current interfaces of type media ("ethernet" or "serial")
            src_node_ports = self.get_node_interfaces(lab, src_node_id).get(media)
            dst_node_ports = self.get_node_interfaces(lab, dst_node_id).get(media)

            # Extract interface dicts from list of interfaces
            src_intf = self.find_node_interface(src_node_i, src_node_ports)
            dst_intf = self.find_node_interface(dst_node_i, dst_node_ports)

            if src_intf and dst_intf:
                net_resp = self.add_lab_network(
                    lab, network_type="bridge", visibility="1"
                )

                if net_resp is not None and net_resp.get("id"):
                    net_id = net_resp.get("id")
                    if net_id:
                        r1 = self.connect_p2p_interface(
                            lab, src_node_id, src_intf, net_id
                        )
                        r2 = self.connect_p2p_interface(
                            lab, dst_node_id, dst_intf, net_id
                        )
                        return (r1, r2)
            elif src_intf:
                raise ValueError(f"interface not found on node: {src_node_i}")
            else:
                raise ValueError(f"interface not found on node: {dst_node_i}")
        elif src_node_id:
            raise ValueError(f"node not found in lab: {dst_node_name}")
        else:
            raise ValueError(f"node not found in lab: {src_node_name}")
        return

    def start_all_nodes(self, path: str):
        """Start one or all nodes configured in a lab

        :param path: path to lab file (including parent folder)
        :type path: str
        """
        url = f"/labs{self.normalize_path(path)}/nodes/start"
        return self.clnt.get(url)

    def stop_all_nodes(self, path: str):
        """Stop one or all nodes configured in a lab

        :param path: [description]
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/stop"
        return self.clnt.get(url)

    def start_node(self, path: str, node_id: str):
        """Start single node in a lab

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: str
        """
        uri = f"/nodes/{node_id}/start"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def stop_node(self, path: str, node_id: str):
        """Stop single node in a lab

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: str
        """
        uri = f"/nodes/{node_id}/stop"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def wipe_all_nodes(self, path: str):
        """Wipe one or all nodes configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        :param path: [description]
        :type path: [type]
        :return: str
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/wipe"
        return self.clnt.get(url)

    def wipe_node(self, path: str, node_id: int):
        """Wipe single node configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        :param path: [description]
        :type path: [type]
        :param node_id: [description]
        :type node_id: [type]
        """
        uri = f"/nodes/{str(node_id)}/wipe"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def export_all_nodes(self, path: str):
        """Export one or all nodes configured in a lab.
        Exporting means saving the startup-config into
        the lab file.

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/export"
        return self.clnt.get(url)

    def export_node(self, path: str, node_id: int):
        """Export node configuration. Exporting means
        saving the startup-config into the lab file.

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: int
        """
        uri = f"/nodes/{str(node_id)}/export"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_node_interfaces(self, path: str, node_id: int):
        """Get configured interfaces from a node.

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: int
        """
        uri = f"/nodes/{str(node_id)}/interfaces"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_topology(self, path: str):
        """Get the lab topology

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path) + "/topology"
        return self.clnt.get(url)

    def get_lab_pictures(self, path: str):
        """Get one or all pictures configured in a lab

        :param path: [description]
        :type path: str
        """
        url = f"/labs{self.normalize_path(path)}/pictures"
        return self.clnt.get(url)

    def get_lab_picture_details(self, path: str, picture_id: int):
        """Retrieve single picture

        :param path: [description]
        :type path: str
        :param picture_id: [description]
        :type picture_id: int
        """
        uri = f"/pictures/{str(picture_id)}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def node_exists(self, path, nodename):
        exists = False
        node = self.get_node_by_name(path, nodename)
        if node is not None:
            exists = node.get("name") == nodename.lower()
        return exists

    def create_lab(
        self,
        name: str,
        path: str = "/",
        author: str = "",
        body: str = "",
        version: str = "1.0",
        description: str = "",
        scripttimeout: int = 600,
        lock: int = 0,
        tenant: str = "",
    ) -> Dict:
        """Create a new lab

        :param name: name of the lab
        :type name: str
        :param path: path to lab file on EVE-NG server, defaults to "/"
        :type path: str, optional
        :param author: lab author, defaults to ""
        :type author: str, optional
        :param body: long description for lab, defaults to ""
        :type body: str, optional
        :param version: lab version. Defaults to "1.0"
        :type version: str, optional
        :param description: short description, defaults to ""
        :type description: str, optional
        :param scripttimeout: value in seconds used for the
                “Configuration Export” and “Boot from exported configs”
                operations, defaults to 600
        :type scripttimeout: int, optional
        :param lock: set lab as as readonly. Defaults to 0
        :type lock: int, optional
        :param tenant: tenant (username) to create lab for, defaults to ""
        :type tenant: str, optional
        """
        data = {
            "path": path,
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "body": body,
            "lock": lock,
            "scripttimeout": scripttimeout,
        }

        url = "/labs"
        if self.supports_multi_tenants:
            existing_user = self.get_user(tenant)
            if existing_user:
                url += "{tenant}/"
        return self.clnt.post(url, data=json.dumps(data))

    def edit_lab(self, path: str, param: dict) -> Dict:
        """Edit an existing lab. The request can set only one single
        parameter. Optional parameter can be reverted to the default
        setting an empty string “”.

        :param path: [description]
        :type path: str
        :param param: [description]
        :type param: dict
        """
        valid_params = (
            "name",
            "version",
            "author",
            "description",
            "body",
            "lock",
            "scripttimeout",
        )
        if len(param) > 1:
            raise ValueError(
                "API allows updating a single paramater per request. "
                f"received {len(param)}."
            )
        for key, _ in param.items():
            if key not in valid_params:
                raise ValueError(f"{key} is an invalid or unsupported paramater")

        url = "/labs" + f"{self.normalize_path(path)}"
        print(url)
        return self.clnt.put(url, data=json.dumps(param))

    def delete_lab(self, path: str) -> bool:
        """Delete an existing lab

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path)
        return self.clnt.delete(url)

    def lock_lab(self, path: str):
        """Lock lab to prevent edits"""
        url = "/labs" + f"{self.normalize_path(path)}/Lock"
        return self.clnt.put(url)

    def unlock_lab(self, path: str):
        """Unlock lab to allow edits"""
        url = "/labs" + f"{self.normalize_path(path)}/Unlock"
        return self.clnt.put(url)

    def _get_network_types(self):
        network_types = set(NETWORK_TYPES)
        virtual_clouds = (f"pnet{x}" for x in range(VIRTUAL_CLOUD_COUNT))
        return network_types.union(virtual_clouds)

    @property
    def network_types(self):
        return self._get_network_types()

    def edit_lab_network(self, path: str, net_id: int, data: Dict = None):
        """Edit lab network

        :param path: [description]
        :type path: str
        :param net_id: [description]
        :type net_id: int
        :param data: [description], defaults to None
        :type data: [type], optional
        """
        if not data:
            raise ValueError("data field is required.")
        url = "/labs" + self.normalize_path(path) + f"/networks/{str(net_id)}"
        return self.clnt.put(url, data=json.dumps(data))

    def add_lab_network(
        self,
        path: str,
        network_type: str = "",
        visibility: int = 0,
        name: str = "",
        left: int = randint(30, 70),
        top: int = randint(30, 70),
    ):
        """Add new network to lab

        :param path: [description]
        :type path: str
        :param network_type: [description], defaults to ""
        :type network_type: str, optional
        :param visibility: [description], defaults to 0
        :type visibility: int, optional
        :param name: network name (i.e. Core Network), default is
                    NetX (X = network_id), defaults to ""
        :type name: str, optional
        :param left: margin from left, in percentage (i.e. 35%),
                    default is a random value between 30% and 70%,
                    defaults to randint(30, 70)
        :type left: int, optional
        :param top:  margin from left, in percentage (i.e. 35%),
                    default is a random value between 30% and 70%,
                    defaults to randint(30, 70)
        :type top: int, optional
        """
        if network_type not in self.network_types:
            raise ValueError(
                f"invalid network type: {network_type} \
                not member of set {self.network_types}"
            )

        data = {
            "left": left,
            "name": name,
            "top": top,
            "type": network_type,
            "visibility": visibility,
        }
        url = "/labs" + self.normalize_path(path) + "/networks"
        return self.clnt.post(url, data=json.dumps(data))

    def delete_lab_network(self, path: str, net_id: int):
        url = f"/labs{self.normalize_path(path)}/networks/{str(net_id)}"
        return self.clnt.delete(url)

    def add_node(
        self,
        path: str,
        template: str,
        delay: int = 0,
        name: str = "",
        node_type: str = "",
        top: int = randint(30, 70),
        left: int = randint(30, 70),
        console: str = "telnet",
        config: str = "Unconfigured",
        ethernet: int = None,
        serial: int = None,
        image: str = None,
        icon: str = None,
        ram: int = None,
        cpu: int = None,
        nvram: int = None,
        idlepc: str = None,
        slots: str = "",
    ):
        """Create node and add to lab


        :param path: [description]
        :type path: str
        :param delay: seconds to wait before starting the node,
                    default is 0, defaults to 0
        :type delay: int, optional
        :param name: node name (i.e. “Core1”), default is
                    NodeX (X = node_id), defaults to ""
        :type name: str, optional
        :param node_type: node type, defaults to "qemu". value ccan be
                        one of ['iol', 'dynamips', 'qemu']
        :type node_type: str, optional
        :param template: [description], defaults to ""
        :type template: template for device type
        :param top: margin from top, in percentage (i.e. 35%), default
                    is a random value between 30% and 70%, defaults to
                    randint(30, 70)
        :type top: int, optional
        :param left: margin from left, in percentage (i.e. 35%), default
                    is a random value between 30% and 70%, defaults to
                    randint(30, 70)
        :type left: int, optional
        :param console: can be telnet or vnc, default is telnet,
        defaults to "telnet". (qemu)
        :type console: str, optional
        :param config: can be 'Unconfigured' or 'Saved',
                    defaults to "Unconfigured"
        :type config: str, optional
        :param ethernet: number of ethernet porgroups (each portgroup
                        configures four interfaces), defaults to None. if None,
                        node will be created with a default of 2
        :type ethernet: int, optional
        :param serial: num of serial portgroups (each portgroup configures
                        four interfaces), defaults to None. if None,
                        node is created >with 2.
        :type serial: int, optional
        :param image: image used to start the node, default is latest
                        included in “List node templates”, defaults to None
        :type image: str, optional
        :param icon: filename for icon used to display the node, default
                is Router.png; (located in /opt/unetlab/html/images/icons/),
                defaults to None
        :type icon: str, optional
        :param ram: MB of RAM configured for the node, default is 1024
        :type ram: int, optional
        :param cpu: number of configured CPU, defaults to None. if None,
                    the number of configured CPU will be  1 (qemu)
        :type cpu: int, optional
        :param nvram: size of NVRAM in KB, default is 1024
        :type nvram: int, optional
        :param idlepc: value used for Dynamips optimization (i.e. 0x80369ac4),
                    default is 0x0 (no optimization) (Dynamips)
        :param slot: 0-9]+ the module configured in a specific slot
                    (i.e. slot1=NM-1FE-TX).
        :type slot: int, optional
        """
        url = "/labs" + self.normalize_path(path) + "/nodes"

        template = template
        resp = self.node_template_detail(template)
        template_defaults = resp.get("options")

        icon = icon or template_defaults.get("icon")["value"]
        ethernet = ethernet or template_defaults.get("ethernet")["value"]
        ram = ram or template_defaults.get("ram")["value"]
        image = image or template_defaults.get("image")["value"]
        cpu = cpu or template_defaults.get("cpu")["value"]

        data = {
            "type": node_type,
            "template": template,
            "config": config,
            "delay": delay,
            "icon": icon,
            "image": image,
            "name": name,
            "left": left,
            "top": top,
            "ram": ram,
            "cpu": cpu,
            "console": console,
            "ethernet": int(ethernet) if ethernet else "",
        }
        resp = {}
        if not self.node_exists(path, name):
            resp = self.clnt.post(url, data=json.dumps(data))
        return resp
