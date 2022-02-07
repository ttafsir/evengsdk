# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


TEST_USER = {
    "username": "testuser99",
    "password": "password1",
    "expiration": "-1",
    "role": "admin",
    "name": "John Doe",
    "email": "john.doe@acme.com",
}


@pytest.fixture()
def test_user():
    return TEST_USER.copy()


@pytest.mark.usefixtures("setup_cli_lab")
class TestUserCommands:
    def _run_commands(self, commands: list) -> Result:
        runner: CliRunner = CliRunner()
        return runner.invoke(cli, commands)

    def test_user_create(self, test_user):
        """
        Arrange/Act: Run the `user` command with the 'create' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        cli_commands = [
            "user",
            "create",
            "--username",
            test_user["username"],
            "--password",
            test_user["password"],
            "--expiration",
            test_user["expiration"],
            "--role",
            test_user["role"],
            "--name",
            test_user["name"],
            "--email",
            test_user["email"],
        ]

        result = self._run_commands(cli_commands)
        assert result.exit_code == 0, result.output

    def test_user_list(self):
        """
        Arrange/Act: Run the `user` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = self._run_commands(["user", "list"])
        assert result.exit_code == 0, result.output

    def test_user_read(self, test_user):
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = self._run_commands(["user", "read", "-u", test_user["username"]])
        assert result.exit_code == 0, result.output

    def test_user_edit(self, test_user):
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        edited_user = test_user.copy()
        edited_user["name"] = "John Doe edited"
        commands = [
            "user",
            "edit",
            "--username",
            edited_user["username"],
            "--name",
            edited_user["name"],
            "--email",
            edited_user["email"],
            "--role",
            edited_user["role"],
            "--expiration",
            edited_user["expiration"],
            "--password",
            edited_user["password"],
        ]
        result = self._run_commands(commands)
        assert result.exit_code == 0, result.output

    def test_user_delete(self, test_user):
        """
        Arrange/Act: Run the `user` command with the 'delete' subcommand.
        Assert: The output indicates that lab deleted successfully.
        """
        result = self._run_commands(["user", "delete", "-u", test_user["username"]])
        assert result.exit_code == 0, result.output
