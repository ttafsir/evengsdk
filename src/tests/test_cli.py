# -*- coding: utf-8 -*-
import json

from click.testing import CliRunner, Result
from dotenv import load_dotenv

from evengsdk.cli.cli import main as cli
from evengsdk.cli.version import __version__


def test_version_displays_library_version():
    """
    Arrange/Act: Run the `version` subcommand.
    Assert: The output matches the library version.
    """
    runner: CliRunner = CliRunner()
    result: Result = runner.invoke(cli, ["version"])
    assert (
        __version__ in result.output.strip()
    ), "Version number should match library version."
