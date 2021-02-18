# -*- coding: utf-8 -*-
import json

from click.testing import CliRunner, Result
import pytest

from evengsdk.cli.cli import main as cli
from evengsdk.cli.version import __version__


LAB_TO_EDIT = {"name": "lab_to_edit", "path": "/"}
LAB_TO_CREATE = {"name": "test lab1", "path": "/test lab1.unl"}


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


class TestSystemCommands:
    def test_system_status(self):
        """
        Arrange/Act: Run the `system` command with the 'status' subcommand.
        Assert: The output indicates that a status is successfully returned.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["system", "status"])

        assert result.exit_code == 0, result.output
        assert 'System' in result.output

    def test_system_list_network_types_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'list-network-types'
            subcommand.
        Assert: The output indicates that network types are successfully
            returned.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["system", "list-network-types"])
        assert result.exit_code == 0, result.output

    def test_system_list_node_templates_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'list-templates'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["system", "list-templates"])
        assert result.exit_code == 0, result.output

    def test_system_list_user_roles_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'list-user-roles'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["system", "list-user-roles"])
        assert result.exit_code == 0, result.output

    def test_system_read_template(self):
        """
        Arrange/Act: Run the `system` command with the 'read-template'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["system", "read-template"])
        assert result.exit_code == 0, result.output


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

    def test_folder_create(self):
        """
        Arrange/Act: Run the `folder` command with the 'create' subcommand.
        Assert: The output indicates that folders are create successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "create"])
        assert result.exit_code == 0, result.output

    def test_folder_read(self):
        """
        Arrange/Act: Run the `folder` command with the 'read' subcommand.
        Assert: The output indicates that folders are retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "read"])
        assert result.exit_code == 0, result.output

    def test_folder_edit(self):
        """
        Arrange/Act: Run the `folder` command with the 'edit' subcommand.
        Assert: The output indicates that folder is updated successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["folder", "edit"])
        assert result.exit_code == 0, result.output

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
            "--name", LAB_TO_CREATE["name"],
            "--author", "joe tester",
            "--path", "/",
            "--description", "Test lab",
            "--version", "1"
        ]
        result: Result = runner.invoke(cli, cli_args)
        assert (
            result.exit_code == 0 or
            "Lab already exists" in str(result.exception)
        )

    def test_lab_create_without_name_raises(self):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab is created successfully.
        """
        runner: CliRunner = CliRunner()
        cli_args = [
            "lab",
            "create",
            "--author", "joe tester",
            "--path", "/",
            "--description", "Test lab",
            "--version", "1"
        ]
        result: Result = runner.invoke(cli, cli_args)
        assert isinstance(result.exception, ValueError)

    def test_lab_edit(self):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: The output indicates that lab is updated successfully.
        """
        create_cli_args = [
            "lab",
            "create",
            "--name", LAB_TO_EDIT["name"],
            "--author", "joe tester2",
            "--path", LAB_TO_EDIT["path"],
        ]
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, create_cli_args)
        assert (
            result.exit_code == 0 or
            "Lab already exists" in str(result.exception)
        )

        edited_name = "edited lab"
        edit_cli_args = [
            "lab",
            "edit",
            "--name", edited_name,
            "--path", f"{LAB_TO_EDIT['path']}{LAB_TO_EDIT['name']}.unl",
        ]
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, edit_cli_args)
        assert result.exit_code == 0, result.output
        LAB_TO_EDIT['path'] = f"{LAB_TO_EDIT['path']}{edited_name}.unl"

    def test_lab_read(self):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand.
        Assert: The output indicates that lab is retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "read"])
        assert result.exit_code == 0, result.output

        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["lab", "read", "-f", "json"])
        json_resp = json.loads(result.output)
        assert json_resp.get('id')

    @pytest.mark.parametrize("lab", [LAB_TO_EDIT, LAB_TO_CREATE])
    def test_lab_delete(self, lab):
        """
        Arrange/Act: Run the `lab` command with the 'delete' subcommand.
        Assert: The output indicates that lab is deleted successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, [
            "lab",
            "delete",
            "--path",
            lab["path"]
        ])
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

    def test_lab_export(self):
        """
        Arrange/Act: Run the `lab` command with the 'export' subcommand.
        Assert: The output indicates that lab exported successfully.
        """
        runner: CliRunner = CliRunner()
        with runner.isolated_filesystem():
            result: Result = runner.invoke(cli, ["lab", "export"])
            assert result.exit_code == 0, result.output
            assert "Success" in result.output

    def test_lab_import(self):
        """
        Arrange/Act: Run the `lab` command with the 'export' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        runner: CliRunner = CliRunner()
        cli_commands = ["lab", "import", "--src", "test.zip"]
        result: Result = runner.invoke(cli, cli_commands)
        assert result.exit_code == 0, result.output


class TestLabNodeCommands:

    def test_lab_node_create(self):
        """
        Arrange/Act: Run the `node` command with the 'create' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["node", "create"])
        assert result.exit_code == 0, result.output

    def test_lab_node_list(self):
        """
        Arrange/Act: Run the `node` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["node", "list"])
        assert result.exit_code == 0, result.output

    def test_lab_node_read(self):
        """
        Arrange/Act: Run the `node` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["node", "read", "--node-id", "1"])
        assert result.exit_code == 0, result.output

    def test_lab_node_start_command(self):
        """
        Arrange/Act: Run the `node` command with the 'start' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        cli_commands = ["node", "start", "--node-id", "1"]
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, cli_commands)
        assert result.exit_code == 0, result.output

    def test_lab_node_stop_command(self):
        """
        Arrange/Act: Run the `node` command with the 'stop' subcommand.
        Assert: The output indicates that lab stopped successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["node", "stop", "--node-id", "1"])
        assert result.exit_code == 0, result.output

    def test_lab_node_upload_config_command(self):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that lab started successfully.
        """
        cli_commands = ["node", "upload-config", "--node-id", "1"]
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, cli_commands)
        assert result.exit_code == 0, result.output


class TestLabNetworkCommands:

    def test_lab_network_create_command(self):
        """
        Arrange/Act: Run the `network` command with the 'create' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["network", "create"])
        assert result.exit_code == 0, result.output

    def test_lab_network_delete(self):
        """
        Arrange/Act: Run the `network` command with the 'delete' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["network", "delete"])
        assert result.exit_code == 0, result.output

    def test_lab_network_edit(self):
        """
        Arrange/Act: Run the `network` command with the 'edit' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["network", "edit"])
        assert result.exit_code == 0, result.output

    def test_lab_network_list(self):
        """
        Arrange/Act: Run the `network` command with the 'list' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["network", "list"])
        assert result.exit_code == 0, result.output

    def test_lab_network_read(self):
        """
        Arrange/Act: Run the `network` command with the 'read' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        runner: CliRunner = CliRunner()
        result: Result = runner.invoke(cli, ["network", "read"])
        assert result.exit_code == 0, result.output
