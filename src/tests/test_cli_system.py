# -*- coding: utf-8 -*-
import os

import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


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


@pytest.fixture()
def lab_to_edit():
    return LAB_TO_EDIT.copy()


@pytest.fixture()
def cli_client(lab_to_edit, client, request):
    client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    return client


@pytest.fixture()
def setup_test_lab(lab_to_edit, cli_client):
    cli_client.api.create_lab(**lab_to_edit)
    yield
    cli_client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    cli_client.api.delete_lab(lab_to_edit["path"] + lab_to_edit["name"])


class TestSystemCommands:
    def _run_commands(self, commands: list):
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": "/test lab1.unl"})
        result: Result = runner.invoke(cli, commands)
        assert result.exit_code == 0, result.output
        return result

    def test_system_status(self):
        """
        Arrange/Act: Run the `system` command with the 'status' subcommand.
        Assert: The output indicates that a status is successfully returned.
        """
        result = self._run_commands(["show-status"])
        assert "qemu_version" in result.output

    def test_system_list_network_types_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'list-network-types'
            subcommand.
        Assert: The output indicates that network types are successfully
            returned.
        """
        result = self._run_commands(["list-network-types"])
        assert "pnet0" in result.output

    def test_system_list_node_templates_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'list-node-templates'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["list-node-templates"])
        assert "osx" in result.output

    def test_system_list_user_roles_text_output(self):
        """
        Arrange/Act: Run the `system` command with the 'user-roles'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["list-user-roles"])
        assert "admin" in result.output

    def test_system_read_template(self):
        """
        Arrange/Act: Run the `system` command with the 'read-template'
            subcommand.
        Assert: The output indicates that node templates are successfully
            returned.
        """
        result = self._run_commands(["show-template", "asa"])
        assert "cpulimit" in result.output
