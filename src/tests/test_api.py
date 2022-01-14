import pytest

from evengsdk.exceptions import EvengHTTPError


LAB_PATH = "/datacenter/leaf_spine_lab.unl"
USERS = {
    "to_create": [("tester1", "test1_pass"), ("tester2", "test2_pass")],
    "non_existing": "fake_user99",
}
TEST_NETWORK = "vCloud"
TEST_NODE = "leaf04"
TEST_CONFIG = """
!
hostname vEOS4
!
"""


class TestEvengApi:
    """Test cases"""

    def test_api_get_server_status(self, authenticated_client):
        """
        Verify server status using the API
        """
        r = authenticated_client.api.get_server_status()
        assert r["data"].get("cpu") is not None

    def test_list_node_templates(self, authenticated_client):
        """
        Verify we can list node templates from API
        """
        r = authenticated_client.api.list_node_templates()
        assert r["data"] is not None

    def test_node_template_detail(self, authenticated_client):
        """
        Verify that we get retrieve the details of a node template
        """
        node_types = ["a10"]
        for n_type in node_types:
            detail = authenticated_client.api.node_template_detail(n_type)
            assert isinstance(detail, dict)

    def test_list_users(self, authenticated_client):
        """
        Verify that we can retrieve list of users and that
        the default 'admin' user  exists.
        """
        r = authenticated_client.api.list_users()
        assert "admin" in r["data"]

    def test_list_user_roles(self, authenticated_client):
        """
        Verify that we can retrieve list of user roles
        """
        r = authenticated_client.api.list_user_roles()
        assert "admin" in r["data"]

    def test_get_user(self, authenticated_client):
        """
        Verify that we can retrieve a single user detail
        """
        r = authenticated_client.api.get_user("admin")
        assert "email" in r["data"]

    def test_get_non_existing_user(self, authenticated_client):
        """
        Verify that the api returns an empty dictionary
        if the user does not exist
        """
        with pytest.raises(EvengHTTPError):
            user = USERS["non_existing"]
            authenticated_client.api.get_user(user)

    def test_add_user(self, authenticated_client):
        """
        Verify that we can created a user with just
        the username and password
        """
        for username, password in iter(USERS["to_create"]):
            try:
                r = authenticated_client.api.add_user(username, password)
                assert r["status"] == "success"
            except EvengHTTPError as e:
                assert "check if already exists" in str(e)

    def test_add_existing_user(self, authenticated_client):
        """
        Verify that adding an existing user raises
        an exception
        """
        for username, password in iter(USERS["to_create"]):
            with pytest.raises(EvengHTTPError):
                authenticated_client.api.add_user(username, password)

    def test_edit_existing_user(self, authenticated_client):
        """
        Verify that we can edit existing user
        """
        new_data = {"email": "test1@testing.com", "name": "John Doe"}
        user = USERS["to_create"][0]
        # edit user
        authenticated_client.api.edit_user(user[0], data=new_data)

        # retrieve updates
        r = authenticated_client.api.get_user(user[0])

        # ensure new data was PUT successfully
        assert r["data"]["email"] == new_data["email"]

    def test_edit_non_existing_user(self, authenticated_client):
        """
        Verify that editing non existing users raises
        an exception.
        """
        with pytest.raises(EvengHTTPError):
            new_data = {"email": "test@testing.com", "name": "John Doe"}
            username = USERS["non_existing"]
            authenticated_client.api.edit_user(username, data=new_data)

    def test_edit_user_w_missing_data_raises(self, authenticated_client):
        """Editing a using without missing data should raise
        a ValueError.
        """
        with pytest.raises(ValueError):
            authenticated_client.api.edit_user("test_user", data={})

    def test_delete_user(self, authenticated_client):
        """
        Verify that we can delete users
        """
        for username, _ in iter(USERS["to_create"]):
            r = authenticated_client.api.delete_user(username)
            assert r["status"] == "success"

            # make sure it was deleted
            with pytest.raises(EvengHTTPError):
                authenticated_client.api.get_user(username)

    def test_list_networks(self, authenticated_client):
        """
        Verify that we can retrieve EVE-NG networks. The
        data returned is a dictionary that includes
        network types and instances.
        """
        r = authenticated_client.api.list_networks()
        assert r["data"]["bridge"] is not None

    def test_list_lab_networks(self, authenticated_client):
        """
        Verify that we can list lab networks.
        """
        r = authenticated_client.api.list_lab_networks(LAB_PATH)
        assert r["data"] is not None

    def test_get_lab_network(self, authenticated_client):
        """
        Verify that we can retrieve a specific lab by id
        """
        r = authenticated_client.api.get_lab_network(LAB_PATH, "1")
        assert r["data"]["type"] is not None

    def test_get_lab_network_by_name(self, authenticated_client):
        """
        Verify that we can retrieve a specific lab by name
        """
        r = authenticated_client.api.get_lab_network_by_name(LAB_PATH, TEST_NETWORK)
        assert r["name"] is not None

    def test_list_lab_links(self, authenticated_client):
        """
        Get all remote endpoints for both ethernet
        and serial interfaces. Returns dictionary
        of existing links or empty dictionary.
        """
        r = authenticated_client.api.list_lab_links(LAB_PATH)
        assert r["status"] == "success"
        assert r["data"] is not None

    def test_list_nodes(self, authenticated_client):
        """
        Verify that we can retrieve all node details
        """
        r = authenticated_client.api.list_nodes(LAB_PATH)
        assert r["status"] == "success"
        assert r["data"] is not None

    def test_get_node(self, authenticated_client):
        """
        Verify that we can details for a single node by ID
        """
        # get with node with ID == 1
        node = authenticated_client.api.get_node(LAB_PATH, "1")
        assert node["data"]["type"] is not None

    def test_add_node(self, authenticated_client):
        """
        Verify that we can details for a single node by ID
        """
        node = {
            "node_type": "qemu",
            "template": "csr1000v",
            "image": "csr1000v-universalk9-16.06.06",
            "name": "CSR1",
            "ethernet": 4,
            "cpu": 2,
            "serial": 2,
            "delay": 0,
        }
        r = authenticated_client.api.add_node(LAB_PATH, **node)
        assert r["status"] == "success"
        assert r["data"]

    def test_get_node_by_name(self, authenticated_client):
        """
        Verify that we can details for a single node by node name
        """
        # get with node with name == TEST_NODE
        r = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        assert r["name"] == TEST_NODE

    def test_get_node_configs(self, authenticated_client):
        """
        Verify that we can retrieve information about the
        node configs
        """
        config_info = authenticated_client.api.get_node_configs(LAB_PATH)
        assert config_info

    def test_get_node_config_by_id(self, authenticated_client):
        """
        Verify that we can retrieve configuration data
        using a specific config ID
        """
        config = authenticated_client.api.get_node_config_by_id(LAB_PATH, "1")
        assert config["data"] is not None

    def test_upload_node_config(self, authenticated_client):
        """
        Upload node's config to set startup config
        """
        resp = authenticated_client.api.get_node_configs(LAB_PATH)
        node_id = next(
            (k for k, v in resp["data"].items() if v["name"] == TEST_NODE), None
        )
        upload_resp = authenticated_client.api.upload_node_config(
            LAB_PATH, node_id, config=TEST_CONFIG
        )
        assert upload_resp["status"] == "success"
        assert "Lab has been saved" in upload_resp["message"]

    def test_stop_all_nodes(self, authenticated_client):
        """
        Stop all nodes in the lab
        """
        result = authenticated_client.api.stop_all_nodes(LAB_PATH)
        assert result["status"] == "success"

    @pytest.mark.slow
    def test_start_all_nodes(self, authenticated_client):
        """
        Start all nodes in the lab
        """
        result = authenticated_client.api.start_all_nodes(LAB_PATH)
        assert result["status"] == "success"

    def test_stop_node(self, authenticated_client):
        """
        Stop a single node in the lab
        """
        node = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = authenticated_client.api.stop_node(LAB_PATH, node["id"])
        assert result["status"] == "success"

    def test_start_node(self, authenticated_client):
        """
        Start a single node in the lab
        """
        node = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = authenticated_client.api.start_node(LAB_PATH, node["id"])
        assert result["status"] == "success"

    def test_wipe_all_nodes(self, authenticated_client):
        """
        Wipe all node startup configs and VLAN db
        """
        result = authenticated_client.api.wipe_all_nodes(LAB_PATH)
        assert result["status"] == "success"

    def test_wipe_node(self, authenticated_client):
        """
        Wipe node startup configs and VLAN db
        """
        node = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = authenticated_client.api.wipe_node(LAB_PATH, node["id"])
        assert result["status"] == "success"

    @pytest.mark.xfail
    def test_export_all_nodes(self, authenticated_client):
        """
        Save all startup configs to lab
        """
        result = authenticated_client.api.export_all_nodes(LAB_PATH)
        assert result["status"] == "success"

    @pytest.mark.xfail
    def test_export_node(self, authenticated_client):
        """
        Save node startup-config to lab
        """
        node = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = authenticated_client.api.export_node(LAB_PATH, node["id"])
        assert result["status"] == "success"

    def test_get_node_interfaces(self, authenticated_client):
        """
        Get configured interfaces from a node
        """
        node = authenticated_client.api.get_node_by_name(LAB_PATH, TEST_NODE)
        result = authenticated_client.api.get_node_interfaces(LAB_PATH, node["id"])
        assert result is not None
        assert isinstance(result, dict)

    def test_list_lab_pictures(self, authenticated_client):
        resp = authenticated_client.api.get_lab_pictures(LAB_PATH)
        assert resp["status"] == "success"
