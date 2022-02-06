import os

import pytest
from dotenv import load_dotenv
from evengsdk.client import EvengClient


load_dotenv()


@pytest.fixture(scope="session")
def client():
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
    username = os.environ["EVE_NG_USERNAME"]
    passwd = os.environ["EVE_NG_PASSWORD"]
    client.login(username=username, password=passwd)
    yield client
    client.logout()
