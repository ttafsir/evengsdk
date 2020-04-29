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


from urllib.parse import quote_plus
from requests.exceptions import HTTPError

from evengsdk.exceptions import EvengApiError

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

    def node_template_detail(self, node_type):
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
        try:
            r = self.clnt.get(f"/users/{username}")
            return r
        except HTTPError:
            return {}

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
        folders = self.clnt.get(f"/folders/")
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
        if path:
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

    def export_lab(self, path, filename='lab_export.zip'):
        """
        Export a lab as a .unl file

        Args:
            path (str): the path of the lab

        Returns:
            file: zip file with exported lab
        """
        url = f"/export"
        lab_filepath = Path(path)

        payload = {
            '0': str(lab_filepath),
            'path': str(lab_filepath.parent)
        }

        resp = self.clnt.post(url, data=json.dumps(payload))
        if resp:
            client = self.clnt
            download_url = f"http://{client.host}:{client.port}{resp}"
            _, r = self.clnt.get(download_url)

            with open(filename, 'wb') as handle:
                handle.write(r.content)

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
        url = f"/labs" + self.normalize_path(path) + "/links"
        links = self.clnt.get(url)
        return links

    def list_nodes(self, path):
        """
        List all nodes in the lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with all lab node details
        """
        uri = "/nodes"
        url = "/labs" + self.normalize_path(path) + uri
        nodes = self.clnt.get(url)
        return nodes

    def get_node(self, path, node_id):
        """
        Retrieve single node from lab by ID

        Args:
            path (str): the path to the lab
            node_id (str): unique ID assigned to node

        Returns:
            dict: dictionary with single lab node details

        """
        uri = f"/nodes/{node_id}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_node_by_name(self, path, name):
        """
        Retrieve single node from lab by name

        Args:
            path (str): the path to the lab
            name (str): node name

        Returns:
            dict: dictionary with single lab node details

        """
        nodes = self.list_nodes(path)
        found = None
        if nodes:
            try:
                found = next(v for k, v in nodes.items() if v['name'] == name)
            except StopIteration:
                self.clnt.log.warning(f'node {name} not found')
        else:
            self.clnt.log.warning(f'no nodes found in lab')
        return found

    def get_node_configs(self, path):
        """
        Return information about node configs

        Args:
            path (str): the path to the lab

        Returns:
            dict:
        """
        url = "/labs" + self.normalize_path(path) + f"/configs"
        configs = self.clnt.get(url)
        return configs

    def get_node_config_by_id(self, path, config_id):
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

    def get_node_config_by_name(self, path, node_name):
        """
        Return information about a specific node given
        the configuration ID

        Args:
            path (str): the path to the lab
            node_name (str): node name to retrieve configuration for

        Returns:
            dict: configuration data
        """
        configs = self.get_node_configs(path)
        data = {}
        try:
            found_id = next(k for k, v in configs.items()
                            if v['name'] == node_name)
            if found_id:
                data = self.get_node_config_by_id(path, found_id)
            return data
        except StopIteration:
            self.clnt.log.warning(f'no configuration for {node_name} found')
        return data

    def upload_node_config(self, path, node_id, config=None, enable=False):
        """
        Upload node's startup config.

        Args:
            path (str): the path to the lab
            node_id (str): node name to upload configuration for
            config (str): the configuration to upload

        Returns:
            dict: operation result
                sample: {
                'code': 201,
                'message': 'Lab has been saved (60023).',
                'status': 'success'
                }
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
        try:
            found = next((idx, i)
                         for idx, i in enumerate(interfaces)
                         if i['name'] == name)
            return found
        except StopIteration:
            return None

    def connect_node(self,
                     lab,
                     src="",
                     src_port="",
                     dst="",
                     dst_port="",
                     dst_type="network",
                     media=""):
        r = None
        dest_types = ["network", "node"]

        if dst_type not in dest_types:
            msg = f"destination type not in allowed types: {dest_types}"
            raise ValueError(msg)

        # normalize lab path
        normpath = self.normalize_path(lab)

        # Connect node to either cloud (network) or node
        if dst_type == "network":
            self.log.debug(f'{lab}: Connecting node {src} to cloud {dst}')
            r = self.connect_node_to_cloud(
                normpath,
                src, src_port, dst,
                media=media)
        else:
            self.log.debug(f'{lab}: Connecting node {src} to node {dst}')
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
            raise ValueError(f"invalid network and/or network")
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
        url = "/labs" + self.normalize_path(path) + f"/nodes/start"
        return self.clnt.get(url)

    def stop_all_nodes(self, path):
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
        url = f"/labs" + self.normalize_path(path) + "/nodes/stop"
        return self.clnt.get(url)

    def start_node(self, path, node_id):
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
        uri = f"/nodes/{node_id}/start"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def stop_node(self, path, node_id):
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
        uri = f"/nodes/{node_id}/stop"
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

    def wipe_node(self, path, node_id):
        """
        Wipe single node configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to wipe

        Returns:
            dict: {
                    "code": 200,
                    "message": "Node cleared (80053).",
                    "status": "success"
                }
        """
        uri = f"/nodes/{node_id}/wipe"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def export_all_nodes(self, path):
        """
        Export one or all nodes configured in a lab.
        Exporting means saving the startup-config into
        the lab file.

        Args:
            path (str): the path to the lab

        Returns:
            dict: {
                    "code": 200,
                    "message": "Nodes exported (80057).",
                    "status": "success"
                }
        """
        url = "/labs" + self.normalize_path(path) + "/nodes/export"
        return self.clnt.get(url)

    def export_node(self, path, node_id):
        """
        Export node configuration. Exporting means
        saving the startup-config into the lab file.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to export

        Returns:
            dict: {
                "code": 200,
                "message": "Node exported (80058).",
                "status": "success"
            }
        """
        uri = f"/nodes/{node_id}/export"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_node_interfaces(self, path, node_id):
        """
        Get configured interfaces from a node.

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to export

        Returns:
            dict: {
                    "code": 200,
                    "data": {
                        "ethernet": [
                            {
                                "name": "Gi0/0",
                                "network_id": 1
                            },
                            {
                                "name": "Gi0/3",
                                "network_id": 0
                            }
                        ],
                        "serial": []
                    },
                    "message": "Successfully listed node interfaces (60030).",
                    "status": "success"
            }
        """
        uri = f"/nodes/{node_id}/interfaces"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def get_lab_topology(self, path):
        """
        Get the lab topology

        Args:
            path (str): the path to the lab
            node_id (str): ID for node to export

        Returns:
            dict: {
                "code": "200",
                "data": [
                    {
                        "destination": "network1",
                        "destination_label": "",
                        "destination_type": "network",
                        "source": "node1",
                        "source_label": "Gi0/0",
                        "source_type": "node",
                        "type": "ethernet"
                    },
                    {
                        "destination": "network1",
                        "destination_label": "",
                        "destination_type": "network",
                        "source": "node2",
                        "source_label": "Gi0/0",
                        "source_type": "node",
                        "type": "ethernet"
                    }
                ],
                "message": "Topology loaded",
                "status": "success"
            }
        """
        url = "/labs" + self.normalize_path(path) + "/topology"
        r = self.clnt.get(url)
        return r

    def get_lab_pictures(self, path):
        """
        Get one or all pictures configured in a lab

        sample output:
            {
                "code": 200,
                "data": {
                    "1": {
                        "height": 201,
                        "id": 1,
                        "name": "RR Logo",
                        "type": "image/png",
                        "width": 410
                    }
                },
                "message": "Successfully listed pictures (60028).",
                "status": "success"
            }
        """
        url = "/labs" + self.normalize_path(path) + f"/pictures"
        return self.clnt.get(url)

    def get_lab_picture_details(self, path, picture_id):
        """
        Retrieve single picture
        """
        uri = f"/pictures/{picture_id}"
        url = "/labs" + self.normalize_path(path) + uri
        return self.clnt.get(url)

    def lab_exists(self, path, name):
        exists = False
        fullpath = path + name.lower() + '.unl'
        lab = self.get_lab(fullpath)
        if lab is not None:
            exists = lab.get('name') == name.lower()
        return exists

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

    def create_lab(self,
                   username,
                   path="/",
                   name="",
                   version=1,
                   description="",
                   body="",
                   **kwargs):
        """Create a new lab

        Args:
            username (str):
            path (str):
            name (str):
            version (int):
            description (str):
            body (str):

        Returns:

        """
        user = self.get_user(username)
        if user:
            author = user.get('name')
            path = kwargs.get('path') or path
            name = kwargs.get('name') or name

            normpath = self.normalize_path(path)
            data = {
                "path": normpath,
                "name":
                    self.slugify(name)
                    if not name.endswith('unl')
                    else self.slugify(name.split('.')[0]),
                "version": kwargs.get('version') or version,
                "author": author,
                "description": kwargs.get('version') or description,
                "body": kwargs.get('body') or body,
            }

            if self.lab_exists(path, name):
                raise EvengApiError('Lab already exists')
            else:
                resp = self.clnt.post('/labs', data=json.dumps(data))
                return resp
        else:
            raise EvengApiError(f"user {username} not found")

    def edit_lab(self,
                 path,
                 name="",
                 version="",
                 author="",
                 description="",
                 **kwargs):
        """
        Edit an existing lab. The request can set only one single
        parameter. Optional parameter can be reverted to the default
        setting an empty string “”.

        Args:
            path (str): path to lab on EVE-NG host. ex /MYLABS/lab1.unl
            version (int): version of the lab
            author (str): name of the author
            descritpion (str): a description for the lab

        Returns:
            dict: {
                "code": 200,
                "message": "Lab has been saved (60023).",
                "status": "success"
            }
        """
        normpath = self.normalize_path(path)
        name = kwargs.get("name") or name
        data = {
            "name": self.slugify(name),
            "version": kwargs.get("version") or version,
            "author": kwargs.get("author") or author,
            "description": kwargs.get("description") or description,
        }
        url = "/labs" + normpath
        return self.clnt.put(url, data=json.dumps(data))

    def delete_lab(self, name="", path="/"):
        """
        Delete an existent lab

            sample output:
                {
                    "code": 200,
                    "message": "Lab has been deleted (60022).",
                    "status": "success"
                }
        """
        normpath = self.normalize_path(path)
        if self.lab_exists(path, name.lower()):
            url = '/labs' + normpath + name.lower() + '.unl'
            resp = self.clnt.delete(url)
            return resp
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

    def add_node(self, path, delay=0, name="", node_type="", template="",
                 top="", left="", console="telnet", config="Unconfigured",
                 image="", **kwargs):
        """ Add a new node to a lab
        Args:

            name (str): node name (i.e. “Core1”), default is
                        NodeX (X = node_id);
            config (str): can be 'Unconfigured' or 'Saved', default
                          is Unconfigured;
            delay (int): seconds to wait before starting the node,
                        default is 0;
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

        template = kwargs.get("template") or template
        resp = self.node_template_detail(template)
        template_details = resp.get('options')

        icon = kwargs.get("icon") \
            or template_details.get("icon")["value"]
        ethernet = kwargs.get("ethernet") \
            or template_details.get("ethernet")["value"]
        ram = kwargs.get("ram") \
            or template_details.get("ram")["value"]
        image = kwargs.get("image") \
            or template_details.get("image")["value"]
        cpu = kwargs.get("cpu") \
            or template_details.get("cpu")["value"]

        data = {
            "type": node_type,
            "template": template,
            "config": kwargs.get("config") or config,
            "delay": kwargs.get("delay") or delay,
            "icon": icon,
            "image": image,
            "name": kwargs.get("name") or name,
            "left": kwargs.get("left") or left,
            "top": kwargs.get("top") or top,
            "ram": ram,
            "cpu": cpu,
            "console": kwargs.get("console") or console,
            "ethernet": int(ethernet),
        }
        resp = {}
        if not self.node_exists(path, name):
            resp = self.clnt.post(url, data=json.dumps(data))
        return resp

    @staticmethod
    def slugify(string):
        return string.lower().replace(' ', '_')
