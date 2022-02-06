import pytest

from evengsdk.exceptions import EvengHTTPError


@pytest.fixture()
def network_name():
    return "vCloud"


@pytest.mark.usefixtures("setup_lab")
class TestEvengApiNetwork:
    """Test cases for Network endpoints"""

    def test_list_lab_networks(self, authenticated_client, lab_path):
        """
        Verify that we can list lab networks.
        """
        r = authenticated_client.api.list_lab_networks(lab_path)
        assert r["data"] is not None

    def test_get_non_existing_lab_network_raises(self, authenticated_client, lab_path):
        """
        Verify that we missing lab network raises an error.
        """
        with pytest.raises(EvengHTTPError):
            authenticated_client.api.get_lab_network(lab_path, "1")

    @pytest.mark.xfail(
        reason="TODO: fix `get_lab_network_by_name` - is returning network types"
    )
    def test_get_lab_network_by_name(
        self, authenticated_client, lab_path, network_name
    ):
        """
        Verify that we can retrieve a specific lab by name
        """
        authenticated_client.api.add_lab_network(lab_path, name=network_name)
        r2 = authenticated_client.api.get_lab_network_by_name(lab_path, network_name)
        assert r2["name"] is not None

    def test_list_lab_links(self, authenticated_client, lab_path):
        """
        Get all remote endpoints for both ethernet
        and serial interfaces. Returns dictionary
        of existing links or empty dictionary.
        """
        r = authenticated_client.api.list_lab_links(lab_path)
        assert r["status"] == "success"
        assert r["data"] is not None

    @pytest.mark.parametrize(
        "name, network_type, visibility",
        [("bridge_network", "bridge", "1"), ("cloud0", "pnet0", "1")],
    )
    def test_add_network(
        self, authenticated_client, lab_path, name, network_type, visibility
    ):
        resp = authenticated_client.api.add_lab_network(
            lab_path, network_type=network_type, name=name, visibility=visibility
        )
        # ID is returned after creation
        network_id = resp.get("data", {}).get("id")
        assert int(network_id)

        # network name exists in lab networks
        r = authenticated_client.api.get_lab_network(lab_path, network_id)

        assert r["data"]["name"] == name

    @pytest.mark.parametrize(
        "network_type, visibility",
        [("point-to-point", "1"), ("pnet10", "1")],
    )
    def test_add_invalid_network_raises(
        self, authenticated_client, lab, network_type, visibility
    ):
        # validate invalid network type raises
        # validate pnet not in (pnet0 - pnet9) range is invalid
        with pytest.raises(ValueError):
            lab_path = lab["path"] + lab["name"]
            authenticated_client.api.add_lab_network(
                lab_path, network_type, visibility=visibility
            )

    def test_edit_network(self, authenticated_client, lab, lab_path):
        net = dict(name="test_network", network_type="bridge", visibility="1")
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
    def test_delete_network(self, authenticated_client, lab_path):
        net = dict(name="bridge_network", network_type="bridge")
        add_resp = authenticated_client.api.add_lab_network(lab_path, **net)
        net_id = add_resp.get("data", {}).get("id")

        print(f"deleting net_id: {net_id}")
        del_resp = authenticated_client.api.delete_lab_network(lab_path, net_id)
        assert del_resp["status"] == "success"
