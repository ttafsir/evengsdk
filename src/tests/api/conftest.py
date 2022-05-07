import pytest


@pytest.fixture(scope="module")
def setup_lab(lab, authenticated_client):
    """Cerate lab and return lab object."""
    yield authenticated_client.api.create_lab(**lab)
    authenticated_client.api.delete_lab(lab["path"] + lab["name"])


@pytest.fixture()
def test_network(authenticated_client, lab_path, test_network_data):
    """set up and teardown a test network"""
    resp = authenticated_client.api.add_lab_network(
        lab_path, **test_network_data, visibility="1"
    )
    net_id = resp.get("data", {}).get("id")
    yield net_id
    authenticated_client.api.delete_lab_network(lab_path, net_id)
