# -*- coding: utf-8 -*-

import copy
import json
from pathlib import Path
from random import randint
from typing import BinaryIO, Dict, Literal, Optional, Tuple
from urllib.parse import quote_plus


class EvengApi:
    def __init__(self, client):
        """EVE-NG API wrapper object

        :param client: the EvengClient object for managing REST calls
        :type client: evengsdk.client.EvengClient
        :param timeout: connection timeout in seconds, defaults to 30
        :type timeout: int, optional
        """
        self.client = client
        self.log = client.log
        self.version = None
        self.supports_multi_tenants = False
        self.is_community = True

        status = self.get_server_status()
        self.version = status["data"]["version"]

        if self.version and "pro" in self.version.lower():
            self.is_community = False

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.client.session)

    def get_server_status(self) -> Dict:
        """Returns EVE-NG server status"""
        return self.client.get("/status")

    def list_node_templates(self) -> Dict:
        """List available node templates from EVE-NG"""
        return self.client.get("/list/templates/")

    def node_template_detail(self, node_type: str) -> Dict:
        """List details for single node template all available
        images for the selected template will be included in the
        output.

        :param node_type: Node type name to retrieve details for
        :type node_type: str
        :return: response dict
        :rtype: str
        """
        return self.client.get(f"/list/templates/{node_type}")

    def list_users(self) -> Dict:
        """Return list of EVE-NG users"""
        return self.client.get("/users/")

    def list_user_roles(self) -> Dict:
        """Return user roles"""
        return self.client.get("/list/roles")

    def get_user(self, username: str) -> Dict:
        """get user details. Returns empty dictionary if the user does
        not exist.

        :param username: username to retrieve details for
        :type username: str
        """
        return self.client.get(f"/users/{username}")

    def add_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        name: str = "",
        email: str = "",
        expiration: str = "-1",
    ) -> Dict:
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
        return self.client.post(
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

    def edit_user(self, username: str, data: dict = None) -> Dict:
        """Edit user details

        :param username: the user name for user to update
        :type username: str
        :param data: payload for user details to update, defaults to None
        :type data: dict, optional
        :raises ValueError: when data value is missing
        """
        if not data:
            raise ValueError("data field is required.")

        url = self.client.url_prefix + f"/users/{username}"
        existing_user = self.get_user(username)

        updated_user = {}
        if existing_user:
            updated_user = copy.deepcopy(existing_user)
            updated_user.update(data)
            return self.client.put(url, data=json.dumps(updated_user))

    def delete_user(self, username: str) -> Dict:
        return self.client.delete(f"/users/{username}")

    def list_networks(self) -> Dict:
        """List network types"""
        return self.client.get("/list/networks")

    def list_folders(self) -> Dict:
        """List all folders, including the labs contained within each"""
        return self.client.get("/folders/")

    def get_folder(self, folder: str) -> Dict:
        """Return details for given folder. folders contain lab files.

        :param folder: path to folder on server. ex. my_lab_folder
        :type folder: str
        """
        return self.client.get(f"/folders/{folder}")

    def normalize_path(self, path: str) -> str:
        if not path.startswith("/"):
            path = (
                "/" + path if self.is_community else f"/{self.client.username}/{path}"
            )
        path = Path(path).resolve()

        # Add extension if needed
        path = path.with_suffix(".unl")

        # make parts of the path url safe
        quoted_parts = [str(quote_plus(x)) for x in path.parts[1:]]

        # rejoin the path and return string
        new_path = Path("/").joinpath(*quoted_parts).as_posix()
        return str(new_path)

    def get_lab(self, path: str) -> Dict:
        """Return details for a single lab

        :param path: path to lab file(including parent folder)
        :type path: str
        """
        url = "/labs" + self.normalize_path(path)
        return self.client.get(url)

    def export_lab(
        self, path: str, filename: str = None
    ) -> Tuple[bool, Optional[BinaryIO]]:
        """Export and download a lab as a .unl file

        :param path: the path of the lab (include parent folder)
        :type path: str
        :param filename: filename to save the export.
                        defaults to 'lab_export.zip'
        :type filename: str, optional
        :return: tuple of (success, file)
        """
        lab_filepath = Path(path)

        payload = {"0": str(lab_filepath), "path": ""}
        resp = self.client.post("/export", data=json.dumps(payload))
        zip_file_endpoint = resp.get("data", "")
        zip_filename = zip_file_endpoint.split("/")[-1]

        if resp:
            client = self.client
            download_url = f"{client.protocol}://{client.host}{zip_file_endpoint}"
            r = self.client.get(download_url, use_prefix=False)

            with open(filename or zip_filename, "wb") as handle:
                handle.write(r.content)
            return (True, zip_filename)
        return (False, None)

    def import_lab(self, path: str, folder: str = "/") -> bool:
        """Import a lab from a .unl file

        :param path: the source .zip file path of the lab
        :type path: str
        :param folder: the destination folder(s) for the lab as a path string
                        defaults to '/'
        :type folder: str, optional
        :return: True if import was successful, False otherwise
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} does not exist.")

        # retrieve the current cookies and reset the client custom headers
        cookies = self.client.session.cookies.get_dict()
        headers = {
            "Accept": "*/*",
            "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
        }
        self.client.session.headers = headers

        # upload the file
        files = {"file": open(path, "rb")}
        return self.client.post("/import", data={"path": folder}, files=files)

    def list_lab_networks(self, path: str) -> Dict:
        """Get all networks configured in a lab

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        normalized_path = self.normalize_path(path)
        url = f"/labs{normalized_path}/networks"
        return self.client.get(url)

    def get_lab_network(self, path: str, net_id: int) -> Dict:
        """Retrieve details for a single network in a lab

        :param path: path to lab file (include parent folder)
        :type path: str
        :param net_id: unique id for the lab network
        :type net_id: int
        """
        normalized_path = self.normalize_path(path)
        url = "/labs" + f"{normalized_path}/networks/{net_id}"
        return self.client.get(url)

    def get_lab_network_by_name(self, path: str, name: str) -> Dict:
        """retrieve details for a single network using the
        lab name

        :param path: path to lab file (include parent folder)
        :type path: str
        :param name: name of the network
        :type name: str
        """
        resp = self.list_lab_networks(path)
        if networks := resp.get("data"):
            return next((v for _, v in networks.items() if v["name"] == name), None)
        return

    def list_lab_links(self, path: str) -> Dict:
        """Get all remote endpoint for both ethernet and serial interfaces

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/links"
        return self.client.get(url)

    def list_nodes(self, path: str) -> Dict:
        """List all nodes in the lab

        :param path: path to lab file (include parent folder)
        :type path: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes"
        return self.client.get(url)

    def get_node(self, path: str, node_id: str) -> Dict:
        """Retrieve single node from lab by ID

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: node ID to retrieve
        :type node_id: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/{node_id}"
        return self.client.get(url)

    def delete_node(self, path: str, node_id: str) -> Dict:
        """Delete a node from the lab

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: node ID to delete
        :type node_id: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/{node_id}"
        return self.client.delete(url)

    def get_node_by_name(self, path: str, name: str) -> Dict:
        """Retrieve single node from lab by name

        :param path: path to lab file (include parent folder)
        :type path: str
        :param name: node name
        :type name: str
        """
        r = self.list_nodes(path)
        node_data = r["data"]
        if node_data:
            return next((v for _, v in node_data.items() if v["name"] == name), None)
        return

    def get_node_configs(self, path: str, configset: str = "default") -> Dict:
        """Return information about node configs

        :param path: path to lab file (include parent folder)
        :type path: str
        :param configset: name of the configset to retrieve configs for (pro version)
        :type configset: str, optional
        """
        url = "/labs" + f"{self.normalize_path(path)}/configs"
        if not self.is_community:
            return self.client.post(url, data=json.dumps({"cfsid": configset}))
        return self.client.get(url)

    def get_node_config_by_id(
        self, path: str, node_id: int, configset: str = "default"
    ) -> Dict:
        """Return configuration information about a specific node given
        the configuration ID

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: ID for node to retrieve configuration for
        :type node_id: int
        :param configset: name of the configset to retrieve configs for (pro version)
        :type configset: str, optional
        """
        url = "/labs" + f"{self.normalize_path(path)}/configs/{node_id}"
        if not self.is_community:
            return self.client.post(url, data=json.dumps({"cfsid": configset}))
        return self.client.get(url)

    def upload_node_config(
        self, path: str, node_id: str, config: str, configset: str = "default"
    ) -> Dict:
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
        if not self.is_community:
            payload["cfsid"] = configset
        return self.client.put(url, data=json.dumps(payload))

    def enable_node_config(self, path: str, node_id: str) -> Dict:
        """Enable a node's startup config

        :param path: path to lab file (include parent folder)
        :type path: str
        :param node_id: node ID to enable config for
        :type node_id: str
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/{node_id}"
        return self.client.put(url, data=json.dumps({"id": node_id, "config": 1}))

    def find_node_interface(
        self,
        path: str,
        node_id: str,
        interface_name: str,
        media: Literal["ethernet", "serial"] = "ethernet",
    ) -> Dict:
        r = self.get_node_interfaces(path, node_id)
        interface_list = r["data"].get(media, [])
        return next(
            (
                (idx, interface)
                for idx, interface in enumerate(interface_list)
                if interface["name"] == interface_name
            ),
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
    ) -> Dict:
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
    ) -> Dict:
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
        interface_id = interface[0]
        payload = {interface_id: str(net_id)}
        self.client.put(url, data=json.dumps(payload))

        # set visibility for bridge to "0" to hide bridge in the GUI
        return self.edit_lab_network(path, net_id, data={"visibility": "0"})

    def connect_node_to_cloud(
        self,
        path: str,
        src: str,
        src_label: str,
        dst: str,
        media: Literal["ethernet", "serial"] = "ethernet",
    ) -> Dict:
        """Connect node to a cloud"""
        normpath = self.normalize_path(path)
        node = self.get_node_by_name(path, src)
        if node is None:
            raise ValueError(f"node {src} not found or invalid")
        node_id = node.get("id")

        net = self.get_lab_network_by_name(path, dst)
        if net is None:
            raise ValueError(f"network {dst} not found or invalid")
        net_id = net.get("id")

        node_interface = self.find_node_interface(path, node_id, src_label, media)
        if not node_interface:
            raise ValueError(f"{src_label} invalid or missing for " f"{src}")
        interface = node_interface[0]

        url = f"/labs{normpath}/nodes/{node_id}/interfaces"
        return self.client.put(url, data=json.dumps({interface: f"{net_id}"}))

    def connect_node_to_node(
        self,
        path: str,
        src: str,
        src_label: str,
        dst: str,
        dst_label: str,
        media: Literal["ethernet", "serial"] = "ethernet",
    ) -> bool:
        """Connect node to another node

        :param path: path to lab file (include parent folder)
        :type path: str
        :param src: source device name
        :type src: str
        :param src_label: source port name
        :type src_label: str
        :param dst: destination device name
        :type dst: str
        :param dst_label: destination port name
        :type dst_label: str
        :param media: port media type, defaults to "ethernet"
        :type media: str, optional
        :return: True if successful
        :rtype: bool
        """

        self.client.log.debug(
            f"connecting node {src} to node {dst}"
            f" on interfaces {src_label} <-> {dst_label}"
            f" in lab {path.replace(' ', '_')}"
        )
        # find nodes using node names
        s_node_dict = self.get_node_by_name(path, src)
        d_node_dict = self.get_node_by_name(path, dst)

        # Validate that we found the hosts to connect
        s_node_id = s_node_dict.get("id")
        d_node_id = d_node_dict.get("id")
        if not all((s_node_id, d_node_id)):
            raise ValueError("host(s) not found or invalid")

        # find the p2p interfaces on each of the nodes
        src_int = self.find_node_interface(path, s_node_id, src_label, media)
        if not src_int:
            raise ValueError(f"{src_label} invalid or missing for " f"{src}")
        dst_int = self.find_node_interface(path, d_node_id, dst_label, media)
        if not dst_int:
            raise ValueError(f"{dst_label} invalid or missing for " f"{dst}")

        # create the bridge for the p2p interfaces
        self.client.log.debug(
            f"creating bridge for p2p link: node{s_node_id} <-> node{d_node_id}"
        )
        net_resp = self.add_lab_network(path, network_type="bridge", visibility="1")
        net_id = net_resp.get("data", {}).get("id")
        self.client.log.debug(f"created bridge ID: {net_id}")

        if not net_id:
            raise ValueError("Failed to create bridge")

        # connect the p2p interfaces to the bridge
        self.client.log.debug(f"connecting node{s_node_id} -> net:{net_id}")
        r1 = self.connect_p2p_interface(path, s_node_id, src_int, net_id)
        self.client.log.debug(f"connecting node{d_node_id} -> net:{net_id}")
        r2 = self.connect_p2p_interface(path, d_node_id, dst_int, net_id)
        return r1["status"] == "success" and r2["status"] == "success"

    def _update_nodes(
        self, path: str, action: Literal["stop", "start", "wipe"]
    ) -> Dict:
        resp = self.list_nodes(path)
        action_method = getattr(self, f"{action}_node")
        if resp["data"]:
            results = []
            for node_id, _ in resp["data"].items():
                res = action_method(path, node_id)
                results.append(res)
            return self._extract_recursive_statuses(results)
        return resp

    def start_all_nodes(self, path: str) -> Dict:
        """Start one or all nodes configured in a lab

        :param path: path to lab file (including parent folder)
        :type path: str
        """
        if self.is_community:
            url = f"/labs{self.normalize_path(path)}/nodes/start"
            return self.client.get(url)
        return self._update_nodes(path, "start")

    def stop_all_nodes(self, path: str) -> Dict:
        """Stop one or all nodes configured in a lab

        :param path: [description]
        :type path: str
        """
        if self.is_community:
            url = f"/labs{self.normalize_path(path)}/nodes/stop"
            return self.client.get(url)
        return self._update_nodes(path, "stop")

    def start_node(self, path: str, node_id: str) -> Dict:
        """Start single node in a lab

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: str
        """
        url = "/labs" + self.normalize_path(path) + f"/nodes/{node_id}/start"
        return self.client.get(url)

    def stop_node(self, path: str, node_id: str) -> Dict:
        """Stop single node in a lab

        :param path: [description]
        :type path: str
        :param node_id: [description]
        :type node_id: str
        """
        url = "/labs" + self.normalize_path(path) + f"/nodes/{node_id}/stop"
        if not self.is_community:
            url += "/stopmode=3"
        return self.client.get(url)

    def _extract_recursive_statuses(self, results):
        success = all(r["status"] == "success" for r in results)
        messages = [r["message"] for r in results]
        return {
            "status": "success" if success else "error",
            "data": results,
            "message": messages,
        }

    def wipe_all_nodes(self, path: str) -> Dict:
        """Wipe one or all nodes configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        :param path: [description]
        :type path: [type]
        :return: str
        """
        if self.is_community:
            url = f"/labs{self.normalize_path(path)}/nodes/wipe"
            return self.client.get(url)
        return self._update_nodes(path, "wipe")

    def wipe_node(self, path: str, node_id: int) -> Dict:
        """Wipe single node configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        :param path: [description]
        :type path: [type]
        :param node_id: [description]
        :type node_id: [type]
        """
        url = "/labs" + self.normalize_path(path) + f"/nodes/{node_id}/wipe"
        return self.client.get(url)

    def export_all_nodes(self, path: str) -> Dict:
        """Export one or all nodes configured in a lab.
        Exporting means saving the startup-config into
        the lab file.

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/export"
        return self.client.put(url)

    def export_node(self, path: str, node_id: int) -> Dict:
        """Export node configuration. Exporting means
        saving the startup-config into the lab file.

        :param path: lab path
        :type path: str
        :param node_id: node ID for to export config from
        :type node_id: int
        """
        url = "/labs" + f"{self.normalize_path(path)}/nodes/{node_id}/export"
        return self.client.put(url)

    def get_node_interfaces(self, path: str, node_id: int) -> Dict:
        """Get configured interfaces from a node.

        :param path: lab path
        :type path: str
        :param node_id: node id in lab
        :type node_id: int
        """
        url = "/labs" + self.normalize_path(path) + f"/nodes/{node_id}/interfaces"
        return self.client.get(url)

    def get_lab_topology(self, path: str) -> Dict:
        """Get the lab topology

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path) + "/topology"
        return self.client.get(url)

    def get_lab_pictures(self, path: str) -> Dict:
        """Get one or all pictures configured in a lab

        :param path: [description]
        :type path: str
        """
        url = f"/labs{self.normalize_path(path)}/pictures"
        return self.client.get(url)

    def get_lab_picture_details(self, path: str, picture_id: int) -> Dict:
        """Retrieve single picture

        :param path: [description]
        :type path: str
        :param picture_id: [description]
        :type picture_id: int
        """
        url = "/labs" + self.normalize_path(path) + f"/pictures/{picture_id}"
        return self.client.get(url)

    def node_exists(self, path, nodename) -> bool:
        node = self.get_node_by_name(path, nodename)
        return node.get("name") == nodename.lower() if node is not None else False

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
        return self.client.post(url, data=json.dumps(data))

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
        return self.client.put(url, data=json.dumps(param))

    def close_lab(self) -> Dict:
        """Close the current lab."""
        url = "/labs/close"
        return self.client.delete(url)

    def delete_lab(self, path: str) -> Dict:
        """Delete an existing lab

        :param path: [description]
        :type path: str
        """
        url = "/labs" + self.normalize_path(path)
        return self.client.delete(url)

    def lock_lab(self, path: str) -> Dict:
        """Lock lab to prevent edits"""
        url = "/labs" + f"{self.normalize_path(path)}/Lock"
        return self.client.put(url)

    def unlock_lab(self, path: str) -> Dict:
        """Unlock lab to allow edits"""
        url = "/labs" + f"{self.normalize_path(path)}/Unlock"
        return self.client.put(url)

    def _get_network_types(self):
        network_types = self.list_networks()
        return [key for key, _ in network_types["data"].items()]

    @property
    def network_types(self):
        return self._get_network_types()

    def edit_lab_network(self, path: str, net_id: int, data: Dict = None) -> Dict:
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
        url = "/labs" + self.normalize_path(path) + f"/networks/{net_id}"
        return self.client.put(url, data=json.dumps(data))

    def add_lab_network(
        self,
        path: str,
        network_type: str = "",
        visibility: int = 0,
        name: str = "",
        left: int = randint(30, 70),
        top: int = randint(30, 70),
    ) -> Dict:
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
        existing_network = self.get_lab_network_by_name(path, name)
        if existing_network:
            raise ValueError(f"Network already exists: `{name}` in lab {path}")

        additional_network_types = ("internal", "private", "nat")
        if self.is_community:
            if any(
                network_type.startswith(prefix) for prefix in additional_network_types
            ):
                raise ValueError(
                    f"Community edition does not support network type: `{network_type}`"
                )
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
        return self.client.post(url, data=json.dumps(data))

    def delete_lab_network(self, path: str, net_id: int) -> Dict:
        url = f"/labs{self.normalize_path(path)}/networks/{net_id}"
        return self.client.delete(url)

    def add_node(
        self,
        path: str,
        template: str,
        delay: int = 0,
        name: str = "",
        node_type: str = "qemu",
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
        slot: str = "",
    ) -> Dict:
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
        url = f"/labs{self.normalize_path(path)}/nodes"
        resp = self.node_template_detail(template)
        template_defaults = resp["data"]["options"]

        ethernet = ethernet or template_defaults.get("ethernet", {}).get("value")
        serial = serial or template_defaults.get("serial", {}).get("value")
        data = {
            "type": node_type,
            "template": template,
            "config": config,
            "delay": delay,
            "icon": icon or template_defaults.get("icon", {}).get("value"),
            "image": image or template_defaults.get("image", {}).get("value"),
            "name": name,
            "left": left,
            "top": top,
            "ram": ram or template_defaults.get("ram", {}).get("value"),
            "cpu": cpu or template_defaults.get("cpu", {}).get("value"),
            "console": console,
            "ethernet": int(ethernet) if ethernet else "",
            "serial": int(serial) if serial else "",
            "nvram": nvram or template_defaults.get("nvram", {}).get("value"),
        }

        if node_type == "dynamips" and idlepc is not None:
            data["idlepc"] = idlepc

        if slot is not None:
            data["slot"] = slot

        resp = {}
        if not self.node_exists(path, name):
            resp = self.client.post(url, data=json.dumps(data))
        return resp
