# -*- coding: utf-8 -*-
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli
from evengsdk.cli.version import __version__


class TestCli:
    """Test general functionality of the CLI"""

    def test_entrypoint(self):
        """
        Is entrypoint script installed? (setup.py)
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_version_displays_library_version(self):
        """
        Arrange/Act: Run the `version` subcommand.
        Assert: The output matches the library version.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["--version"])
        assert (
            __version__ in result.output.strip()
        ), "Version number should match library version."


class TestCliUnauthenticated:
    """Test CLI with unauthenticated user."""

    def test_cli_login_with_invalid_credentials(self):
        """
        Arrange/Act: Run a CLI command with invalid credentials.
        Assert: The output matches the expected error message and not the traceback.
        """
        env_vars = {"EVE_NG_USERNAME": "invalid", "EVE_NG_PASSWORD": "invalid"}
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "list"], env=env_vars)
        assert (
            "Authentication failed" in result.output.strip()
        ), "Error message should match expected error message."
