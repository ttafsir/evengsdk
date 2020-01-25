#! /usr/bin/env python
import copy
import json
import os

from evengsdk.exceptions import EvengApiError
from urllib.parse import quote_plus

NETWORK_TYPES = ["bridge","ovs"]
VIRTUAL_CLOUD_COUNT = 9

class EvengApi:

    def __init__(self, clnt, timeout=30):
        """ Initialize the class.
            Args:
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
        """
        Get server status

        Returns:
            dict: server status details
        """
        return self.clnt.get('/status')

    def list_node_templates(self):
        """
        List details for all node template

        Returns:
            dict: dictionary of node templates

        example:
            {
                'a10': 'A10 vThunder.missing',
                'acs': 'Cisco ACS.missing',
                'alteon': 'Radware AlteonVA.missing',
                'ampcloud': 'Cisco AMP Cloud.missing',
            }
        """
        return self.clnt.get('/list/templates/')

    def node_template_detail(self, node_type):
        """
        List details for single node template
        All available images for the selected template will be included in the output

        Args:
            node_type (str): type of node

        """
        return self.clnt.get(f'/list/templates/{node_type}')

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
        user = self.clnt.get(f"/users/{username}")
        return user or {}

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
            expiration(str): date until the user is valid (UNIX timestamp) or -1 if never expires;
            name(str): a description for the user, usually salutation;
            password (string): the user password used to login;
            role(string): choices are ['user', 'admin']
            username (str): a unique alphanumeric string used to login

        Returns:
            Dictionary with user data

        """
        username = username or kwargs.get('username')
        password = password or kwargs.get('password')
        if not (username and password):
            raise ValueError('Missing username and/or password for user')
        else:
            existing = self.get_user(username)
            if not existing:
                user = {
                    "username": username,
                    "name": kwargs.get('name') or name,
                    "email": kwargs.get('email') or email,
                    "password": password,
                    "role": kwargs.get('role') or role,
                    "expiration": "-1"
                }
                self.clnt.log.debug('creating new user {}'.format(username))
                data = json.dumps(user)
                return self.clnt.post('/users', data=data)
            else:
                raise EvengApiError('User already exists')
        return

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
        user = self.get_user(username)

        updated_user = {}

        if user and data:
            updated_user = copy.deepcopy(user)
            updated_user.update(data)
            response = self.clnt.put(url, data=json.dumps(updated_user))
            return response
        else:
            raise EvengApiError('User Does not exist')

    def delete_user(self, username):
        """
        Delete EVE-NG user

        Args:
            username (str): username to delete

        Returns:
            dict: dictionary with the status of the DELETE operation
                  sample output:
                   {'code': 201, 'status': 'success', 'message': 'User saved (60042).'}
        """
        existing = self.get_user(username)
        if existing:
            response = self.clnt.delete(f'/users/{username}')
            return response
        else:
            raise EvengApiError('User does not exists')

    def list_networks(self):
        """
        List network types

        Returns:
            dict: dictionary of networks
        """
        networks = self.clnt.get('/list/networks')
        return networks or {}

    # def list_folders(self):
    #     """
    #     List folders for user
    #     """
    #     return self.clnt.get(f"/folders/")

    # def add_folder(self, name):
    #     """
    #     Add a new folder for user account
    #     """
    #     slug = self.slugify(name)
    #     data = {"path": f"/{slug}", "name": slug}
    #     return self.clnt.get("/folders", data=json.dumps(data))

    # def move_folder(self, old_path, new_path):
    #     """
    #     Move/rename an existent folder
    #     """
    #     data = {'path': new_path}
    #     endpoint = f"/folders/{old_path}"
    #     return self.put_handle_response(endpoint, data=json.dumps(data))

    # def delete_folder(self, path):
    #     """
    #     Delete an existing folder
    #     """
    #     return self.del_handle_response(f"/folders/{path}")

    @staticmethod
    def normalize_path(path):
        path = path.lstrip("/")
        dir_, file_ = os.path.split(path)
        q_plus = quote_plus(dir_)
        normpath = "/".join((q_plus, file_))
        return normpath

    def get_lab(self, path):
        """
        get details for a single lab. Returns empty dict
        if lab does not exist.

        Args:
            path (str): the path of the lab

        Returns:
            dict: dictionary with lab details
        """
        normpath = self.normalize_path(path)
        if not normpath.endswith(".unl"):
            normpath = normpath + ".unl"
        url = f"/labs/{normpath}"
        lab_details = self.clnt.get(url)
        return lab_details or {}

    def list_lab_networks(self, path):
        """
        Get one or all networks configured in a lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with configured networks
        """
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/networks"
        lab_networks = self.clnt.get(url)
        return lab_networks or {}

    def get_lab_network(self, path, net_id):
        """
        retrieve details for a single network in a lab

        Args:
            path (str): the path to the lab
            net_id (str): unique id for the lab

        Returns:
            dict: dictionary with network details
        """
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/networks/{net_id}"
        network = self.clnt.get(url)
        return network or {}

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
        networks  = self.list_lab_networks(path)
        print(networks)

        found = {}
        if networks:
            try:
                found = next(v for k,v in networks.items() if v['name'] == name)
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/links"
        links =  self.clnt.get(url)
        return links or {}

    def list_nodes(self, path):
        """
        List all nodes in the lab

        Args:
            path (str): the path to the lab

        Returns:
            dict: dictionary with all lab node details
        """
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes"
        nodes = self.clnt.get(url)
        return nodes or {}

    def get_node(self, path, node_id):
        """
        Retrieve single node from lab by ID

        Args:
            path (str): the path to the lab
            node_id (str): unique ID assigned to node

        Returns:
            dict: dictionary with single lab node details

        """
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}"
        node =  self.clnt.get(url)
        return node or {}

    def get_node_by_name(self, path, name):
        """
        Retrieve single node from lab by name

        Args:
            path (str): the path to the lab
            name (str): node name

        Returns:
            dict: dictionary with single lab node details

        """
        nodes  = self.list_nodes(path)
        found = {}
        if nodes:
            try:
                found = next(v for k,v in nodes.items() if v['name'] == name)
            except StopIteration:
                self.clnt.log.warning(f'node {name} not found')
        else:
            self.clnt.log.warning(f'0 nodes found in lab')
        return found

    def get_node_configs(self, path):
        """
        Return information about node configs

        Args:
            path (str): the path to the lab

        Returns:
            dict:
        """
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/configs"
        config_data =  self.clnt.get(url)
        return config_data or {}

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
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/configs/{config_id}"
        config_data = self.clnt.get(url)
        return config_data or {}

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
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/configs/"

        data = {}
        try:
            found_id = next(k for k,v in configs.items() if v['name'] == node_name)
            if found_id:
                data = self.get_node_config_by_id(path, found_id)
                print(data)
            return data
        except StopIteration:
            self.clnt.log.warning(f'no configuration for {node_name} found')
        return data

    def upload_node_config(self, path, node_id, config=None):
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
        current_cfg = self.get_node_config_by_id(path, node_id)

        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/configs/{node_id}"
        payload = {
            "id": node_id,
            "data": config
        }
        resp = self.clnt.put(url, data=json.dumps(payload))
        return resp

    @staticmethod
    def find_node_interface(name, intf_list):
        interfaces = list(intf_list)
        try:
            found = next( (idx, i) for idx, i in enumerate(interfaces) if i['name'] == name)
            return found
        except StopIteration:
            return None

    def connect_node(self,
                     lab,
                     src="",
                     src_intf="",
                     dst="",
                     dst_intf="",
                     dst_type="network",
                     media_type=""):
        r = None
        dest_types = ["network", "node"]
        if dst_type not in dest_types:
            raise ValueError("destination type not in allowed types: {dest_types}")

        self.clnt.log.debug(f"connecting {src} to {dst}")
        if dst_type == "network":
            r = self.connect_node_to_cloud(lab, src, src_intf, dst, media_type=media_type)
        else:
            r= self.connect_node_to_node(lab, src, src_intf, dst, dst_intf, media_type=media_type)
        return r

    def connect_p2p_interface(self, lab, node_id, interface, net_id):
        """
        Connect node interface to a network
        """
        normpath = self.normalize_path(lab)
        url = "/labs/" + normpath + f"/nodes/{node_id}/interfaces"

        intf_id = interface[0]
        data = {intf_id: str(net_id)}

        # connect interfaces
        r1 = self.clnt.put(url, data=json.dumps(data))

        # set visibility for bridge to "0" to hide bridge
        r2 = self.edit_lab_network(lab, net_id, data={"visibility": "0"})

        return r1

    def connect_node_to_cloud(self, lab, node_name, node_intf, net_name, media_type="ethernet"):
        node = self.get_node_by_name(lab, node_name)
        net = self.get_lab_network_by_name(lab, net_name)

        if node and net:
            node_id = node.get('id')
            node_intf_lst = self.get_node_interfaces(lab, node_id).get(media_type)
            node_intf = self.find_node_interface(node_intf, node_intf_lst)

            # Network and interface IDs for the request data
            intf_id = str(node_intf[0])
            net_id = net.get("id")
            data = {intf_id: str(net_id) }

            # Build url for request
            normpath = self.normalize_path(lab)
            url = "/labs/" + normpath + f"/nodes/{node_id}/interfaces"

            # connect interface to cloud
            r1 = self.put_handle_response(url, data=json.dumps(data))
            return r1

        elif node:
            raise ValueError(f"network {net_name} not found or invalid")
        elif cloud:
            raise ValueError(f"node {node_name} not found or invalid")
        else:
            raise ValueError(f"invalid network and/or network")
        return

    def connect_node_to_node(self, lab, src_node_name, src_node_i, dst_node_name, dst_node_i, media_type="ethernet"):
        src_node = self.get_node_by_name(lab, src_node_name)
        dst_node = self.get_node_by_name(lab, dst_node_name)

        # Validate hosts
        if not all((src_node,dst_node)):
            raise ValueError("host(s) not found or invalid")

        # Node IDs
        src_node_id = src_node.get('id')
        dst_node_id = dst_node.get('id')

        if src_node_id and dst_node_id:
            # Get all current interfaces of type media_type ("ethernet" or "serial")
            src_node_intfs = self.get_node_interfaces(lab, src_node_id).get(media_type)
            dst_node_intfs = self.get_node_interfaces(lab, dst_node_id).get(media_type)

            # Extract interface dicts from list of interfaces
            src_intf = self.find_node_interface(src_node_i, src_node_intfs)
            dst_intf = self.find_node_interface(dst_node_i, dst_node_intfs)

            if src_intf and dst_intf:
                net = None
                net_resp = self.add_lab_network(lab, network_type="bridge", visibility="1")
                if net_resp.get('status') == 'success':
                    net_id = self.get_response_data(net_resp).get("data").get("id")
                    if net_id:
                        r1 = self.connect_p2p_interface(lab, src_node_id, src_intf, net_id)
                        r2 = self.connect_p2p_interface(lab, dst_node_id, dst_intf, net_id)
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
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/start"
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/stop"
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/{node_id}/start"
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/{node_id}/stop"
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
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/wipe"
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/{node_id}/wipe"
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/export"
        resp = self.clnt.get(url)
        print(resp)
        return resp

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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/{node_id}/export"
        resp = self.clnt.get(url)
        print(node_id, url, resp)
        return resp

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
                                "name": "Gi0/1",
                                "network_id": 3
                            },
                            {
                                "name": "Gi0/2",
                                "network_id": 5
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
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes/{node_id}/interfaces"
        interfaces = self.clnt.get(url)
        return interfaces or {}

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
                    },
                    {
                        "destination": "network1",
                        "destination_label": "",
                        "destination_type": "network",
                        "source": "node3",
                        "source_label": "e0/0",
                        "source_type": "node",
                        "type": "ethernet"
                    }
                ],
                "message": "Topology loaded",
                "status": "success"
            }
        """
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/topology"
        topology = self.clnt.get(url)
        return topology or {}

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
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/pictures"
        return self.get_handle_response(url)

    def get_lab_picture_details(self, path, picture_id):
        """
        A single picture can be retrieved

            sample output:
                {
                    "code": 200,
                    "data": {
                        "height": 201,
                        "id": "1",
                        "map": "<area shape='circle' coords='248,66,30' href='telnet://:'>\n",
                        "name": "RR Logo",
                        "type": "image/png",
                        "width": 410
                    },
                    "message": "Picture loaded",
                    "status": "success"
                }
        """
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/pictures/{picture_id}"
        return self.get_handle_response(url)

    def get_lab_picture_data():
        # curl -s -c /tmp/cookie -b /tmp/cookie -X GET -H 'Content-type: application/json'
        # http://127.0.0.1/api/labs/User1/Lab%201.unl/pictures/1/data/32/32

        # The resized picture is generated with original aspect-ratio using given values as maximum witdh/lenght.
        pass

    def create_lab(self, username, path="/", name="", version="1", description="", body="", **kwargs):
        """ Create a new lab

        payload = {
            "path":"/User1/Folder 3",
            "name":"New Lab",
            "version":"1",
            "author":"User1 Lastname",
            "description":"A new demo lab",
            "body":"Lab usage and guide"
        }

        sample response:
            {
                "code": 200,
                "message": "Lab has been created (60019).",
                "status": "success"
            }
        """
        user = self.get_user(username)

        if user:
            author = user.get('name')
            path = kwargs.get('path') or path
            name = kwargs.get('name') or name

            normpath = self.normalize_path(path)
            data = {
                "path": normpath,
                "name": self.slugify(name),
                "version": kwargs.get('version') or version,
                "author": author,
                "description": kwargs.get('version') or description,
                "body": kwargs.get('body') or body,
            }
            return self.post_handle_response('/labs', data=json.dumps(data))
        else:
            raise(f"user {username} not found")

    def edit_lab(self, path, name="", version="", author="", description="", **kwargs):
        """
        Edit an existing lab. The request can set only one single
        parameter. Optional parameter can be reverted to the default
        setting an empty string “”.

            payload = {
                "name":"Different Lab",
                "version":"2",
                "author":"AD",
                "description":"A different demo lab"
            }

            sample output:
                {
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
        url = "/labs/" + normpath
        return self.put_handle_response(url, data=json.dumps(data))

    def move_lab():
        # Move an existing lab to a different folder
        # curl -s -c /tmp/cookie -b /tmp/cookie -X PUT -d '{"path":"/User1/Folder 2"}' -H 'Content-type: application/json' http://127.0.0.1/api/labs/User1/Folder%203/New%20Lab.unl/move

        # {
        #     "code": 200,
        #     "message": "Lab moved (60035).",
        #     "status": "success"
        # }
        pass

    def delete_lab(self, path):
        """ Delete an existent lab

            sample output:
                {
                    "code": 200,
                    "message": "Lab has been deleted (60022).",
                    "status": "success"
                }
        """
        normpath = self.normalize_path(path)
        if not normpath.endswith(".unl"):
            normpath = normpath + ".unl"

        try:
            existing = self.get_lab(path)
        except EvengApiError:
            return {"message": "does not exist"}

        if existing:
            path = '/labs' + normpath
            return self.del_handle_response(path)
        else:
            raise EvengApiError('lab does not exists')

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
        data = {
            "left": kwargs.get("left") or left,
            "name": kwargs.get("name") or name,
            "top": kwargs.get("top") or top,
            "type": kwargs.get("type") or network_type,
            "visibility": kwargs.get("visibility") or visibility
        }
        """
        normpath = self.normalize_path(path)
        url = '/labs/' + normpath + f'/networks/{net_id}'
        return self.put_handle_response(url, data=json.dumps(data))


    def add_lab_network(self, path, network_type="", visibility="0", name="", left="", top="", **kwargs):
        """
        Add a new network to a lab

        Args:
            left: mergin from left, in percentage (i.e. 35%), default is a
                  random value between 30% and 70%;
            name: network name (i.e. Core Network), default is
                  NetX (X = network_id)
            top:  margin from top, in percentage (i.e. 25%), default is a
                  random value between 30% and 70%;
            type (mandatory): see “List network types”

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

        data = {
            "left": kwargs.get("left") or left,
            "name": kwargs.get("name") or name,
            "top": kwargs.get("top") or top,
            "type": kwargs.get("type") or network_type,
            "visibility": kwargs.get("visibility") or visibility
        }
        normpath = self.normalize_path(path)
        url = '/labs/' + normpath + '/networks'
        return self.post_handle_response(url, data=json.dumps(data))

    def delete_lab_network(self, path, name):
        normpath = self.normalize_path(path)
        url = None
        try:
            int(name)
            url = '/labs/' + normpath + '/networks/' + name
        except ValueError:
            net = self.get_lab_network_by_name(path, name)
            if net is not None:
                net_id = net.get('id')
                url = '/labs/' + normpath + '/networks/' + str(net_id)
            else:
                return ValueError(f"network with name/id '{name}' not found")
        return self.del_handle_response(url)

    def add_node(self, path, delay=0, name="", node_type="", template="",
                     top="", left="", console="telnet", config="Unconfigured",
                     image="", **kwargs):
        """ Add a new node to a lab

        Args:

            name (str): node name (i.e. “Core1”), default is NodeX (X = node_id);
            config (str): can be 'Unconfigured' or 'Saved', default is Unconfigured;
            delay (int): seconds to wait before starting the node, default is 0;
            icon (str): filename for icon (located under /opt/unetlab/html/images/icons/) used to display the node, default is Router.png;
            image: image used to start the node, default is latest included in “List node templates”;
            left: mergin from left, in percentage (i.e. 35%), default is a random value between 30% and 70%;
            ram: MB of RAM configured for the node, default is 1024;
            template (mandatory): see “List node templates”;
            top: margin from top, in percentage (i.e. 25%), default is a random value between 30% and 70%;
            type (mandatory): can be iol, dynamips or qemu.
            Parameters for IOL nodes:
            ethernet: number of ethernet porgroups (each portgroup configures four interfaces), default is 2;
            nvram: size of NVRAM in KB, default is 1024;
            serial: number of serial porgroups (each portgroup configures four interfaces), default is 2.

            # for Dynamips nodes:
            idlepc: value used for Dynamips optimization (i.e. 0x80369ac4), default is 0x0 (no optimization);
            nvram: size of NVRAM in KB, default is 1024;
            slot[0-9]+: the module configured in a specific slot (i.e. slot1=NM-1FE-TX).

            # Parameters for QEMU nodes:
            console: can be telnet or vnc, default is telnet;
            cpu: number of configured CPU, default is 1;
            ethernet: number of ethernet interfaces, default is 4;
            uuid: UUID configured, default is a random UUID (i.e. 641a4800-1b19-427c-ae87-4a8ee90b7790).
        """
        normpath = self.normalize_path(path)
        url = f"/labs/{normpath}/nodes"

        template = kwargs.get("template") or template
        node_template_details = self.node_template_detail(template)

        icon = kwargs.get("icon") or node_template_details.get("icon")["value"]
        ethernet = kwargs.get("ethernet") or node_template_details.get("ethernet")["value"]
        ram = kwargs.get("ram") or node_template_details.get("ram")["value"]
        image = kwargs.get("image") or node_template_details.get("image")["value"]
        cpu = kwargs.get("cpu") or node_template_details.get("cpu")["value"]

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
        resp = self.clnt.post(url, data=json.dumps(data))
        return resp or {}

    @staticmethod
    def slugify(string):
        return string.lower().replace(' ', '_')