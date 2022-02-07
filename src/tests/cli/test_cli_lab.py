# -*- coding: utf-8 -*-
import re

import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


LAB_TO_CREATE = {"name": "test lab1", "path": "/test lab1.unl"}


@pytest.fixture(scope="module")
def lab_to_create(authenticated_client):
    lab = LAB_TO_CREATE.copy()
    yield lab
    authenticated_client.api.delete_lab(lab["path"])


@pytest.mark.usefixtures("setup_cli_lab")
class TestLabCommands:
    def _run_commands(self, commands, lab_path=None):
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": lab_path})
        return runner.invoke(cli, commands)

    def test_lab_create(self, lab_to_create):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab is created successfully.
        """
        cli_args = [
            "lab",
            "create",
            "--author",
            "joe tester",
            "--name",
            f"{lab_to_create['name']}",
            "--path",
            "/",
            "--description",
            "Test lab",
            "--version",
            "1",
        ]
        result = self._run_commands(cli_args)
        assert result.exit_code == 0  # or "Lab already exists" in str(result.output)

    def test_lab_create_without_name_raises(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab is created successfully.
        """
        cli_args = [
            "lab",
            "create",
            "--author",
            "joe tester",
            "--path",
            "/",
            "--description",
            "Test lab",
            "--version",
            "1",
        ]
        result = self._run_commands(cli_args, cli_lab_path)
        assert result.exit_code > 0
        assert "Missing option" in result.output

    def test_lab_edit(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: The output indicates that lab is updated successfully.
        """
        cli_args = ["lab", "edit", "--version", "2"]
        result = self._run_commands(cli_args, cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_read(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand.
        Assert: The output indicates that lab is retrieved successfully.
        """
        cli_args = ["lab", "read"]
        result = self._run_commands(cli_args, cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_start(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'start' subcommand.
        Assert: The output indicates that lab is started successfully.
        """
        result = self._run_commands(["lab", "start"], cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_stop(self, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'stop' subcommand.
        Assert: The output indicates that lab is stopped successfully.
        """
        result = self._run_commands(["lab", "stop"], cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_list(self):
        """
        Arrange/Act: Run the `lab` command with the 'list' subcommand.
        Assert: The output indicates that labs are listed successfully.
        """
        result = self._run_commands(["lab", "list"])
        assert result.exit_code == 0, result.output

    @pytest.mark.skip(reason="TODO: fix empty lab raises error")
    def test_list_lab_topology(self):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology is retrieved
            successfully.
        """
        result = self._run_commands(["lab", "topology"])
        assert result.exit_code == 0, result.output


@pytest.mark.usefixtures("setup_cli_lab")
class TestImportExportCommands:
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
            zipname = match.group(0)

            # Import the lab
            result2: Result = runner.invoke(cli, ["lab", "import", "--src", zipname])
            assert result2.exit_code == 0, result2.output
            assert "imported" in result2.output
