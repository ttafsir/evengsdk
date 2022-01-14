# -*- coding: utf-8 -*-
import os
import re

import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli
from evengsdk.cli.version import __version__
from evengsdk.exceptions import EvengHTTPError


LAB_TO_EDIT = {"name": "lab_to_edit", "path": "/"}
LAB_TO_CREATE = {"name": "test lab1", "path": "/test lab1.unl"}
NODE_TO_CREATE = {
    "node_type": "qemu",
    "template": "csr1000v",
    "image": "csr1000v-universalk9-16.06.06",
    "name": "CSR1",
    "ethernet": 4,
    "cpu": 2,
    "serial": 2,
    "delay": 0,
}
TEST_CONFIG = """
!
hostname vEOS4
!
"""


@pytest.fixture(scope="session")
def lab_to_edit():
    return LAB_TO_EDIT.copy()


@pytest.fixture(scope="session")
def cli_client(client):
    client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    yield client


@pytest.fixture(scope="session")
def setup_test_lab(lab_to_edit, cli_client):
    cli_client.log.debug("starting CLI test..")
    try:
        cli_client.api.create_lab(**lab_to_edit)
    except EvengHTTPError as e:
        if "already exists" not in f"{e}":
            cli_client.log.debug("Lab already exists...skipping setup")
            raise e
    yield
    cli_client.log.debug("cleaning up test session..")
    cli_client.api.delete_lab(lab_to_edit["path"] + lab_to_edit["name"])
    if not cli_client.session:
        cli_client.login(
            username=os.environ["EVE_NG_USERNAME"],
            password=os.environ["EVE_NG_PASSWORD"],
        )
    cli_client.logout()


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
        result: Result = runner.invoke(cli, ["version"])
        assert (
            __version__ in result.output.strip()
        ), "Version number should match library version."


class TestUserCommands:
    def test_user_list(self):
        """
        Arrange/Act: Run the `user` command with the 'list' subcommand.
        Assert: The output indicates that users are listed successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["user", "list"])
        assert result.exit_code == 0, result.output

    def test_user_create(self):
        """
        Arrange/Act: Run the `user` command with the 'create' subcommand.
        Assert: The output indicates that user is created successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["user", "create"])
        assert result.exit_code == 0, result.output

    def test_user_edit(self):
        """
        Arrange/Act: Run the `user` command with the 'edit' subcommand.
        Assert: The output indicates that user is updated successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["user", "edit"])
        assert result.exit_code == 0, result.output

    def test_user_read(self):
        """
        Arrange/Act: Run the `user` command with the 'read' subcommand.
        Assert: The output indicates that user is retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["user", "read"])
        assert result.exit_code == 0, result.output

    def test_user_delete(self):
        """
        Arrange/Act: Run the `user` command with the 'delete' subcommand.
        Assert: The output indicates that user is retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["user", "delete"])
        assert result.exit_code == 0, result.output


class TestLabFolderCommands:
    def test_folder_list(self):
        """
        Arrange/Act: Run the `folder` command with the 'list' subcommand.
        Assert: The output indicates that folders are listed successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "list"])
        assert result.exit_code == 0, result.output

    @pytest.mark.xfail
    def test_folder_create(self):
        """
        Arrange/Act: Run the `folder` command with the 'create' subcommand.
        Assert: The output indicates that folders are create successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "create"])
        assert result.exit_code == 0, result.output

    @pytest.mark.xfail
    def test_folder_read(self):
        """
        Arrange/Act: Run the `folder` command with the 'read' subcommand.
        Assert: The output indicates that folders are retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "read", "/"])
        assert result.exit_code == 0, result.output

    @pytest.mark.xfail
    def test_folder_edit(self):
        """
        Arrange/Act: Run the `folder` command with the 'edit' subcommand.
        Assert: The output indicates that folder is updated successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "edit"])
        assert result.exit_code == 0, result.output

    @pytest.mark.xfail
    def test_folder_delete(self):
        """
        Arrange/Act: Run the `folder` command with the 'delete' subcommand.
        Assert: The output indicates that folder is deleted successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "delete"])
        assert result.exit_code == 0, result.output


class TestLabCommands:
    def test_lab_create(self):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab is created successfully.
        """
        runner: CliRunner = CliRunner()
        cli_args = [
            "lab",
            "create",
            "--author",
            "joe tester",
            "--name",
            f"{LAB_TO_CREATE['name']}",
            "--path",
            "/",
            "--description",
            "Test lab",
            "--version",
            "1",
        ]
        result: Result = runner.invoke(cli, cli_args)
        assert result.exit_code == 0 or "Lab already exists" in str(result.output)

    def test_lab_create_without_name_raises(self):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab is created successfully.
        """
        runner: CliRunner = CliRunner()
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
        result: Result = runner.invoke(cli, cli_args)
        assert result.exit_code > 0
        assert "Missing option" in result.output

    def test_lab_edit(self, lab_to_edit):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: The output indicates that lab is updated successfully.
        """
        edit_cli_args = [
            "lab",
            "edit",
            "--version",
            "2",
            "--path",
            f"{lab_to_edit['path']}{lab_to_edit['name']}.unl",
        ]
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, edit_cli_args)
        assert result.exit_code == 0, result.output
        # LAB_TO_EDIT['path'] = f"{LAB_TO_EDIT['path']}{edited_name}.unl"

    def test_lab_read(self):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand.
        Assert: The output indicates that lab is retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(
            cli, ["lab", "read", "--path", LAB_TO_CREATE["path"]]
        )
        assert result.exit_code == 0, result.output

    def test_lab_delete(self):
        """
        Arrange/Act: Run the `lab` command with the 'delete' subcommand.
        Assert: The output indicates that lab is deleted successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(
            cli, ["lab", "delete", "--path", LAB_TO_CREATE["path"]]
        )
        assert result.exit_code == 0, result.output

    def test_lab_start(self):
        """
        Arrange/Act: Run the `lab` command with the 'start' subcommand.
        Assert: The output indicates that lab is started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "start"])
        assert result.exit_code == 0, result.output

    def test_lab_stop(self):
        """
        Arrange/Act: Run the `lab` command with the 'stop' subcommand.
        Assert: The output indicates that lab is stopped successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "stop"])
        assert result.exit_code == 0, result.output

    def test_lab_list(self):
        """
        Arrange/Act: Run the `lab` command with the 'list' subcommand.
        Assert: The output indicates that labs are listed successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "list"])
        assert result.exit_code == 0, result.output

    def test_list_lab_topology(self):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology is retrieved
            successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "topology"])
        assert result.exit_code == 0, result.output


class TestImportExportCommands:
    def test_lab_export_and_import(self, lab_to_edit, setup_test_lab):
        """
        Arrange/Act: Run the `lab` command with the 'export' subcommand.
        Assert: The output indicates that lab exported successfully.
        """
        path = f"{lab_to_edit['path']}{lab_to_edit['name']}.unl"
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": path})
        with runner.isolated_filesystem():
            # Export the lab
            result: Result = runner.invoke(cli, ["lab", "export", "--path", path])
            assert result.exit_code == 0, result.output
            assert "Lab exported" in result.output

            # grab the exported lab
            match = re.search(r"unetlab_.*zip", result.output)
            zipname = match.group(0)

            # Import the lab
            result2: Result = runner.invoke(cli, ["lab", "import", "--src", zipname])
            assert result2.exit_code == 0, result2.output
            assert "imported" in result2.output
