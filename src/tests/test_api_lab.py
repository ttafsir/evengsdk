import json
import os
import pytest
import sys

print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))

from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengLoginError, EvengApiError
from requests.exceptions import HTTPError


LAB_PATH = '/datacenter/'
LAB_NAME = 'leaf_spine_lab'
EXT = '.unl'

DEVICE_UNDER_TEST = {
    'host': '10.246.48.76',
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


class TestEvengApiLab:
    ''' Test cases '''

    def test_api_get_lab_wo_extension(self, client):
        """
        Retrieve Lab details without file extension
        """
        fullpath = LAB_PATH + LAB_NAME
        lab = client.api.get_lab(fullpath)
        assert lab.get('name') == LAB_NAME

    def test_api_get_lab_w_extension(self, client):
        """
        Retrieve Lab details with file extension
        """
        fullpath = LAB_PATH + LAB_NAME + EXT
        lab = client.api.get_lab(fullpath)
        assert lab.get('name') == LAB_NAME

    def test_get_non_existing_lab(self, client):
        """
        Verify that retrieving a non existing lab
        raises an error.
        """
        fullpath = LAB_PATH + LAB_NAME
        with pytest.raises(HTTPError):
            lab = client.api.get_lab('FAKE_LAB_PATH')