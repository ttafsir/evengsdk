# -*- coding: utf-8 -*-
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli
from evengsdk.cli.version import __version__


class TestCli:
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
