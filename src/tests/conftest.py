import os
from datetime import datetime

import pytest
from dotenv import load_dotenv

from evengsdk.client import EvengClient

load_dotenv()


@pytest.fixture(scope="session")
def client():
    """Create and teardown client"""
    client = EvengClient(
        os.environ["EVE_NG_HOST"], log_file="test.log", log_level="DEBUG"
    )
    if os.environ["EVE_NG_PROTOCOL"] == "https":
        client.protocol = "https"
        client.ssl_verify = False
        client.disable_insecure_warnings = True
    return client


@pytest.fixture(scope="module")
def authenticated_client(client):
    """Authenticate client and return client object."""
    username = os.environ["EVE_NG_USERNAME"]
    passwd = os.environ["EVE_NG_PASSWORD"]
    client.login(username=username, password=passwd)
    yield client
    client.logout()


@pytest.fixture(scope="session")
def lab():
    """Create lab fixture."""
    now = datetime.now()
    ts = str(datetime.timestamp(now)).split(".", maxsplit=1)[0]
    return {"name": f"test-lab-{ts}", "description": "Test Lab", "path": "/"}


@pytest.fixture(scope="module")
def cli_lab():
    """Create lab fixture."""
    now = datetime.now()
    ts = str(datetime.timestamp(now)).split(".", maxsplit=1)[0]
    return {"name": f"test-cli-lab-{ts}", "description": "Test Lab", "path": "/"}


@pytest.fixture()
def lab_path(lab):
    """Return lab path for API tests"""
    return lab["path"] + lab["name"]


@pytest.fixture(scope="module")
def cli_lab_path(cli_lab):
    """Return lab path for CLI tests"""
    return cli_lab["path"] + cli_lab["name"]


@pytest.fixture()
def network_name():
    return "vCloud"


@pytest.fixture()
def test_network_data():
    """returns a dict with test data for a network"""
    return dict(name="test_network", network_type="bridge")


@pytest.fixture(scope="session")
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser99",
        "password": "password1",
        "expiration": "-1",
        "role": "admin",
        "name": "John Doe",
        "email": "john.doe@acme.com",
    }


@pytest.fixture(scope="session")
def test_node_data():
    """returns a dict with test data for a node"""
    return {
        "node_type": "qemu",
        "template": "veos",
        "image": "veos-4.21.1.1F",
        "name": "leaf01",
        "ethernet": 4,
        "cpu": 2,
        "serial": 2,
        "delay": 0,
    }


@pytest.fixture(scope="session")
def test_node_config():
    """Test config data for a node."""
    return """
!
hostname vEOS4
!
"""
