# -*- coding: utf-8 -*-
import re

import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


def run_cli_command(commands: list) -> Result:
    """Helper function to Run CLI command."""
    runner: CliRunner = CliRunner()
    return runner.invoke(cli, commands)


@pytest.fixture(scope="module")
def test_lab(cli_lab, cli_lab_path):
    """Create Test user."""
    cli_args = [
        "--name",
        cli_lab["name"],
        "--description",
        cli_lab["description"],
        "--path",
        cli_lab["path"],
    ]
    yield run_cli_command(["lab", "create", *cli_args])
    run_cli_command(["lab", "delete", "--path", cli_lab_path])


@pytest.mark.usefixtures("test_lab")
class TestLabCommands:
    """CLI Lab Commands"""

    def test_lab_single_edit(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: The output indicates that lab is updated successfully.
        """
        result = run_cli_command(
            ["lab", "edit", "--version", "2", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output
        assert "success" in result.output.lower()

    def test_lab_edit_multiple_fields_fails(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: That only a single field can be set a time.
        """
        result = run_cli_command(
            [
                "lab",
                "edit",
                "--version",
                "3",
                "--author",
                "tester",
                "--path",
                cli_lab_path,
            ]
        )
        assert result.exit_code > 0, result.output
        assert "may only set one at a time" in result.output.lower()

    def test_lab_read(self, cli_lab, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand.
        Assert: The output indicates that lab is retrieved successfully.
        """
        result = run_cli_command(["lab", "read", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output
        assert cli_lab["name"] in result.output

    def test_lab_read_non_existent(self):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand for a non-existant lab.
        Assert: The output indicates that lab is retrieved successfully.
        """
        result = run_cli_command(["lab", "read", "--path", "/n0n-e0xist"])
        assert result.exit_code > 0, result.output
        assert "does not exist" in result.output.lower()

    def test_lab_delete_non_existent(self):
        """
        Arrange/Act: Run the `lab` command with the 'delete' subcommand.
        Assert: The output indicates that lab is deleted successfully.
        """
        result = run_cli_command(["lab", "delete", "--path", "/n0n-existent"])
        assert result.exit_code > 0, result.output
        assert "does not exist" in result.output.lower()

    def test_lab_start(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'start' subcommand.
        Assert: The output indicates that lab is started successfully.
        """
        result = run_cli_command(["lab", "start", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    def test_lab_stop(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'stop' subcommand.
        Assert: The output indicates that lab is stopped successfully.
        """
        result = run_cli_command(["lab", "stop", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    def test_lab_list(self):
        """
        Arrange/Act: Run the `lab` command with the 'list' subcommand.
        Assert: The output indicates that labs are listed successfully.
        """
        result = run_cli_command(["lab", "list"])
        assert result.exit_code == 0, result.output

    def test_list_lab_empty_topology(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology is retrieved
            successfully.
        """
        result = run_cli_command(["lab", "topology", "--path", cli_lab_path])
        assert result.exit_code > 0
        assert "lab empty?" in result.output.lower()


@pytest.mark.usefixtures("test_lab")
class TestImportExportCommands:
    """Test Import/Export Commands"""

    def test_lab_export_and_import(self, cli_lab_path, authenticated_client):
        """
        Arrange/Act: Run the `lab` command with the 'export' subcommand.
        Assert: The output indicates that lab exported successfully.
        """
        path = f"{cli_lab_path}.unl"
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": path})
        with runner.isolated_filesystem():
            # Export the lab
            result: Result = runner.invoke(cli, ["lab", "export", "--path", path])
            assert result.exit_code == 0, result.output
            assert "Lab exported" in result.output

            # replace ansi escape sequences
            # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            result = ansi_escape.sub("", result.output)

            # grab the exported lab
            if authenticated_client.api.is_community:
                match = re.search(r"unetlab_.*zip", result)
            else:
                match = re.search(r"eve-ng_.*zip", result)
            zipname = match[0]

            # Import the lab
            result2: Result = runner.invoke(cli, ["lab", "import", "--src", zipname])
            assert result2.exit_code == 0, result2.output
            assert "imported" in result2.output
