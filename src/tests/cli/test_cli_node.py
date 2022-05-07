# -*- coding: utf-8 -*-
import pytest


@pytest.mark.usefixtures("test_cli_lab", "test_node")
class TestLabNodeCommands:
    """CLI Node Commands"""

    def test_lab_node_list(self, cli_lab_path, helpers):
        """
        Arrange/Act: Run the `node` command with the 'list' subcommand.
        Assert: The output indicates that node imported successfully.
        """
        result = helpers.run_cli_command(["node", "list", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    @pytest.mark.parametrize(
        "command,expected_string",
        [
            ("start", "started"),
            ("stop", "stopped"),
            ("read", "image"),
            ("wipe", "wiped"),
            ("export", "exported"),
        ],
    )
    def test_lab_node_commands(self, cli_lab_path, command, expected_string, helpers):
        """
        Arrange/Act: Run the `node` command with the crud subcommands.
        Assert: The output indicates that node retrieved successfully.
        """
        result = helpers.run_cli_command(
            ["node", command, "--node-id", "1", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output
        assert expected_string in result.output

    @pytest.mark.parametrize(
        "command,expected_string",
        [
            ("wipe", "wiped"),
            ("export", "exported"),
        ],
    )
    def test_lab_node_all_commands(
        self, cli_lab_path, command, expected_string, helpers
    ):
        """
        Arrange/Act: Run the `node` commands with subcommands that support multiple nodes.
        Assert: The output indicates that command retrieved successfully for all nodes.
        """
        result = helpers.run_cli_command(["node", command, "--path", cli_lab_path])
        assert result.exit_code == 0, result.output
        assert expected_string in result.output

    @pytest.mark.parametrize(
        "command",
        ["create", "start", "stop", "read", "delete", "wipe", "export", "config"],
    )
    def test_lab_node_commads_with_error(self, command, cli_lab_path, helpers):
        """
        Arrange/Act: Run the `node` command with the crud subcommands.
        Assert: The output indicates that node displays error message instead of traceback.
        """
        args = ["node", command, "--node-id", "99", "--path", cli_lab_path]
        if command == "create":
            args = [
                "node",
                command,
                "--path",
                cli_lab_path,
                "--name",
                "test",
                "--template",
                "invalid",
            ]
        result = helpers.run_cli_command(args)
        assert result.exit_code > 0, result.output
        if command == "create":
            assert "Template does not exists or is not available" in result.output
        else:
            assert "Cannot find node in the selected lab" in result.output

    def test_lab_node_upload_config_inline(self, cli_lab_path, helpers):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that node string configuration
            uploaded successfully.
        """
        result = helpers.run_cli_command(
            ["node", "config", "--path", cli_lab_path, "-n", "1", "-c", "hostname test"]
        )
        assert result.exit_code == 0, result.output
        assert "Lab has been saved" in result.output

    def test_lab_node_upload_config_file(self, datadir, cli_lab_path, helpers):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that node string configuration
            uploaded successfully.
        """
        src = datadir / "test_config.txt"
        result = helpers.run_cli_command(
            ["node", "config", "--path", cli_lab_path, "-n", "1", "--src", str(src)]
        )
        assert result.exit_code == 0, result.output
        assert "Lab has been saved" in result.output

    def test_lab_node_upload_config_get(self, cli_lab_path, helpers):
        """
        Arrange/Act: Run the `node` command with the 'upload-config'
            subcommand.
        Assert: The output indicates that node string configuration
            uploaded successfully.
        """
        result = helpers.run_cli_command(
            ["node", "config", "--path", cli_lab_path, "-n", "1"]
        )
        assert result.exit_code == 0, result.output
