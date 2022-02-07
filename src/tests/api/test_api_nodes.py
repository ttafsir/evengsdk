import pytest


@pytest.fixture()
def test_config():
    return """
!
hostname vEOS4
!
"""


@pytest.fixture()
def test_node():
    return {
        "node_type": "qemu",
        "template": "veos",
        "image": "veos-4.27.0F",
        "name": "leaf99",
        "ethernet": 4,
        "cpu": 2,
        "serial": 2,
        "delay": 0,
    }


@pytest.mark.usefixtures("setup_lab")
class TestEvengApiNodes:
    """Test cases for Lab nodes"""

    def test_list_nodes(self, authenticated_client, lab_path):
        """
        Verify that we can retrieve all node details
        """
        r = authenticated_client.api.list_nodes(lab_path)
        assert r["status"] == "success"
        assert r["data"] is not None

    def test_add_node(self, authenticated_client, lab_path, test_node):
        """
        Verify that we can details for a single node by ID
        """
        r = authenticated_client.api.add_node(lab_path, **test_node)
        assert r["status"] == "success"

    def test_get_node(self, authenticated_client, lab_path):
        """
        Verify that we can details for a single node by ID
        """
        # get with node with ID == 1
        node = authenticated_client.api.get_node(lab_path, 1)
        assert node["data"]["type"] is not None

    def test_get_node_by_name(self, authenticated_client, lab_path, test_node):
        """
        Verify that we can details for a single node by node name
        """
        # get with node with name == test_node
        r = authenticated_client.api.get_node_by_name(lab_path, test_node["name"])
        assert r["name"] == test_node["name"]

    def test_get_node_configs(self, authenticated_client, lab_path):
        """
        Verify that we can retrieve information about the
        node configs
        """
        config_info = authenticated_client.api.get_node_configs(lab_path)
        assert config_info

    def test_get_node_config_by_id(self, authenticated_client, lab_path):
        """
        Verify that we can retrieve configuration data
        using a specific config ID
        """
        config = authenticated_client.api.get_node_config_by_id(lab_path, 1)
        print(config)
        assert config["data"] is not None

    def test_upload_node_config(
        self, authenticated_client, lab_path, test_node, test_config
    ):
        """
        Upload node's config to set startup config
        """
        resp = authenticated_client.api.get_node_configs(lab_path)
        node_id = next(
            (k for k, v in resp["data"].items() if v["name"] == test_node["name"]), None
        )
        upload_resp = authenticated_client.api.upload_node_config(
            lab_path, node_id, config=test_config
        )
        assert upload_resp["status"] == "success"
        assert "Lab has been saved" in upload_resp["message"]

    def test_stop_all_nodes(self, authenticated_client, lab_path):
        """
        Stop all nodes in the lab
        """
        result = authenticated_client.api.stop_all_nodes(lab_path)
        assert result["status"] == "success"

    @pytest.mark.slow
    def test_start_all_nodes(self, authenticated_client, lab_path):
        """
        Start all nodes in the lab
        """
        result = authenticated_client.api.start_all_nodes(lab_path)
        print(result)
        if authenticated_client.api.is_community:
            assert result["status"] == "success"
        else:
            for item in result["data"]:
                assert item["status"] == "success"

    def test_stop_node(self, authenticated_client, lab_path, test_node):
        """
        Stop a single node in the lab
        """
        node = authenticated_client.api.get_node_by_name(lab_path, test_node["name"])
        result = authenticated_client.api.stop_node(lab_path, node["id"])
        assert result["status"] == "success"

    def test_start_node(self, authenticated_client, lab_path, test_node):
        """
        Start a single node in the lab
        """
        result = authenticated_client.api.start_node(lab_path, 1)
        assert result["status"] == "success"

    def test_wipe_all_nodes(self, authenticated_client, lab_path):
        """
        Wipe all node startup configs and VLAN db
        """
        result = authenticated_client.api.wipe_all_nodes(lab_path)
        assert result["status"] == "success"

    def test_wipe_node(self, authenticated_client, lab_path, test_node):
        """
        Wipe node startup configs and VLAN db
        """
        node = authenticated_client.api.get_node_by_name(lab_path, test_node["name"])
        result = authenticated_client.api.wipe_node(lab_path, node["id"])
        assert result["status"] == "success"

    @pytest.mark.xfail
    def test_export_all_nodes(self, authenticated_client, lab_path):
        """
        Save all startup configs to lab
        """
        result = authenticated_client.api.export_all_nodes(lab_path)
        assert result["status"] == "success"

    @pytest.mark.xfail
    def test_export_node(self, authenticated_client, lab_path, test_node):
        """
        Save node startup-config to lab
        """
        node = authenticated_client.api.get_node_by_name(lab_path, test_node["name"])
        result = authenticated_client.api.export_node(lab_path, node["id"])
        assert result["status"] == "success"

    def test_get_node_interfaces(self, authenticated_client, lab_path, test_node):
        """
        Get configured interfaces from a node
        """
        node = authenticated_client.api.get_node_by_name(lab_path, test_node["name"])
        result = authenticated_client.api.get_node_interfaces(lab_path, node["id"])
        assert result is not None
        assert isinstance(result, dict)
