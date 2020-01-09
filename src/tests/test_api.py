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

    def test_api_get_status(self, client):
        """
        Verify server status using the API
        """
        r = client.api.get_status()
        assert r.get('data') is not None
