import pytest


@pytest.fixture()
def lab():
    return {
        "name": "TestLab",
        "path": "/",
        "description": "short description",
        "version": "1",
        "body": "longer description",
    }


@pytest.fixture()
def lab_path(lab):
    return lab["path"] + lab["name"]


@pytest.fixture()
def setup_lab(lab, authenticated_client):
    yield authenticated_client.api.create_lab(**lab)
    authenticated_client.api.delete_lab(lab["path"] + lab["name"])


class TestEvengApiNetwork:
    """Test cases for Network endpoints"""

    @pytest.mark.parametrize(
        "name, network_type, visibility",
        [("bridge_network", "bridge", "1"), ("cloud0", "pnet0", "1")],
    )
    def test_add_network(
        self, authenticated_client, setup_lab, lab, name, network_type, visibility
    ):
        lab_path = lab["path"] + lab["name"]
        resp = authenticated_client.api.add_lab_network(
            lab_path, network_type=network_type, name=name, visibility=visibility
        )
        # ID is returned after creation
        network_id = resp.get("data", {}).get("id")
        assert int(network_id)

        # network name exists in lab networks
        lab_networks = authenticated_client.api.list_lab_networks(lab_path)

        assert lab_networks["data"][f"{network_id}"]["name"] == name

    @pytest.mark.parametrize(
        "network_type, visibility",
        [("point-to-point", "1"), ("pnet10", "1")],
    )
    def test_add_invalid_network_raises(
        self, authenticated_client, setup_lab, lab, network_type, visibility
    ):
        # validate invalid network type raises
        # validate pnet not in (pnet0 - pnet9) range is invalid
        with pytest.raises(ValueError):
            lab_path = lab["path"] + lab["name"]
            authenticated_client.api.add_lab_network(
                lab_path, network_type, visibility=visibility
            )

    def test_edit_network(self, authenticated_client, setup_lab, lab, lab_path):
        net = dict(name="bridge_network", network_type="bridge", visibility="1")
        add_resp = authenticated_client.api.add_lab_network(lab_path, **net)
        net_id = add_resp.get("data", {}).get("id")

        edited = lab.copy()
        edited.update({"name": "edited"})

        # edit operation is successful
        edit_resp = authenticated_client.api.edit_lab_network(
            lab_path, net_id, data=edited
        )
        assert edit_resp["code"] == 201

        # network updated
        lab_networks = authenticated_client.api.list_lab_networks(lab_path)
        assert lab_networks["data"][f"{net_id}"]["name"] == "edited"

        # edit operation without data should raise
        with pytest.raises(ValueError):
            edit_resp = authenticated_client.api.edit_lab_network(lab_path, net_id)

    @pytest.mark.xfail(reason="TODO: fix this test")
    def test_delete_network(self, authenticated_client, setup_lab, lab_path):
        net = dict(name="bridge_network", network_type="bridge")
        add_resp = authenticated_client.api.add_lab_network(lab_path, **net)
        net_id = add_resp.get("data", {}).get("id")

        print(f"deleting net_id: {net_id}")
        del_resp = authenticated_client.api.delete_lab_network(lab_path, net_id)
        assert del_resp["status"] == "success"
