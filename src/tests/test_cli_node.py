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


class TestLabNodeCommands:
    def _run_commands(self, commands: list):
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": "/test lab1.unl"})
        return runner.invoke(cli, commands)

    def _run_node_command(self, cmd: str):
        return self._run_commands(["node", cmd, "--node-id", "1"])

    def test_lab_node_create(self):
        """
        Arrange/Act: Run the `node` command with the 'create' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        cli_commands = [
            "node",
            "create",
            "--node-type",
            "qemu",
            "--name",
            "TEST_CSR",
            "--template",
            "csr1000v",
            "--ethernet",
            "4",
        ]

        result = self._run_commands(cli_commands)
        assert result.exit_code == 0, result.output

    def test_lab_node_list(self):
        """
        Arrange/Act: Run the `node` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = self._run_commands(["node", "list"])
        assert result.exit_code == 0, result.output

    def test_lab_node_read(self):
        """
        Arrange/Act: Run the `node` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = self._run_node_command("read")
        assert result.exit_code == 0, result.output

    def test_lab_node_start_command(self):
        """
        Arrange/Act: Run the `node` command with the 'start' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        result = self._run_node_command("start")
        assert result.exit_code == 0, result.output
        assert "started" in result.output

    def test_lab_node_stop_command(self):
        """
        Arrange/Act: Run the `node` command with the 'stop' subcommand.
        Assert: The output indicates that lab stopped successfully.
        """
        result = result = self._run_node_command("stop")
        assert result.exit_code == 0, result.output
        assert "stopped" in result.output

    @pytest.mark.skip(reason="TODO: Need to fix set-active command")
    def test_lab_node_upload_config_command(self):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that lab string configuration
            uploaded successfully.
        """
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": "/test lab1.unl"})
        with runner.isolated_filesystem():
            with open("config.txt", "w") as f:
                f.write(TEST_CONFIG)
            commands = [
                "node",
                "upload-config",
                "-n",
                "1",
                "-c",
                "hostname test" f"--path {LAB_TO_CREATE}",
            ]
            result: Result = runner.invoke(cli, commands)
            assert result.exit_code == 0, result.output
            assert "Lab has been saved" in result.output
