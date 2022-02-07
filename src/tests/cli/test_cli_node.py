# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


LAB_TO_CREATE = {"name": "test lab1", "path": "/test lab1.unl"}
TEST_CONFIG = """
!
hostname vEOS4
!
"""


@pytest.fixture()
def test_node():
    return {
        "node_type": "qemu",
        "template": "veos",
        "image": "veos-4.21.1.1F",
        "name": "leaf01",
        "ethernet": 4,
        "cpu": 2,
        "serial": 2,
        "delay": 0,
    }


@pytest.mark.usefixtures("setup_cli_lab")
class TestLabNodeCommands:
    def _run_commands(self, commands, lab_path):
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": lab_path})
        return runner.invoke(cli, commands)

    def _run_node_command(self, cmd: str, *args, **kwargs):
        return self._run_commands(["node", cmd, "--node-id", "1"], *args, **kwargs)

    def test_lab_node_create(self, cli_lab_path, test_node):
        """
        Arrange/Act: Run the `node` command with the 'create' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        cli_commands = [
            "node",
            "create",
            "--node-type",
            test_node["node_type"],
            "--name",
            test_node["name"],
            "--template",
            test_node["template"],
            "--ethernet",
            test_node["ethernet"],
        ]

        result = self._run_commands(cli_commands, cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_node_list(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = self._run_commands(["node", "list"], cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_node_read(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = self._run_node_command("read", cli_lab_path)
        assert result.exit_code == 0, result.output

    def test_lab_node_start_command(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'start' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        result = self._run_node_command("start", cli_lab_path)
        assert result.exit_code == 0, result.output
        assert "started" in result.output

    def test_lab_node_stop_command(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'stop' subcommand.
        Assert: The output indicates that lab stopped successfully.
        """
        result = result = self._run_node_command("stop", cli_lab_path)
        assert result.exit_code == 0, result.output
        assert "stopped" in result.output

    @pytest.mark.skip(reason="TODO: fix enable=True argument")
    def test_lab_node_upload_config_command(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that lab string configuration
            uploaded successfully.
        """
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": cli_lab_path})
        with runner.isolated_filesystem():
            with open("config.txt", "w") as f:
                f.write(TEST_CONFIG)
            commands = [
                "node",
                "config",
                "-n",
                "1",
                "-c",
                "hostname test",
            ]
            result: Result = runner.invoke(cli, commands)
            assert result.exit_code == 0, result.output
            assert "Lab has been saved" in result.output
