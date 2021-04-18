import pytest

from evengsdk.client import EvengClient
from requests.exceptions import HTTPError


LAB_PATH = '/datacenter/'
LAB_NAME = 'leaf_spine_lab'
EXT = '.unl'

DEVICE_UNDER_TEST = {
    'host': '10.246.32.35',
    'username': 'admin',
    'password': 'eve'
}
TESTLAB = {
  'name': 'TestLab',
  'path': '/',
  'description': 'short description',
  'version': '1',
  'body': 'longer description'
}

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
        with pytest.raises(HTTPError):
            client.api.get_lab('FAKE_LAB_PATH')

    def test_create_lab(self, client):
        resp = client.api.create_lab(**TESTLAB)
        assert resp['status'] == 'success'

    def test_get_lab_topology(self, client):
        lab_path = TESTLAB['path'] + TESTLAB['name']
        resp = client.api.get_lab(lab_path)
        assert resp['status'] == 'success'