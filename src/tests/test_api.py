import pytest

from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengHTTPError


LAB_PATH = '/datacenter/leaf_spine_lab.unl'
DEVICE_UNDER_TEST = {
    'host': '10.246.32.119',
    'username': 'admin',
    'password': 'eve'
}
USERS = {
    'to_create': [('tester1', 'test1_pass'), ('tester2', 'test2_pass')],
    'non_existing': 'fake_user99'
}
TEST_NETWORK = 'ATC-vCloud'
TEST_NODE = 'leaf04'
TEST_CONFIG = """
!
hostname vEOS4
!
"""


@pytest.fixture()
def client():
    client = EvengClient(
        DEVICE_UNDER_TEST['host'],
        log_level='DEBUG',
        log_file='api.log'
    )
    username = DEVICE_UNDER_TEST['username']
    passwd = DEVICE_UNDER_TEST['password']
    client.login(username=username, password=passwd)
    yield client
    client.logout()


class TestEvengApi:
    ''' Test cases '''

    def test_api_get_get_server_status(self, client):
        """
        Verify server status using the API
        """
        status = client.api.get_server_status()
        assert status.get('cpu') is not None

    def test_list_node_templates(self, client):
        """
        Verify we can list node templates from API
        """
        templates = client.api.list_node_templates()
        assert isinstance(templates, dict)

    def test_node_template_detail(self, client):
        """
        Verify that we get retrieve the details of a node template
        """
        node_types = ['a10']
        for n_type in node_types:
            detail = client.api.node_template_detail(n_type)
            assert isinstance(detail, dict)

    def test_list_users(self, client):
        """
        Verify that we can retrieve list of users and that
        the default 'admin' user  exists.
        """
        users = client.api.list_users()
        assert 'admin' in users

    def test_list_user_roles(self, client):
        """
        Verify that we can retrieve list of user roles
        """
        roles = client.api.list_user_roles()
        assert 'admin' in roles

    def test_get_user(self, client):
        """
        Verify that we can retrieve a single user detail
        """
        user_details = client.api.get_user('admin')
        assert 'email' in user_details

    def test_get_non_existing_user(self, client):
        """
        Verify that the api returns an empty dictionary
        if the user does not exist
        """
        user = USERS['non_existing']
        with pytest.raises(EvengHTTPError):
            client.api.get_user(user)

    def test_add_user(self, client):
        """
        Verify that we can created a user with just
        the username and password
        """
        for username, password in (user for user in USERS['to_create']):
            try:
                r = client.api.add_user(username, password)
                assert r.get('status') == 'success'
            except EvengHTTPError as e:
                assert 'check if already exists' in str(e)

    def test_add_existing_user(self, client):
        """
        Verify that adding an existing user raises
        an exception
        """
        for username, password in (user for user in USERS['to_create']):
            with pytest.raises(EvengHTTPError):
                client.api.add_user(username, password)

    def test_edit_existing_user(self, client):
        """
        Verify that we can edit existing user
        """
        new_data = {'email': 'test1@testing.com', 'name': 'John Doe'}
        user = USERS['to_create'][0]
        # edit user
        client.api.edit_user(user[0], data=new_data)

        # retrieve updates
        updated_user = client.api.get_user(user[0])

        # ensure new data was PUT successfully
        assert updated_user['email'] == new_data['email']

    def test_edit_non_existing_user(self, client):
        """
        Verify that editing non existing users raises
        an exception.
        """
        new_data = {
            'email': 'test@testing.com',
            'name': 'John Doe'
        }
        username = USERS['non_existing']
        with pytest.raises(EvengHTTPError):
            client.api.edit_user(username, data=new_data)

    def test_delete_user(self, client):
        """
        Verify that we can delete users
        """
        for username, _ in (user for user in USERS['to_create']):
            resp = client.api.delete_user(username)
            assert resp.get('status') == 'success'

            # make sure it was deleted
            with pytest.raises(EvengHTTPError):
                client.api.get_user(username)

    def test_delete_non_existing_user(self, client):
        """
        Verify that deleting non_existing users
        raises an exception.
        """
        with pytest.raises(EvengHTTPError):
            client.api.delete_user(USERS['non_existing'])

    def test_list_networks(self, client):
        """
        Verify that we can retrieve EVE-NG networks. The
        data returned is a dictionary that includes
        network types and instances.
        """
        networks = client.api.list_networks()
        assert networks['bridge'] is not None

    def test_list_lab_networks(self, client):
        """
        Verify that we can list lab networks.
        """
        networks = client.api.list_lab_networks(LAB_PATH)
        assert isinstance(networks, dict)

    def test_get_lab_network(self, client):
        """
        Verify that we can retrieve a specific lab by id
        """
        network_details = client.api.get_lab_network(LAB_PATH, '1')
        assert network_details['type'] is not None

    def test_get_lab_network_by_name(self, client):
        """
        Verify that we can retrieve a specific lab by name
        """
        network_details = client.api.get_lab_network_by_name(
            LAB_PATH,
            TEST_NETWORK
        )
        assert network_details is not None

    def test_list_lab_links(self, client):
        """
        Get all remote endpoints for both ethernet
        and serial interfaces. Returns dictionary
        of existing links or empty dictionary.
        """
        links = client.api.list_lab_links(LAB_PATH)
        assert links is not None

    def test_list_nodes(self, client):
        """
        Verify that we can retrieve all node details
        """
        nodes = client.api.list_nodes(LAB_PATH)
        assert nodes is not None and nodes

    def test_get_node(self, client):
        """
        Verify that we can details for a single node by ID
        """
        # get with node with ID == 1
        node = client.api.get_node(LAB_PATH, '1')
        assert node['type'] is not None

    def test_add_node(self, client):
        """
        Verify that we can details for a single node by ID
        """
        node = {
            'node_type': 'qemu',
            'template': 'csr1000v',
            'image': 'csr1000v-universalk9-16.06.06',
            'name': "CSR1",
            'ethernet': 4,
            'cpu': 2,
            'serial': 2,
            'delay': 0
        }
        resp = client.api.add_node(LAB_PATH, **node)
        assert resp

    def test_get_node_by_name(self, client):
        """
        Verify that we can details for a single node by node name
        """
        # get with node with name == TEST_NODE
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        assert node['name'] == TEST_NODE

    def test_get_node_configs(self, client):
        """
        Verify that we can retrieve information about the
        node configs
        """
        config_info = client.api.get_node_configs(LAB_PATH)
        assert config_info

    def test_get_node_config_by_id(self, client):
        """
        Verify that we can retrieve configuration data
        using a specific config ID
        """
        config = client.api.get_node_config_by_id(LAB_PATH, '1')
        assert config['data'] is not None

    def test_get_node_config_by_name(self, client):
        """
        Verify that we can retrieve configuration data
        using a node name
        """
        config = client.api.get_node_config_by_name(LAB_PATH, TEST_NODE)
        assert config['name'] == TEST_NODE

    def test_upload_node_config(self, client):
        """
        Upload node's config to set startup config
        """
        config = client.api.get_node_config_by_name(LAB_PATH, TEST_NODE)
        node_id = config.get('id')
        resp = client.api.upload_node_config(
            LAB_PATH,
            node_id,
            config=TEST_CONFIG
        )
        assert resp['status'] == 'success'

    def test_stop_all_nodes(self, client):
        """
        Stop all nodes in the lab
        """
        result = client.api.stop_all_nodes(LAB_PATH)
        assert result['status'] == 'success'

    def test_start_all_nodes(self, client):
        """
        Start all nodes in the lab
        """
        result = client.api.start_all_nodes(LAB_PATH)
        assert result['status'] == 'success'

    def test_stop_node(self, client):
        """
        Stop a single node in the lab
        """
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = client.api.stop_node(LAB_PATH, node['id'])
        assert result['status'] == 'success'

    def test_start_node(self, client):
        """
        Start a single node in the lab
        """
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = client.api.start_node(LAB_PATH, node['id'])
        assert result['status'] == 'success'

    def test_wipe_all_nodes(self, client):
        """
        Wipe all node startup configs and VLAN db
        """
        result = client.api.wipe_all_nodes(LAB_PATH)
        assert result['status'] == 'success'

    def test_wipe_node(self, client):
        """
        Wipe node startup configs and VLAN db
        """
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = client.api.wipe_node(LAB_PATH, node['id'])
        assert result['status'] == 'success'

    @pytest.mark.xfail
    def test_export_all_nodes(self, client):
        """
        Save all startup configs to lab
        """
        result = client.api.export_all_nodes(LAB_PATH)
        assert result['status'] == 'success'

    @pytest.mark.xfail
    def test_export_node(self, client):
        """
        Save node startup-config to lab
        """
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = client.api.export_node(LAB_PATH, node['id'])
        assert result['status'] == 'success'

    def test_get_node_interfaces(self, client):
        """
        Get configured interfaces from a node
        """
        node = client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = client.api.get_node_interfaces(LAB_PATH, node['id'])
        assert result is not None
        assert isinstance(result, dict)
