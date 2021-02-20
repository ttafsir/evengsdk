# -*- coding: utf-8 -*-
"""
evegnsdk.api
~~~~~~~~~~~~~~~
This module contains the primary object for
the EVE-NG API wrapper
"""
import copy
import json
from pathlib import Path
from typing import Dict

from urllib.parse import quote_plus
from requests.exceptions import HTTPError

from evengsdk.exceptions import EvengApiError, EvengHTTPError


NETWORK_TYPES = ["bridge", "ovs"]
VIRTUAL_CLOUD_COUNT = 9


class EvengApi:

    def __init__(self, clnt, timeout=30):
        """
        User-created :class: `EvengAPI <EvengAPI>` object.
        Used by :class: `EvengClient <EvengClient>`, to make API calls to
        EVE-NG host.

        clnt (obj): A EvengClient object
        """
        self.clnt = clnt
        self.log = clnt.log
        self.timeout = timeout
        self.version = None
        self.session = clnt.session

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.session)

    def get_server_status(self):
        """Get server status"""
        return self.clnt.get('/status')

    def list_node_templates(self, include_missing=False):
        """
        List details for all node template

        Args:
            include_missing (bool): include node templates without
                images.

        Returns: dict
        """
        templates = self.clnt.get('/list/templates/')
        if not include_missing:
            templates = {
                k: v for k, v in templates.items()
                if 'missing' not in v
            }
        return templates

    def node_template_detail(self, node_type: str):
        """
        List details for single node template
        All available images for the selected template will be included in the
        output.

        Args:
            node_type (str): type of node
        """
        node_templates = self.clnt.get(f'/list/templates/{node_type}')
        return node_templates

    def list_users(self):
        """
        get list of users

        Returns:
            dict: returns dictionary containing user details
        """
        return self.clnt.get('/users/')

    def list_user_roles(self):
        """
        list user roles
        """
        return self.clnt.get('/list/roles')

    def get_user(self, username):
        """
        get user details. Returns empty dictionary if the user does
        not exist.

        Args:
            username (str): username to retrieve

        Returns:
            dict: user details
        """
        return self.clnt.get(f"/users/{username}")

    def add_user(self,
                 username,
                 password,
                 role='user',
                 name='',
                 email='',
                 expiration='-1',
                 **kwargs):
        """
        Add new user

        Args:
            email(str): the email address of the user;
            expiration(str): date until the user is valid (UNIX timestamp)
                or -1 if never expires;
            name(str): a description for the user, usually salutation;
            password (string): the user password used to login;
            role(string): choices are ['user', 'admin']
            username (str): a unique alphanumeric string used to login

        Returns:
            Dictionary with user data.

        """
        username = username or kwargs.get('username')
        password = password or kwargs.get('password')
        if not (username and password):
            raise ValueError('missing required username and/or password')

        user = {
            "username": username,
            "name": kwargs.get('name') or name,
            "email": kwargs.get('email') or email,
            "password": password,
            "role": kwargs.get('role') or role,
            "expiration": "-1"
        }

        self.clnt.log.debug('creating new user {}'.format(username))
        try:
            r = self.clnt.post('/users', data=json.dumps(user))
            return r
        except HTTPError as e:
            err = str(e)
            self.clnt.log.error(f'Could not create user: {err}')
            raise e

    def edit_user(self, username, data=None):
        """
        Edit user details

        Args:
            username(str): the user name for user
            data(dict): payload for user details to update

        Returns:
            dict:
        """
        url = self.clnt.url_prefix + f"/users/{username}"
        user_resp = self.get_user(username)

        # return empty dict if user does not exist
        if not user_resp:
            return user_resp

        updated_user = {}
        if data:
            updated_user = copy.deepcopy(user_resp)
            updated_user.update(data)
            resp = self.clnt.put(url, data=json.dumps(updated_user))
            return resp
        else:
            raise ValueError('data field is required.')

    def delete_user(self, username):
        """
        Delete EVE-NG user

        Args:
            username (str): username to delete

        Returns:
            dict: dictionary with the status of the DELETE operation

            sample output:
            {
                'code': 201,
                'status': 'success',
                'message': 'User saved (60042).'
            }
        """
        existing = self.get_user(username)
        if existing:
            resp = self.clnt.delete(f'/users/{username}')
            return resp
        raise EvengApiError('User does not exists or could not be deleted')

    def list_networks(self):
        """
        List network types

        Returns:
            dict: dictionary of networks
        """
        networks = self.clnt.get('/list/networks')
        return networks

    def list_folders(self):
        """
        List all folders and include labs
        """
        folders = self.clnt.get("/folders/")
        return folders

    def get_folder(self, folder):
        """
        List folders for user. folders contain lab files.

        Args:
            folder (str): folder name/path

        Returns:
            dict: dictionary with folder details
        """
        folder_details = self.clnt.get(f"/folders/{folder}")
        return folder_details

    @staticmethod
    def normalize_path(path):
        if path == "/":
            return path
        elif path:
            if not path.startswith('/'):
                path = '/' + path
            path = Path(path).resolve()

            # Add extension if needed
            path = path.with_suffix('.unl')

            # make parts of the path url safe
            quoted_parts = [str(quote_plus(x)) for x in path.parts[1:]]

            # rejoin the path and return string
            new_path = Path('/').joinpath(*quoted_parts)
            return str(new_path)
        return path

    def get_lab(self, path):
        """
        get details for a single lab. Returns empty dict
        if lab does not exist.

        Args:
            path (str): the path of the lab

        Returns:
            dict: dictionary with lab details
        """
        url = "/labs" + self.normalize_path(path)
        return self.clnt.get(url)

    def get_lab_download_link(self, labpath: str) -> Dict:
        endpoint = "/export"
        lab_filepath = Path(labpath)
        payload = {
            '0': str(lab_filepath),
            'path': str(lab_filepath.parent)
        }
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
        }
        return self.clnt.post(
            endpoint,
            data=json.dumps(payload),
            headers=headers
        )

    def export_lab(self, path: str) -> bool:
        """Export a lab as an archive file

        Args:
            path (str): path to lab on EVE-NG

        Returns:
            content (bytes): file content bytes
        """
        # request download link
        if download_ep := self.get_lab_download_link(path):
            url = (
                f"http://{self.clnt.host}{download_ep}"
            )
            # download archive
            if resp := self.clnt.session.get(url):
                filename = download_ep.split('/')[-1]
                return (filename, resp.content)
        return

    def import_lab(self, filepath: Path, folder: str = "/"):
        """Import lab into EVE-NG from ZIP archive

        Args:
            filepath (Path): Path object for ZIP archive
            folder (str, optional): folder to import lab to. Defaults to "/".

        Returns:
            dict: response object from API
        """
        ep = '/import'
        with filepath.open(mode='rb') as f:
            headers = {'content-type': 'multipart/form-data'}
            r = self.clnt.post(
                ep,
                headers=headers,
                data={"path": folder},
                files={'file': f})
            return r

    def list_lab_networks(self, path):
        """
        Get one or all networks configured in a lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with configured networks
        """
        uri = "/networks"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_network(self, path, net_id):
        """
        retrieve details for a single network in a lab

        Args:
            path (str): the path to the lab
            net_id (str): unique id for the lab

        Returns:
            dict: dictionary with network details
        """
        uri = f"/networks/{net_id}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_network_by_name(self, path, name):
        """
        retrieve details for a single network using the
        lab name

        Args:
            path (str): the path to the lab
            net_id (str): unique id for the lab

        Returns:
            dict: dictionary with network details
        """
        networks = self.list_lab_networks(path)

        found = {}
        if networks:
            try:
                found = next(v for k, v in networks.items()
                             if v['name'] == name)
                return found
            except StopIteration:
                self.clnt.log.warning(f'Lab {name} not found')
        return found

    def list_lab_links(self, path):
        """
        Get all remote endpoint for both ethernet and serial interfaces

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with lab links
        """
        url = "/labs" + self.normalize_path(path) + "/links"
        links = self.clnt.get(url)
        return links

    def list_nodes(self, path: str) -> Dict:
        """
        List all nodes in the lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with all lab node details
        """
        url = "/labs" + self.normalize_path(path) + "/nodes"
        return self.clnt.get(url)

    def get_node(self, path: str, node_id: str) -> Dict:
        """
        Retrieve single node from lab by ID

        Args:
            path (str): the path to the lab
            node_id (str): unique ID assigned to node

        Returns:
            dict: dictionary with single lab node details
        """
        uri = f"/nodes/{str(node_id)}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_node_by_name(self, path: str, name: str) -> Dict:
        """
        Retrieve single node from lab by name

        Args:
            path (str): the path to the lab
            name (str): node name

        Returns:
            dict: dictionary with single lab node details

        """
        nodes = self.list_nodes(path)
        node = next((v for k, v in nodes.items() if v['name'] == name), {})
        return node

    def get_node_configs(self, path: str) -> Dict:
        """
        Return information about node start-up configs

        Args:
            path (str): the path to the lab

        Returns:
            dict:
        """
        url = "/labs" + self.normalize_path(path) + "/configs"
        configs = self.clnt.get(url)
        return configs

    def get_node_config_by_id(self, path: str, config_id: int) -> Dict:
        """
        Return information about a specific node given
        the configuration ID

        Args:
            path (str): the path to the lab
            config_id (str): unique ID for the config to retrieve

        Returns:
            dict: configuration data
        """
        uri = f"/configs/{config_id}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_node_config_by_name(self, path: str, node: str) -> Dict:
        """
        Return information about a specific node given
        the configuration ID

        Args:
            path (str): the path to the lab
            node (str): node name to retrieve configuration for

        Returns:
            dict: configuration data
        """
        configs = self.get_node_configs(path)

        # find node id using the name
        n_id = next((k for k, v in configs.items() if v['name'] == node), {})

        # get node config if we have ID
        if n_id:
            config = self.get_node_config_by_id(path, n_id)
            return config

        raise EvengApiError(f'could not find ID for {node}')

    def upload_node_config(
        self,
        path: str,
        node_id: int,
        config: str = "",
        enable: bool = False
    ):
        """
        Upload node's startup config.

        Args:
            path (str): the path to the lab
            node_id (str): node name to upload configuration for
            config (str): the configuration to upload
            enable (bool): enable the uploaded config

        Returns:
            dict: operation result response
        """
        # current_cfg = self.get_node_config_by_id(path, node_id)
        if node_id:
            uri = f"/configs/{node_id}"
            url = "/labs" + self.normalize_path(path) + uri
            payload = {"id": node_id, "data": config}
            resp = self.clnt.put(url, data=json.dumps(payload))
            return resp
        else:
            raise ValueError('Node ID is required.')

    @staticmethod
    def find_node_interface(name, intf_list):
        interfaces = list(intf_list)
        return next(((idx, i) for idx, i in enumerate(interfaces)
                    if i['name'] == name), None)
        # try:
        #     found = next((idx, i)
        #                  for idx, i in enumerate(interfaces)
        #                  if i['name'] == name)
        #     return found
        # except StopIteration:
        #     return None

    def connect_node(
        self,
        path: str,
        src: str = "",
        src_port: str = "",
        dst: str = "",
        dst_port: str = "",
        dst_type="network",
        media=""
    ) -> Dict:
        """Connect node to network or other node

        Args:
            path (str): lab path
            src (str, optional): source node name. Defaults to "".
            src_port (str, optional): source node port. Defaults to "".
            dst (str, optional): destination. Defaults to "".
            dst_port (str, optional): destination port. Defaults to "".
            dst_type (str, optional): destination type (node/network).
                Defaults to "network".
            media (str, optional): port media type. Defaults to "".

        Raises:
            ValueError: [description]

        Returns:
            Dict: [description]
        """
        r = None
        dest_types = ["network", "node"]

        if dst_type not in dest_types:
            msg = f"destination type not in allowed types: {dest_types}"
            raise ValueError(msg)

        # normalize lab path
        normpath = self.normalize_path(path)

        # Connect node to either cloud (network) or node
        if dst_type == "network":
            self.log.debug(f'{path}: Connecting node {src} to cloud {dst}')
            r = self.connect_node_to_cloud(
                normpath,
                src, src_port, dst,
                media=media)
        else:
            self.log.debug(f'{path}: Connecting node {src} to node {dst}')
            r = self.connect_node_to_node(
                normpath,
                src, src_port,
                dst, dst_port,
                media=media)
        return r

    def connect_p2p_interface(self, lab, node_id, interface, net_id):
        """
        Connect node interface to a network
        """
        uri = f"/nodes/{node_id}/interfaces"
        url = "/labs" + self.normalize_path(lab) + uri

        intf_id = interface[0]
        data = {intf_id: str(net_id)}

        # connect interfaces
        self.clnt.put(url, data=json.dumps(data))

        # set visibility for bridge to "0" to hide bridge in the GUI
        r2 = self.edit_lab_network(lab, net_id, data={"visibility": "0"})

        return r2

    def connect_node_to_cloud(self,
                              lab,
                              node_name,
                              node_port,
                              net_name,
                              media="ethernet"):
        node = self.get_node_by_name(lab, node_name)
        net = self.get_lab_network_by_name(lab, net_name)

        if node and net:
            node_id = node.get('id')
            node_port_lst = self.get_node_interfaces(lab, node_id).get(media)
            found_interface = self.find_node_interface(node_port,
                                                       node_port_lst)
            if not found_interface:
                raise(f'Interface {found_interface} does not exist.')

            # Network and interface IDs for the request data
            intf_id = str(found_interface[0])
            net_id = net.get("id")
            data = {intf_id: str(net_id)}

            uri = f"/nodes/{node_id}/interfaces"
            url = "/labs" + self.normalize_path(lab) + uri

            # connect interface to cloud
            r1 = self.clnt.put(url, data=json.dumps(data))
            return r1

        elif node:
            raise ValueError(f"network {net_name} not found or invalid")
        elif net:
            raise ValueError(f"node {node_name} not found or invalid")
        else:
            raise ValueError("invalid network and/or network")
        return

    def connect_node_to_node(self,
                             lab,
                             src_node_name,
                             src_node_i,
                             dst_node_name,
                             dst_node_i,
                             media="ethernet"):
        src_node = self.get_node_by_name(lab, src_node_name)
        dst_node = self.get_node_by_name(lab, dst_node_name)

        # Validate hosts
        if not all((src_node, dst_node)):
            raise ValueError("host(s) not found or invalid")

        # Node IDs
        src_node_id = src_node.get('id')
        dst_node_id = dst_node.get('id')

        if src_node_id and dst_node_id:
            # Get all current interfaces of type media ("ethernet" or "serial")
            src_node_ports = self.get_node_interfaces(
                lab, src_node_id).get(media)
            dst_node_ports = self.get_node_interfaces(
                lab, dst_node_id).get(media)

            # Extract interface dicts from list of interfaces
            src_intf = self.find_node_interface(src_node_i, src_node_ports)
            dst_intf = self.find_node_interface(dst_node_i, dst_node_ports)

            if src_intf and dst_intf:
                net_resp = self.add_lab_network(
                    lab,
                    network_type="bridge",
                    visibility="1")

                if net_resp is not None and net_resp.get('id'):
                    net_id = net_resp.get('id')
                    if net_id:
                        r1 = self.connect_p2p_interface(
                            lab,
                            src_node_id,
                            src_intf, net_id)
                        r2 = self.connect_p2p_interface(
                            lab,
                            dst_node_id,
                            dst_intf, net_id)
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

    def start_all_nodes(self, path):
        """
        Start one or all nodes configured in a lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with operation results
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/start"
        return self.clnt.get(url)

    def stop_all_nodes(self, path: str) -> Dict:
        """
        Stop one or all nodes configured in a lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with operation results

        sample output:
            {
                "code": 200,
                "message": "Nodes stopped (80050).",
                "status": "success"
            }
        """
        url = f"/labs{self.normalize_path(path)}/nodes/stop"
        return self.clnt.get(url)

    def start_node(self, path: str, node_id: int) -> Dict:
        """
        start single node in a lab

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to start

        Returns:
            dict: dictionary with operation results
                  sample: {
                        "code": 200,
                        "message": "Node started (80049).",
                        "status": "success"
                    }
        """
        uri = f"/nodes/{str(node_id)}/start"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def stop_node(self, path: str, node_id: int) -> Dict:
        """
        Stop single node in a lab

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to start

        Returns:
            dict: dictionary with operation results
                  sample: {
                    "code": 200,
                    "message": "Node stopped (80051).",
                    "status": "success"
                }
        """
        uri = f"/nodes/{str(node_id)}/stop"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def wipe_all_nodes(self, path):
        """
        Wipe one or all nodes configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with operation results
                  sample: {
                    "code": 200,
                    "message": "Nodes cleared (80052).",
                    "status": "success"
                  }
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/wipe"
        return self.clnt.get(url)

    def wipe_node(self, path: str, node_id: int) -> Dict:
        """
        Wipe single node configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to wipe

        Returns:
            dict: response dict
        """
        uri = f"/nodes/{node_id}/wipe"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def export_all_nodes(self, path: str) -> Dict:
        """
        Export one or all nodes configured in a lab.
        Exporting means saving the startup-config into
        the lab file.

        Args:
            path (str): the path to the lab

        Returns:
            dict: response dict
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/export"
        return self.clnt.get(url)

    def export_node(self, path: str, node_id: int) -> Dict:
        """
        Export node configuration. Exporting means
        saving the startup-config into the lab file.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to export

        Returns:
            dict: response dict
        """
        uri = f"/nodes/{node_id}/export"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.put(url)

    def get_node_interfaces(self, path: str, node_id: int):
        """
        Get configured interfaces from a node.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to export
        """
        uri = f"/nodes/{node_id}/interfaces"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_topology(self, lab_path: str) -> Dict:
        """Retrieve lab topology

        Args:
            lab_path (str): full path to lab. ex /my_lab.unl

        Returns:
            Dict: Response dictionary
        """
        url = "/labs" + self.normalize_path(lab_path) + "/topology"
        return self.clnt.get(url)

    def get_lab_pictures(self, lab_path: str):
        """Re

        Args:
            lab_path (str): [description]

        Returns:
            [type]: [description]
        """
        url = "/labs" + self.normalize_path(lab_path) + "/pictures"
        return self.clnt.get(url)

    def get_lab_picture_details(self, path, picture_id):
        """
        Retrieve single picture
        """
        uri = f"/pictures/{picture_id}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_path(self, path, name):
        fullpath = None
        if name and path:
            fullpath = (
                f"{path}/{name}.unl"
                if not name.endswith("unl")
                else f"{path}/{name}"
            )
        elif path:
            if not len(path.split('/')) > 1:
                raise ValueError(
                        "Invalid name or path. Please pass either"
                        "the name and folder path for the lab or pass"
                        "The full path to the lab"
                )
            fullpath = path
        return fullpath

    def lab_exists(self, lab_path):
        try:
            return self.get_lab(lab_path)
        except EvengHTTPError:
            return False

    def node_exists(self, path, nodename):
        exists = False
        node = self.get_node_by_name(path, nodename)
        if node is not None:
            exists = node.get('name') == nodename.lower()
        return exists

    def network_exists(self, path, name):
        exists = False
        net = self.get_lab_network_by_name(path, name)
        if net is not None:
            exists = net.get('name') == name
        return exists

    def create_lab(
        self,
        name: str,
        author: str = "",
        path: str = "/",
        version: int = 1,
        description: str = "",
        body: str = "",
    ) -> Dict:
        """Creates New lab on EVE-NG host

        Args:
            author (str, optional): lab author . Defaults to "".
            path (str, optional): parent folder(s). Defaults to "/".
            name (str, optional): lab name. Defaults to "".
            version (int, optional): lab version. Defaults to 1.
            description (str, optional): lab description. Defaults to "".
            body (str, optional): [description]. Defaults to "".

        Raises:
            EvengApiError: [description]
            EvengApiError: [description]

        Returns:
            Dict: Response object
        """
        if not name:
            raise ValueError('`name` is required')
        data = {
            "path": self.normalize_path(path),
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "body": body,
        }
        labpath = self.get_lab_path(path, name)
        if self.lab_exists(labpath):
            raise EvengApiError('Lab already exists')
        else:
            return self.clnt.post('/labs', data=json.dumps(data))

    def edit_lab(
        self,
        full_path: str,
        name: str = "",
        author: str = "",
        version: int = None,
        description: str = "",
        body: str = "",
    ) -> Dict:
        """
        Edit an existing lab. The request can set only a single
        parameter. Optional parameter can be reverted to the default
        setting an empty string “”.

        Args:
            full_path (str): full_path for lab. ex: /datacenter/lab1.unl
            name (str, optional): [description]. Defaults to "".
            author (str, optional): [description]. Defaults to "".
            version (int, optional): [description]. Defaults to None.
            description (str, optional): [description]. Defaults to "".
            body (str, optional): [description]. Defaults to "".

        Returns:
            Dict: [description]
        """
        params = ('name', 'author', 'version', 'description', 'body')
        data = {
            k: v for k, v in locals().items() if k in params and v
        }
        url = "/labs" + full_path
        return self.clnt.put(url, data=json.dumps(data))

    def delete_lab(self, name: str = "", path: str = "/"):
        """Delete lab from EVE-NG host

        Args:
            name (str, optional): [description]. Defaults to "".
            path (str, optional): [description]. Defaults to "/".

        Raises:
            EvengApiError: [description]

        Returns:
            [type]: [description]
        """
        labpath = self.get_lab_path(path, name)
        normpath = self.normalize_path(labpath)
        if self.lab_exists(labpath):
            url = '/labs' + normpath
            return self.clnt.delete(url)
        else:
            raise EvengApiError('Lab does not exists')

    def lock_lab(self, name="", path="/"):
        """Lock lab to prevent edits"""
        name = self.slugify(name) \
            if not name.endswith('unl') \
            else self.slugify(name.split('.')[0])
        url = '/labs' + self.normalize_path(path) + '/name/lock'
        resp = self.clnt.put(url)
        return resp

    def unlock_lab(self, name="", path="/"):
        """Unlock lab to allow edits
        """
        name = self.slugify(name) \
            if not name.endswith('unl') \
            else self.slugify(name.split('.')[0])
        url = '/labs' + self.normalize_path(path) + '/name/Unlock'
        resp = self.clnt.put(url)
        return resp

    def _get_network_types(self):
        network_types = set(NETWORK_TYPES)
        virtual_clouds = (f"pnet{x}" for x in range(VIRTUAL_CLOUD_COUNT))
        return network_types.union(virtual_clouds)

    @property
    def network_types(self):
        return self._get_network_types()

    def edit_lab_network(self, path, net_id, data=None):
        """
        Edit lab network

        Args:
            left (int):
            name (str):
            top (int):
            type (str):
            visibility (int): 0 or 1 to indicate visibility

        """
        url = '/labs' + self.normalize_path(path) + f'/networks/{net_id}'
        return self.clnt.put(url, data=json.dumps(data))

    def add_lab_network(self,
                        path="/",
                        network_type="",
                        visibility="0",
                        name="",
                        left="",
                        top="", **kwargs):
        """
        Add a new network to a lab

        Args:
            left (int): mergin from left, in percentage (i.e. 35%),
                default is a random value between 30% and 70%;
            name (str): network name (i.e. Core Network), default is
                  NetX (X = network_id)
            top (int):  margin from top, in percentage (i.e. 25%),
                default is a random value between 30% and 70%;
            type (int): see “List network types”

        Returns:
            dict: {
                    "code": 201,
                    "message": "Network has been added to the lab (60006).",
                    "status": "success"
                }
        """
        network_type = kwargs.get('network_type') or network_type
        if network_type not in self.network_types:
            raise ValueError(f'invalid network type: {network_type} \
                not member of set {self.network_types}')

        name = kwargs.get("name") or name
        data = {
            "left": kwargs.get("left") or left,
            "name": name,
            "top": kwargs.get("top") or top,
            "type": kwargs.get("type") or network_type,
            "visibility": kwargs.get("visibility") or visibility
        }
        url = '/labs' + self.normalize_path(path) + '/networks'

        if not self.network_exists(path, name):
            return self.clnt.post(url, data=json.dumps(data))
        else:
            raise EvengApiError('Network Already Exists')

    def delete_lab_network(self, name="", path="/"):
        try:
            int(name)
            url = '/labs' + self.normalize_path(path) + '/networks/' + name
        except ValueError:
            net = self.get_lab_network_by_name(path, name)
            if net is not None:
                net_id = net.get('id')
                uri = '/networks/' + str(net_id)
                url = '/labs' + self.normalize_path(path) + uri
            else:
                return ValueError(f"network with name/id '{name}' not found")
        return self.clnt.delete(url)

    def add_node(
        self,
        path: str,
        name: str = "",
        delay: int = 0,
        node_type: str = "qemu",
        template: str = "",
        icon: str = "",
        image: str = "",
        top: int = 0,
        left: int = 0,
        ethernet: int = 2,
        serial: int = 2,
        config: str = "Unconfigured",
        ram: int = 1024,
        nvram: int = 1024,
        console: str = "telnet",
        cpu: int = 1,
        uuid: str = "",
        idlepc: str = "",
        slot: str = ""
    ) -> Dict:
        """ Add a new node to a lab

        Args:
            path (str): lab path
            name (str): node name (ex: “Core1”), default is NodeX (X = node_id)
            config (str): can be 'Unconfigured' or 'Saved'
            delay (int): seconds to wait before starting the node, default is 0
            icon (str): filename for icon used to display the node, default
                is Router.png; (located in /opt/unetlab/html/images/icons/)
            image (str): image used to start the node, default is latest
                         included in “List node templates”;
            left (int): mergin from left, in percentage (i.e. 35%), default
                        is a random value between 30% and 70%;
            ram (int): MB of RAM configured for the node, default is 1024;
            template (str): (mandatory) - template for device type
            top (int): margin from top, in percentage (i.e. 25%),
                       default is a random value between 30% and 70%;
            type (str): (mandatory) value ccan be one of
                        ['iol', 'dynamips', 'qemu'].
            ethernet (int): number of ethernet porgroups (each portgroup
                            configures four interfaces), default is 2;
            nvram (int): size of NVRAM in KB, default is 1024;
            serial (int): num of serial porgroups (each portgroup configures
                          four interfaces), default is 2.

            # Dynamips
            idlepc: value used for Dynamips optimization (i.e. 0x80369ac4),
                    default is 0x0 (no optimization);
            nvram: size of NVRAM in KB, default is 1024;
            slot (str): 0-9]+ the module configured in a specific slot
                        (i.e. slot1=NM-1FE-TX).

            # Parameters for QEMU nodes
            console (str): can be telnet or vnc, default is telnet;
            cpu (int): number of configured CPU, default is 1;
            uuid (str): UUID configured, default is a random UUID
                    (i.e. 641a4800-1b19-427c-ae87-4a8ee90b7790).
        """
        url = '/labs' + self.normalize_path(path) + "/nodes"

        node_data = dict(
            name=name, type=node_type, template=template,
            config=config, delay=delay, left=left, top=top, ram=ram,
            nvram=nvram
        )
        # get template data from EVE-NG
        if template_data := self.node_template_detail(template):
            template_data = template_data.get('options')

        # set template details or insert defaults from template data
        node_data.update({
            'icon': icon or template_data.get('icon')['value'],
            'image': image or template_data.get('image')['value'],
            'ethernet': (
                int(ethernet) or
                template_data.get('ethernet')['value'],
            ),
            'serial': (
                int(serial) or
                template_data.get('serial')['value'],
            ),
            'ram': ram or template_data.get('ram')['value']
        })

        if node_type == "qemu":
            node_data.update({
                "console": console,
                "cpu": cpu,
                "uuid": uuid
            })

        if node_data == "dynamips":
            node_data.update({
                "idlepc": idlepc,
                "slot": slot,
                "nvram": nvram
            })

        return self.clnt.post(url, data=json.dumps(node_data))

    def delete_node(self, path: str, node_id: int) -> Dict:
        """Delete node from lab

        Args:
            path (str): lab path
            node_id (int): Node ID to remove

        Returns:
            dict: response dictionary
        """
        url = f"/labs{self.normalize_path(path)}/nodes/{node_id}"
        return self.clnt.delete(url)

    @staticmethod
    def slugify(string):
        return string.lower().replace(' ', '_')
