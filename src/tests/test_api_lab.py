import pytest

from evengsdk.exceptions import EvengHTTPError


LAB_PATH = "/datacenter/"
LAB_NAME = "leaf_spine_lab"
EXT = ".unl"


TESTLAB = {
    "name": "TestLab",
    "path": "/",
    "description": "short description",
    "version": "1",
    "body": "longer description",
}


class TestEvengApiLab:
    """Test cases"""

    def test_api_get_lab_wo_extension(self, authenticated_client):
        """
        Retrieve Lab details without file extension
        """
        fullpath = LAB_PATH + LAB_NAME
        resp = authenticated_client.api.get_lab(fullpath)
        assert resp["data"]["name"] == LAB_NAME

    def test_api_get_lab_w_extension(self, authenticated_client):
        """
        Retrieve Lab details with file extension
        """
        fullpath = LAB_PATH + LAB_NAME + EXT
        resp = authenticated_client.api.get_lab(fullpath)
        assert resp["data"]["name"] == LAB_NAME

    def test_get_non_existing_lab(self, authenticated_client):
        """
        Verify that retrieving a non existing lab
        raises an error.
        """
        with pytest.raises(EvengHTTPError):
            authenticated_client.api.get_lab("FAKE_LAB_PATH")

    def test_create_lab(self, authenticated_client):
        resp = authenticated_client.api.create_lab(**TESTLAB)
        assert resp["status"] == "success"

    def test_edit_lab(self, authenticated_client):
        long_description = "longer description with edit"
        lab_path = TESTLAB["path"] + TESTLAB["name"]
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
    def test_edit_lab_unsupported_params(self, authenticated_client, params):
        with pytest.raises(ValueError):
            lab_path = TESTLAB["path"] + TESTLAB["name"]
            authenticated_client.api.edit_lab(lab_path, params)

    def test_lock_lab(self, authenticated_client):
        lab_path = TESTLAB["path"] + TESTLAB["name"]
        resp = authenticated_client.api.lock_lab(lab_path)
        assert resp["status"] == "success"

    def test_unlock_lab(self, authenticated_client):
        lab_path = TESTLAB["path"] + TESTLAB["name"]
        resp = authenticated_client.api.unlock_lab(lab_path)
        assert resp["status"] == "success"

    def test_get_lab_topology(self, authenticated_client):
        lab_path = TESTLAB["path"] + TESTLAB["name"]
        resp = authenticated_client.api.get_lab(lab_path)
        assert resp["data"]["name"] == TESTLAB["name"]
        lab_path = TESTLAB["path"] + TESTLAB["name"]

    def test_delete_lab(self, authenticated_client):
        lab_path = TESTLAB["path"] + TESTLAB["name"]
        resp = authenticated_client.api.delete_lab(lab_path)
        assert resp["status"] == "success"
