# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner

from evengsdk.cli.cli import main as cli


@pytest.mark.usefixtures("setup_cli_lab")
class TestSystemCommands:
    def _run_commands(self, commands, lab_path):
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": lab_path})
        return runner.invoke(cli, commands)

    def test_system_status(self, cli_lab_path):
        """
        Arrange/Act: Run the `system` command with the 'status' subcommand.
        Assert: The output indicates that a status is successfully returned.
        """
        result = self._run_commands(["show-status"], cli_lab_path)
        assert "qemu_version" in result.output

    def test_system_list_network_types_text_output(self, cli_lab_path):
        """
        Arrange/Act: Run the `system` command with the 'list-network-types'
            subcommand.
        Assert: The output indicates that network types are successfully
            returned.
        """
        result = self._run_commands(["list-network-types"], cli_lab_path)
        assert "pnet0" in result.output

    def test_system_list_node_templates_text_output(self, cli_lab_path):
        """
        Arrange/Act: Run the `system` command with the 'list-node-templates'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["list-node-templates"], cli_lab_path)
        assert "osx" in result.output

    def test_system_list_user_roles_text_output(self, cli_lab_path):
        """
        Arrange/Act: Run the `system` command with the 'user-roles'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["list-user-roles"], cli_lab_path)
        assert "admin" in result.output

    def test_system_read_template(self, cli_lab_path):
        """
        Arrange/Act: Run the `system` command with the 'read-template'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["show-template", "asa"], cli_lab_path)
        assert "cpulimit" in result.output
