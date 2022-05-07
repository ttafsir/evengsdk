# -*- coding: utf-8 -*-
import json

import pytest


@pytest.mark.usefixtures("setup_cli_lab")
class TestSystemCommands:
    """CLI System Commands"""

    @pytest.mark.parametrize(
        "command,expected_string",
        [
            ("show-status", "qemu_version"),
            ("list-node-templates", "osx"),
            ("list-user-roles", "admin"),
            (["show-template", "asa"], "cpulimit"),
        ],
    )
    def test_system_commands(self, helpers, command, expected_string):
        """
        Arrange/Act: Run the `system` commands.
        Assert: The output indicates that a status is successfully returned.
        """
        commands = command if isinstance(command, list) else [command]
        result = helpers.run_cli_command(commands)
        assert expected_string in result.output

    @pytest.mark.parametrize(
        "command,expected_string",
        [
            ("show-status", "System"),
            ("list-node-templates", "Node Template"),
            ("list-user-roles", "User Roles"),
        ],
    )
    def test_system_commands_json_output(
        self, helpers, command, expected_string, escape_ansi_regex
    ):
        """
        Arrange/Act: Run the `system` commands with json output.
        Assert: The output indicates that a status is successfully returned.
        """
        output_format = "json"
        commands = command if isinstance(command, list) else [command]
        commands.extend(["--output", output_format])
        result = helpers.run_cli_command(commands)
        escaped_result = escape_ansi_regex.sub("", result.output)
        assert expected_string in escaped_result or json.loads(escaped_result)

    def test_system_list_network_types_text_output(self, authenticated_client, helpers):
        """
        Arrange/Act: Run the `system` command with the 'list-network-types'
            subcommand.
        Assert: The output indicates that network types are successfully
            returned.
        """
        result = helpers.run_cli_command(["list-network-types"])
        if authenticated_client.api.is_community:
            assert "pnet0" in result.output
        else:
            assert "nat0" in result.output
