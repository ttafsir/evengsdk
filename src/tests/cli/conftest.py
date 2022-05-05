import os

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="module")
def setup_cli_lab(cli_lab, authenticated_client):
    """Create and teardown lab"""
    yield authenticated_client.api.create_lab(**cli_lab)
    authenticated_client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    authenticated_client.api.delete_lab(cli_lab["path"] + cli_lab["name"])


@pytest.fixture(scope="module")
def test_lab(cli_lab, authenticated_client):
    """Create and teardown lab"""
    yield authenticated_client.api.create_lab(**cli_lab)
    authenticated_client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    authenticated_client.api.delete_lab(cli_lab["path"] + cli_lab["name"])
