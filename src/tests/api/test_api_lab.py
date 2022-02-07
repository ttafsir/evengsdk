import pytest

from evengsdk.exceptions import EvengHTTPError


@pytest.mark.usefixtures("setup_lab")
class TestEvengApiLab:
    """Test cases"""

    def test_api_get_lab_wo_extension(self, authenticated_client, lab, lab_path):
        """
        Retrieve Lab details without file extension
        """
        resp = authenticated_client.api.get_lab(lab_path)
        assert resp["data"]["name"] == lab["name"]

    def test_api_get_lab_w_extension(self, authenticated_client, lab, lab_path):
        """
        Retrieve Lab details with file extension
        """
        resp = authenticated_client.api.get_lab(lab_path)
        assert resp["data"]["name"] == lab["name"]

    def test_get_non_existing_lab(self, authenticated_client):
        """
        Verify that retrieving a non existing lab
        raises an error.
        """
        with pytest.raises(EvengHTTPError):
            authenticated_client.api.get_lab("FAKE_LAB_PATH")

    def test_edit_lab(self, authenticated_client, lab_path):
        long_description = "longer description with edit"
        edited_param = {"body": long_description}
        resp = authenticated_client.api.edit_lab(lab_path, edited_param)
        assert resp["status"] == "success"

    @pytest.mark.parametrize(
        "params",
        [
            {"long_description": "test unknown param"},
            {"name": "new_test", "description": "test"},
        ],
    )
    def test_edit_lab_unsupported_params(self, authenticated_client, params, lab_path):
        with pytest.raises(ValueError):
            authenticated_client.api.edit_lab(lab_path, params)

    def test_lock_lab(self, authenticated_client, lab_path):
        resp = authenticated_client.api.lock_lab(lab_path)
        assert resp["status"] == "success"

    def test_unlock_lab(self, authenticated_client, lab_path):
        resp = authenticated_client.api.unlock_lab(lab_path)
        assert resp["status"] == "success"

    def test_get_lab_topology(self, authenticated_client, lab_path, lab):
        resp = authenticated_client.api.get_lab(lab_path)
        assert resp["data"]["name"] == lab["name"]

    def test_list_lab_pictures(self, authenticated_client, lab_path):
        resp = authenticated_client.api.get_lab_pictures(lab_path)
        assert resp["status"] == "success"
