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

    def test_list_network_types(self, authenticated_client):
        """
        Verify that we can retrieve EVE-NG networks. The
        data returned is a dictionary that includes
        network types and instances.
        """
        r = authenticated_client.api.list_networks()
        assert r["data"]["bridge"] is not None
