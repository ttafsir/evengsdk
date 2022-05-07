# -*- coding: utf-8 -*-
import pytest


@pytest.fixture(scope="session")
def test_user(test_user_data, helpers):
    """Create Test user."""
    cli_args = [
        "--username",
        test_user_data["username"],
        "--password",
        test_user_data["password"],
        "--expiration",
        test_user_data["expiration"],
        "--role",
        test_user_data["role"],
        "--name",
        test_user_data["name"],
        "--email",
        test_user_data["email"],
    ]
    yield helpers.run_cli_command(["user", "create", *cli_args])
    helpers.run_cli_command(["user", "delete", "-u", test_user_data["username"]])


@pytest.mark.usefixtures("test_user")
class TestUserCommands:
    """Test user CLI commands."""

    def test_user_list(self, test_user_data, helpers):
        """
        Arrange/Act: Run the `user` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = helpers.run_cli_command(["user", "list"])
        assert result.exit_code == 0, result.output
        assert test_user_data["username"] in result.output

    def test_user_read(self, test_user_data, helpers):  # noqa: F811
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = helpers.run_cli_command(
            ["user", "read", "-u", test_user_data["username"]]
        )
        assert test_user_data["username"] in result.output

    def test_user_edit(self, test_user_data, helpers):
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        edited_user = test_user_data.copy()
        edited_user["name"] = "John Doe edited"
        commands = [
            "user",
            "edit",
            "--username",
            edited_user["username"],
        ]
        result = helpers.run_cli_command(commands)
        assert "User saved" in result.output

    @pytest.mark.parametrize("subcommand", ["read", "edit", "delete"])
    def test_user_update_non_existent(self, helpers, subcommand):
        """
        Arrange/Act: Run the `user` command with crud subcommands for a non-existant lab.
        Assert: The output indicates that lab is errors are correctly displayed without traceback.
        """
        result = helpers.run_cli_command(["user", subcommand, "-u", "fake_user"])
        assert result.exit_code > 0, result.output
        assert "User not found" in result.output
