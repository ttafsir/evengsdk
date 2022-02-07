import pytest

from evengsdk.exceptions import EvengHTTPError


USERS = {
    "to_create": [("tester1", "test1_pass"), ("tester2", "test2_pass")],
    "non_existing": "fake_user99",
}


class TestEvengApiUser:
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
