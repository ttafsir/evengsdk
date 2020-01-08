#! /usr/bin/env python
import copy
import json
import os

# from ansible.module_utils.six.moves.urllib.parse import urlencode, quote_plus
from evengsdk.exceptions import EvengApiError

NETWORK_TYPES = ["bridge","ovs"]
VIRTUAL_CLOUD_COUNT = 9

class EvengApi:

    def __init__(self, clnt, timeout=30):
        ''' Initialize the class.
            Args:
                clnt (obj): A EvengClient object
        '''
        self.clnt = clnt
        self.log = clnt.log
        self.timeout = timeout
        self.version = None
        self.session = clnt.session

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.session)

    def get_response_data(self, resp):
        if isinstance(resp, dict):
            return resp
        try:
            clean_resp = resp.decode('utf-8')
            json_resp = json.loads(clean_resp)
            if json_resp.get('data') is not None:
                return json_resp.get('data')
            else:
                return json_resp
        except Exception as e:
            self.clnt.log.warning('error parsing response data: ',str(e))
            return resp

    @staticmethod
    def slugify(string):
        return string.lower().replace(' ', '_')

    def response_data(self, resp):
        if isinstance(resp, dict):
            return resp
        try:
            clean_resp = resp.decode('utf-8')
            json_resp = json.loads(clean_resp)
            return json_resp
        except Exception as e:
            self.clnt.log.warning('error parsing response data')
            return resp

    def get_handle_response(self, url):
        r = self.clnt.get(url)
        return self.get_response_data(r)

    def post_handle_response(self, url, data=None):
        r = self.clnt.post(url, data=data)
        return self.response_data(r)

    def del_handle_response(self, url):
        r = self.clnt.delete(url)
        return self.response_data(r)

    def put_handle_response(self, url, data=None):
        r = self.clnt.put(url, data=data)
        return self.response_data(r)

    def get_status(self):
        '''Get server status'''
        return self.get_handle_response('/status')

    def list_node_templates(self):
        '''List details for each node template'''
        return self.get_handle_response('/list/templates/')

    def node_template_detail(self, node_type):
        ''' List details for single node template
            All available images for the selected template will be included in the output
        '''
        data = self.get_handle_response(f'/list/templates/{node_type}')
        if data:
            return data.get("options")
        return

    def list_users(self):
        '''get list of users'''
        return self.get_handle_response('/users/')

    def list_user_roles(self):
        '''list user roles'''
        return self.get_handle_response('/list/roles')

    def get_user(self, username):
        '''get user details'''
        user = None
        if username:
            try:
                user = self.get_handle_response(f"/users/{username}")
            except Exception as e:
                if 'User not found' in str(e):
                    user = None
                else:
                    raise(e)
        return user

    def get_user_auth(self, username):
        endpoint = '/auth'
        pass

    def add_user(self, username='', password='', role='user', name='', email='', expiration='-1', **kwargs):
        '''Add new user

           Parameters:
            email(str): the email address of the user;
            expiration(str): date until the user is valid (UNIX timestamp) or -1 if never expires;
            name(str): a description for the user, usually salutation;
            password (string): the user password used to login;
            role(string): choices are ['user', 'admin']
            username (str): a unique alphanumeric string used to login;

           Returns:
            Dictionary with user data
        '''
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
                return self.post_handle_response('/users', data=data)
            else:
                raise EvengApiError('User already exists')
        return

    def edit_user(self, username, data=None):
        '''
           Parameters:
            email(str): the email address of the user;
            expiration(str): date until the user is valid (UNIX timestamp) or -1 if never expires;
            name(str): a description for the user, usually salutation;
            password (string): the user password used to login;
            role(string): choices are ['user', 'admin']
        '''
        url = self.clnt.url_prefix + f"/users/{username}"
        r = None

        existing = self.get_user(username)

        updated_user = {}
        if existing and data:
            updated_user = copy.deepcopy(current_user)
            updated_user.update(data)
            r = self.clnt.put(url, headers=self.clnt.headers, data=json.dumps(updated_user))
        return self.get_response_data(r)

    def delete_user(self, username):
        '''Delete EVE-NG user'''
        existing = self.get_user(username)
        if existing:
            return self.del_handle_response(f'/users/{username}')
        else:
            raise EvengApiError('User does not exists')

    def list_networks(self):
        '''List network types'''
        return self.get_handle_response('/list/networks')

    def list_folders(self):
        '''List folders for user
        '''
        return self.get_handle_response(f"/folders/")

    def add_folder(self, name):
        '''Add a new folder for user account
        '''
        slug = self.slugify(name)
        data = {"path": f"/{slug}", "name": slug}
        return self.post_handle_response("/folders", data=json.dumps(data))

    def move_folder(self, old_path, new_path):
        ''' Move/rename an existent folder
        '''
        data = {'path': new_path}
        endpoint = f"/folders/{old_path}"
        return self.put_handle_response(endpoint, data=json.dumps(data))

    def delete_folder(self, path):
        '''Delete an existing folder
        '''
        return self.del_handle_response(f"/folders/{path}")

    @staticmethod
    def normalize_path(path):
        path = path.lstrip("/")
        dir_, file_ = os.path.split(path)
        q_plus = quote_plus(dir_)
        normpath = "/".join((q_plus, file_))
        return normpath

    def get_lab(self, path):
        '''get details for a single lab

           example response:
            {
                 "code": 200,
                 "data": {
                     "author": "User1 Lastname",
                     "body": "",
                     "description": "A new test lab.",
                     "filename": "Lab 1.unl",
                     "id": "d34628dd-cc1d-4e52-8f91-4a0673985d87",
                     "name": "Lab 1",
                     "version": "1"
                 },
                 "message": "Lab has been loaded (60020).",
                 "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        if not normpath.endswith(".unl"):
            normpath = normpath + ".unl"
        url = "/labs/" + normpath
        print(url)
        return self.get_handle_response(url)

    def list_lab_networks(self, path):
        ''' Get one or all networks configured in a lab
            {
                "code": 200,
                "data": {
                    "1": {
                        "id": 1,
                        "left": 409,
                        "name": "Net OVS",
                        "top": 345,
                        "type": "ovs"
                    },
                    "2": {
                        "id": 2,
                        "left": 583,
                        "name": "Net2",
                        "top": 261,
                        "type": "bridge"
                    },
                    "3": {
                        "id": 3,
                        "left": 256,
                        "name": "Net3",
                        "top": 276,
                        "type": "bridge"
                    }
                },
                "message": "Successfully listed networks (60004).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + "/networks"
        return self.get_handle_response(url)

    def get_lab_network(self, path, net_id):
        '''retrieve details for a single network in a lab
            sample output:
                {
                    "code": 200,
                    "data": {
                        "left": 409,
                        "name": "Net OVS",
                        "top": 345,
                        "type": "ovs"
                    },
                    "message": "Successfully listed network (60005).",
                    "status": "success"
                }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/networks/{net_id}"
        return self.get_handle_response(url)

    def get_lab_network_by_name(self, path, name):
        networks  = self.list_lab_networks(path)
        if networks:
            try:
                found = next(v for k,v in networks.items() if v['name'] == name)
                return found
            except StopIteration:
                return None
        return

    def list_lab_links(self, path):
        '''Get all remote endpoint for both ethernet and serial interfaces
            {
                "code": 200,
                "data": {
                    "ethernet": {
                        "1": "Net OVS",
                        "2": "Net2",
                        "3": "Net3",
                        "4": "Net4",
                        "5": "Net5"
                    },
                    "serial": {
                        "3": {
                            "1": "R3 s1/0",
                            "17": "R3 s1/1",
                            "33": "R3 s1/2",
                            "49": "R3 s1/3"
                        },
                        "4": {
                            "1": "R4 s1/0",
                            "17": "R4 s1/1",
                            "33": "R4 s1/2",
                            "49": "R4 s1/3"
                        }
                    }
                },
                "message": "Fetced all lab networks and serial endpoints (60024).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/links"
        return self.get_handle_response(url)

    def list_lab_nodes(self, path):
        '''List all nodes in the lab
        {
            "code": 200,
            "data": {
                "1": {
                    "console": "telnet",
                    "cpu": 1,
                    "delay": 0,
                    "ethernet": 4,
                    "icon": "Router.png",
                    "id": 1,
                    "image": "vios-adventerprisek9-m-15.4-1.3.0.181",
                    "left": 358,
                    "name": "R1",
                    "ram": 512,
                    "status": 0,
                    "template": "vios",
                    "top": 330,
                    "type": "qemu",
                    "url": "telnet://127.0.0.1:32769",
                    "uuid": "ab60e9de-2599-4b67-919a-b769fb6e270d"
                },
                "2": {
                    "console": "telnet",
                    "cpu": 1,
                    "delay": 0,
                    "ethernet": 4,
                    "icon": "Router.png",
                    "id": 2,
                    "image": "vios-adventerprisek9-m-15.4-1.3.0.181",
                    "left": 501,
                    "name": "R2",
                    "ram": 512,
                    "status": 0,
                    "template": "vios",
                    "top": 330,
                    "type": "qemu",
                    "url": "telnet://127.0.0.1:32770",
                    "uuid": "206323a6-000b-40bc-a765-9c7e7e5751ee"
                }
            },
            "message": "Successfully listed nodes (60026).",
            "status": "success"
        }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes"
        return self.get_handle_response(url)

    def get_lab_node(self, path, node_id):
        '''retrieve single node from lab

          sample output:
            {
                "code": 200,
                "data": {
                    "config": "Unconfigured",
                    "console": "telnet",
                    "cpu": 1,
                    "delay": 0,
                    "ethernet": 4,
                    "icon": "Router.png",
                    "image": "vios-adventerprisek9-m-15.4-1.3.0.181",
                    "left": 358,
                    "name": "R1",
                    "ram": 512,
                    "status": 0,
                    "template": "vios",
                    "top": 330,
                    "type": "qemu",
                    "url": "telnet://127.0.0.1:32769",
                    "uuid": "ab60e9de-2599-4b67-919a-b769fb6e270d"
                },
                "message": "Successfully listed node (60025).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}"
        return self.get_handle_response(url)

    def get_lab_node_by_name(self, path, name):
        nodes  = self.list_lab_nodes(path)
        if nodes:
            try:
                found = next(v for k,v in nodes.items()
                               if v['name'] == name)
                return found
            except StopIteration:
                return None
        return

    @staticmethod
    def find_node_interface(name, intf_list):
        interfaces = list(intf_list)
        try:
            found = next( (idx, i) for idx, i in enumerate(interfaces) if i['name'] == name)
            return found
        except StopIteration:
            return None

    def connect_node(self, lab, src="", src_intf="", dst="", dst_intf="", dst_type="network", media_type=""):
        r = None
        dest_types = ["network", "node"]
        if dst_type not in dest_types:
            raise ValueError("destination type not in allowed types: {dest_types}")

        print(f"connecting {src} to {dst}")
        if dst_type == "network":
            r = self.connect_node_to_cloud(lab, src, src_intf, dst, media_type=media_type)
        else:
            r= self.connect_node_to_node(lab, src, src_intf, dst, dst_intf, media_type=media_type)
        return r

    def connect_p2p_interface(self, lab, node_id, interface, net_id):
        ''' Connect node interface to a network
        '''
        normpath = self.normalize_path(lab)
        url = "/labs/" + normpath + f"/nodes/{node_id}/interfaces"

        intf_id = interface[0]
        data = {intf_id: str(net_id)}

        # connect interfaces
        r1 = self.put_handle_response(url, data=json.dumps(data))

        # set visibility for bridge to "0" to hide bridge
        r2 = self.edit_lab_network(lab, net_id, data={"visibility": "0"})

        return r1

    def connect_node_to_cloud(self, lab, node_name, node_intf, net_name, media_type="ethernet"):
        node = self.get_lab_node_by_name(lab, node_name)
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
        src_node = self.get_lab_node_by_name(lab, src_node_name)
        dst_node = self.get_lab_node_by_name(lab, dst_node_name)

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
        ''' Start one or all nodes configured in a lab

            sample output:
                {
                    "code": 400,
                    "message": "Failed to start node (12).",
                    "status": "fail"
                }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/start"
        return self.get_handle_response(url)

    def stop_all_nodes(self, path):
        ''' Stop one or all nodes configured in a lab

          sample output:
            {
                "code": 200,
                "message": "Nodes stopped (80050).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/stop"
        return self.get_handle_response(url)

    def start_node(self, path, node_id):
        ''' start single node in a lab
        {
            "code": 200,
            "message": "Node started (80049).",
            "status": "success"
        }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}/start"
        return self.get_handle_response(url)

    def stop_node(self, path, node_id):
        '''Stop single node in a lab

          sample output:
            {
                "code": 200,
                "message": "Node stopped (80051).",
                "status": "success"
            }

        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}/stop"
        return self.get_handle_response(url)

    def wipe_all_nodes(self, path):
        '''
        Wipe one or all nodes configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

           sample output:
            {
                "code": 200,
                "message": "Nodes cleared (80052).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/wipe"
        return self.get_handle_response(url)

    def wipe_node(self, path, node_id):
        '''
        Wipe single node configured in a lab. Wiping deletes
        all user config, included startup-config, VLANs, and so on. The
        next start will rebuild node from selected image.

        sample output:

            {
                "code": 200,
                "message": "Node cleared (80053).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}/wipe"
        return self.get_handle_response(url)

    def export_all_nodes(self, path):
        '''
        Export one or all nodes configured in a lab. Exporting means saving
        the startup-config into the lab file.

        sample output:
            {
                "code": 200,
                "message": "Nodes exported (80057).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/export"
        return self.get_handle_response(url)

    def export_node(self, path, node_id):
        '''
        Export node configuration. Exporting means saving the startup-config
        into the lab file.

        sample output:
            {
                "code": 200,
                "message": "Node exported (80058).",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}/export"
        return self.get_handle_response(url)

    def get_node_interfaces(self, path, node_id):
        '''
        Get configured interfaces from a node.

        sample output:
            {
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
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes/{node_id}/interfaces"
        return self.get_handle_response(url)

    def get_lab_topology(self, path):
        '''
        Get the lab topology

        sample output:
            {
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
                    },
                    {
                        "destination": "node1",
                        "destination_label": "Gi0/1",
                        "destination_type": "node",
                        "source": "node3",
                        "source_label": "e0/1",
                        "source_type": "node",
                        "type": "ethernet"
                    }
                ],
                "message": "Topology loaded",
                "status": "success"
            }
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/topology"
        return self.get_handle_response(url)

    def get_lab_pictures(self, path):
        '''
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
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/pictures"
        return self.get_handle_response(url)

    def get_lab_picture_details(self, path, picture_id):
        '''
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
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/pictures/{picture_id}"
        return self.get_handle_response(url)

    def get_lab_picture_data():
        # curl -s -c /tmp/cookie -b /tmp/cookie -X GET -H 'Content-type: application/json'
        # http://127.0.0.1/api/labs/User1/Lab%201.unl/pictures/1/data/32/32

        # The resized picture is generated with original aspect-ratio using given values as maximum witdh/lenght.
        pass

    def create_lab(self, username, path="/", name="", version="1", description="", body="", **kwargs):
        ''' Create a new lab

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
        '''
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
        ''' Edit an existing lab. The request can set only one single
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
        '''
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
        ''' Delete an existent lab

            sample output:
                {
                    "code": 200,
                    "message": "Lab has been deleted (60022).",
                    "status": "success"
                }
        '''
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
        '''Edit lab network
        data = {
            "left": kwargs.get("left") or left,
            "name": kwargs.get("name") or name,
            "top": kwargs.get("top") or top,
            "type": kwargs.get("type") or network_type,
            "visibility": kwargs.get("visibility") or visibility
        }
        '''
        normpath = self.normalize_path(path)
        url = '/labs/' + normpath + f'/networks/{net_id}'
        return self.put_handle_response(url, data=json.dumps(data))


    def add_lab_network(self, path, network_type="", visibility="0", name="", left="", top="", **kwargs):
        '''Add a new network to a lab
        {
            "code": 201,
            "message": "Network has been added to the lab (60006).",
            "status": "success"
        }
        Parameters:
            left: mergin from left, in percentage (i.e. 35%), default is a
                  random value between 30% and 70%;
            name: network name (i.e. Core Network), default is
                  NetX (X = network_id)
            top:  margin from top, in percentage (i.e. 25%), default is a
                  random value between 30% and 70%;
            type (mandatory): see “List network types”
        '''
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

    def add_lab_node(self, path, delay=0, name="", node_type="", template="",
                     top="", left="", console="telnet", config="Unconfigured",
                     image="", **kwargs):
        ''' Add a new node to a lab
        sample output:
            {
                "code": 201,
                "message": "Lab has been saved (60023).",
                "status": "success"
            }
        # Parameters:

        # config: can be Unconfigured or Saved, default is Unconfigured;
        # delay: seconds to wait before starting the node, default is 0;
        # icon: icon (located under /opt/unetlab/html/images/icons/) used to display the node, default is Router.png;
        # image: image used to start the node, default is latest included in “List node templates”;
        # left: mergin from left, in percentage (i.e. 35%), default is a random value between 30% and 70%;
        # name: node name (i.e. “Core1”), default is NodeX (X = node_id);
        # ram: MB of RAM configured for the node, default is 1024;
        # template (mandatory): see “List node templates”;
        # top: margin from top, in percentage (i.e. 25%), default is a random value between 30% and 70%;
        # type (mandatory): can be iol, dynamips or qemu.
        # Parameters for IOL nodes:

        # ethernet: number of ethernet porgroups (each portgroup configures four interfaces), default is 2;
        # nvram: size of NVRAM in KB, default is 1024;
        # serial: number of serial porgroups (each portgroup configures four interfaces), default is 2.

        # Parameters for Dynamips nodes:
        # idlepc: value used for Dynamips optimization (i.e. 0x80369ac4), default is 0x0 (no optimization);
        # nvram: size of NVRAM in KB, default is 1024;
        # slot[0-9]+: the module configured in a specific slot (i.e. slot1=NM-1FE-TX).

        # Parameters for QEMU nodes:
        # console: can be telnet or vnc, default is telnet;
        # cpu: number of configured CPU, default is 1;
        # ethernet: number of ethernet interfaces, default is 4;
        # uuid: UUID configured, default is a random UUID (i.e. 641a4800-1b19-427c-ae87-4a8ee90b7790).
        '''
        normpath = self.normalize_path(path)
        url = "/labs/" + normpath + f"/nodes"

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
        return self.post_handle_response(url, data=json.dumps(data))