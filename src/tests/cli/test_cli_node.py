# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


@pytest.fixture(scope="module")
def test_node(test_node_data, cli_lab_path):
    """Create Test user."""
    cli_commands = [
        "node",
        "create",
        "--path",
        cli_lab_path,
        "--node-type",
        test_node_data["node_type"],
        "--name",
        test_node_data["name"],
        "--template",
        test_node_data["template"],
        "--ethernet",
        test_node_data["ethernet"],
    ]
    yield run_cli_command(cli_commands)
    run_cli_command(["node", "delete", "-n", "1", "--path", cli_lab_path])


def run_cli_command(commands: list) -> Result:
    """Helper function to Run CLI command."""
    runner: CliRunner = CliRunner()
    return runner.invoke(cli, commands)


@pytest.mark.usefixtures("test_lab", "test_node")
class TestLabNodeCommands:
    """CLI Node Commands"""

    def test_lab_node_list(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'list' subcommand.
        Assert: The output indicates that lab imported successfully.
        """
        result = run_cli_command(["node", "list", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    def test_lab_node_read(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'read' subcommand.
        Assert: The output indicates that lab retrieved successfully.
        """
        result = run_cli_command(
            ["node", "read", "--node-id", "1", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output

    def test_lab_node_start_command(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'start' subcommand.
        Assert: The output indicates that lab started successfully.
        """
        result = run_cli_command(
            ["node", "start", "--node-id", "1", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output
        assert "started" in result.output

    def test_lab_node_stop_command(self, cli_lab_path):
        """
        Arrange/Act: Run the `node` command with the 'stop' subcommand.
        Assert: The output indicates that lab stopped successfully.
        """
        result = result = run_cli_command(
            ["node", "stop", "--node-id", "1", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output
        assert "stopped" in result.output

    def test_lab_node_upload_config_command(self, cli_lab_path, test_node_config):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that lab string configuration
            uploaded successfully.
        """
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": cli_lab_path})
        with runner.isolated_filesystem():
            with open("config.txt", "w", encoding="utf-8") as f:
                f.write(test_node_config)
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
