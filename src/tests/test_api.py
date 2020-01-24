import logging
import json
import os
import pytest
import sys

print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))

from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengLoginError, EvengApiError


LAB_PATH = '/enablement labs/a_leaf_spine.unl'
DEVICE_UNDER_TEST = {
    'host': '10.246.49.23',
    'username': 'admin',
    'password': 'eve'
}
USERS = {
    'to_create': [('tester1', 'test1_pass'), ('tester2', 'test2_pass')],
    'non_existing': 'fake_user99'
}
TEST_NETWORK = 'ATC-vCloud'

@pytest.fixture()
def client():
    client = EvengClient(DEVICE_UNDER_TEST['host'], log_level='DEBUG', log_file='api.log')
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
        user_details = client.api.get_user(user)
        assert user_details == {}

    def test_add_user(self, client):
        """
        Verify that we can created a user with just
        the username and password
        """
        for username, password in (user for user in USERS['to_create']):
            result = client.api.add_user(username, password)
            assert result['status'] == "success"

    def test_add_existing_user(self, client):
        """
        Verify that adding an existing user raises
        an exception
        """
        for username, password in (user for user in USERS['to_create']):
            with pytest.raises(EvengApiError):
                result = client.api.add_user(username, password)

    def test_edit_existing_user(self, client):
        """
        Verify that we can edit existing user
        """
        new_data = {
            'email': 'test1@testing.com',
            'name': 'John Doe'
        }
        user = USERS['to_create'][0]
        # edit user
        client.api.edit_user(user[0], data=new_data)

        # retrieve updates
        updated_user = client.api.get_user(user[0])

        # ensure new data was PUT successfully
        assert updated_user['email'] == new_data['email']

    def test_edit_non_existing_user(self, client):
        """
        Verify that we can edit existing user
        """
        new_data = {
            'email': 'test@testing.com',
            'name': 'John Doe'
        }
        username = USERS['non_existing']
        with pytest.raises(EvengApiError):
            result = client.api.edit_user(username, data=new_data)


    def test_delete_user(self, client):
        """
        Verify that we can delete users
        """
        for username, _ in (user for user in USERS['to_create']):
            client.api.delete_user(username)
            user = client.api.get_user(username)
            assert user == {}

    def test_delete_non_existing_user(self, client):
        """
        Verify that deleting non_existing users
        raises an exception.
        """
        with pytest.raises(EvengApiError):
            client.api.delete_user(USERS['non_existing'])

    def test_list_networks(self, client):
        """
        Verify that we can retrieve EVE-NG networks. The
        data returned is a dictionary that includes
        network types and instances.
        """
        networks = client.api.list_networks()
        assert networks['bridge'] is not None

    def test_get_existing_lab(self, client):
        """
        Verify that we can get details for an existing lab.
        The 'id' key in the return value should not be None.
        """
        lab_details = client.api.get_lab(LAB_PATH)
        assert lab_details['id'] is not None

    def test_get_non_existing_lab(self, client):
        """
        Verify that retrieving a non existing lab
        returns and empty dict.
        """
        lab_details = client.api.get_lab('FAKE_LAB_PATH')
        assert lab_details  == {}

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
        network_details = client.api.get_lab_network_by_name(LAB_PATH, TEST_NETWORK)
        assert network_details['type'] is not None

    def test_list_lab_links(self, client):
        pass

    def test_list_lab_nodes(self, client):
        pass

    def test_get_lab_node(self, client):
        pass

    def test_get_lab_node_by_name(self, client):
        pass
