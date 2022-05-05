import pytest

from evengsdk.exceptions import EvengHTTPError


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

    def test_get_lab_network_by_name(
        self, authenticated_client, lab_path, test_network, test_network_data
    ):
        """
        Verify that we can retrieve a specific lab by name
        """
        resp = authenticated_client.api.get_lab_network(lab_path, test_network)
        assert resp["data"]["name"] == test_network_data["name"]

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
        if not authenticated_client.api.is_community and network_type == "pnet0":
            pytest.skip("pnet0 is not supported for pro version")

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

    def test_edit_network(self, authenticated_client, lab_path, test_network):
        """Edit a network"""
        data = {"name": "new_name"}
        edit_resp = authenticated_client.api.edit_lab_network(
            lab_path, test_network, data=data
        )

        # retrieve the edited network
        lab_networks = authenticated_client.api.list_lab_networks(lab_path)

        assert edit_resp["code"] == 201
        assert lab_networks["data"][f"{test_network}"]["name"] == "new_name"
