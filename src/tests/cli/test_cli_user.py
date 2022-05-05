# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


def run_cli_command(commands: list) -> Result:
    """Helper function to Run CLI command."""
    runner: CliRunner = CliRunner()
    return runner.invoke(cli, commands)


@pytest.fixture(scope="session")
def test_user(test_user_data):
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
    yield run_cli_command(["user", "create", *cli_args])
    run_cli_command(["user", "delete", "-u", test_user_data["username"]])


@pytest.mark.usefixtures("test_user")
class TestUserCommands:
    """Test user CLI commands."""

    def test_user_list(self, test_user_data):
        """
        Arrange/Act: Run the `user` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = run_cli_command(["user", "list"])
        assert result.exit_code == 0, result.output
        assert test_user_data["username"] in result.output

    def test_user_read(self, test_user_data):  # noqa: F811
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = run_cli_command(["user", "read", "-u", test_user_data["username"]])
        assert result.exit_code == 0, result.output

    def test_user_edit(self, test_user_data):
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
        result = run_cli_command(commands)
        assert result.exit_code == 0, result.output
